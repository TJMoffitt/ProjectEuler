"""Bid Remote: run the Bid Clicker in a Playwright-controlled browser and drive it from a web page.

Start with `python app.py` (see README.md). Settings come from environment variables or a .env file
next to this script.
"""

import asyncio
import hashlib
import hmac
import itertools
import json
import os
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from playwright.async_api import BrowserContext, Page, async_playwright
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")


def env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


PASSWORD = os.getenv("BID_PASSWORD", "")
TOTP_SECRET = os.getenv("BID_TOTP_SECRET", "").replace(" ", "")
SESSION_SECRET = os.getenv("SESSION_SECRET") or secrets.token_hex(32)
MAX_BID_CAP = float(os.getenv("MAX_BID_CAP", "0") or 0)  # 0 = no overall cap
HEADLESS = env_bool("HEADLESS", False)
PROFILE_DIR = HERE / os.getenv("BROWSER_PROFILE", "profile")  # relative paths are relative to this folder
CHROME_PATH = os.getenv("CHROME_PATH") or None
COOKIE_SECURE = env_bool("COOKIE_SECURE", False)
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
BID_LOG = HERE / os.getenv("BID_LOG", "bids.log")
BIDDER_JS = HERE / "bidder.js"

if len(PASSWORD) < 10:
    raise SystemExit("Set BID_PASSWORD (at least 10 characters) in .env — see .env.example")
if not os.getenv("SESSION_SECRET"):
    print("SESSION_SECRET not set: you'll be logged out whenever the server restarts.")

# Changing the password invalidates existing logins
AUTH_VERSION = hashlib.sha256((PASSWORD + TOTP_SECRET).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- browser


class Browser:
    """One persistent Chromium profile; every tab gets bidder.js and a numeric id."""

    def __init__(self):
        self.pw = None
        self.ctx: BrowserContext | None = None
        self.pages: dict[int, Page] = {}
        self.ids = itertools.count(1)
        self.events: list[dict] = []  # recent arm/bid/disarm events for the dashboard

    async def start(self):
        self.pw = await async_playwright().start()
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        self.ctx = await self.pw.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=HEADLESS,
            executable_path=CHROME_PATH,
            no_viewport=not HEADLESS,
            viewport={"width": 1280, "height": 900} if HEADLESS else None,
            args=[
                # Keep background tabs running at full speed
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
            ],
        )
        await self.ctx.expose_binding("__bidReport", self.on_report)
        await self.ctx.add_init_script(path=str(BIDDER_JS))
        self.ctx.on("page", self.register)
        for page in self.ctx.pages:
            self.register(page)

    async def stop(self):
        if self.ctx:
            await self.ctx.close()
        if self.pw:
            await self.pw.stop()

    def register(self, page: Page):
        pid = next(self.ids)
        self.pages[pid] = page
        page.on("close", lambda _: self.pages.pop(pid, None))

    def get(self, pid: int) -> Page:
        page = self.pages.get(pid)
        if not page or page.is_closed():
            raise HTTPException(404, "That tab is gone")
        return page

    def on_report(self, source, event):
        if not isinstance(event, dict):
            return
        entry = {"time": datetime.now().isoformat(timespec="seconds"), "url": source["page"].url, **event}
        self.events = (self.events + [entry])[-200:]
        with BID_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    async def status(self, page: Page):
        try:
            return await asyncio.wait_for(
                page.evaluate("() => window.__bidStatus ? window.__bidStatus() : null"), 2
            )
        except Exception:
            return None  # navigating, or the page is busy

    async def tab_info(self, pid: int, page: Page):
        st = await self.status(page)
        try:
            title = await asyncio.wait_for(page.title(), 2)
        except Exception:
            title = ""
        return {"id": pid, "url": page.url, "title": title, "status": st}


browser = Browser()


@asynccontextmanager
async def lifespan(_app):
    await browser.start()
    yield
    await browser.stop()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="bidremote",
    max_age=30 * 24 * 3600,
    same_site="strict",
    https_only=COOKIE_SECURE,
)


# ---------------------------------------------------------------- auth

failures: list[float] = []  # times of recent failed logins (all clients: behind a tunnel they share one IP)
LOCKOUT_COUNT, LOCKOUT_WINDOW = 10, 15 * 60


def logged_in(request: Request) -> bool:
    return request.session.get("auth") == AUTH_VERSION


def require_auth(request: Request):
    if not logged_in(request):
        raise HTTPException(401, "Log in first")


def check_totp(code: str) -> bool:
    if not TOTP_SECRET:
        return True
    import pyotp

    return pyotp.TOTP(TOTP_SECRET).verify(code.strip(), valid_window=1)


LOGIN_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Bid Remote</title><link rel="icon" href="data:,">
<style>
 :root{color-scheme:light dark;--bg:#f6f7f9;--card:#fff;--fg:#1d2127;--muted:#6b7280;--line:#d6d9de;--accent:#1f5fa8;--bad:#b42318}
 @media (prefers-color-scheme:dark){:root{--bg:#111418;--card:#1b1f25;--fg:#e8eaed;--muted:#9aa1ab;--line:#333a44;--accent:#5b9be6;--bad:#f07167}}
 body{margin:0;background:var(--bg);color:var(--fg);font:16px system-ui,sans-serif;display:grid;place-items:center;min-height:100vh}
 form{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:24px;width:min(340px,calc(100vw - 32px));box-sizing:border-box}
 h1{font-size:20px;margin:0 0 16px} label{display:block;font-weight:600;margin:12px 0 4px}
 input{width:100%;box-sizing:border-box;padding:10px;font-size:16px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
 button{margin-top:18px;width:100%;padding:11px;font-size:16px;border:0;border-radius:6px;background:var(--accent);color:#fff;cursor:pointer}
 .err{color:var(--bad);margin-top:12px;font-size:14px}
</style></head><body><form method="post" action="/login">
<h1>Bid Remote</h1>
<label for="p">Password</label><input id="p" name="password" type="password" autocomplete="current-password" autofocus required>
__TOTP__
<button>Log in</button>__ERR__</form></body></html>"""

TOTP_FIELD = ('<label for="c">Authenticator code</label>'
              '<input id="c" name="code" inputmode="numeric" autocomplete="one-time-code" required>')


def login_page(error: str = "") -> HTMLResponse:
    html = LOGIN_PAGE.replace("__TOTP__", TOTP_FIELD if TOTP_SECRET else "")
    html = html.replace("__ERR__", f'<div class="err">{error}</div>' if error else "")
    return HTMLResponse(html, status_code=401 if error else 200)


@app.get("/login")
async def login_form(request: Request):
    if logged_in(request):
        return RedirectResponse("/", 303)
    return login_page()


@app.post("/login")
async def login(request: Request, password: str = Form(""), code: str = Form("")):
    now = time.time()
    failures[:] = [t for t in failures if now - t < LOCKOUT_WINDOW]
    if len(failures) >= LOCKOUT_COUNT:
        return login_page("Too many failed attempts — try again in 15 minutes.")
    ok_pw = hmac.compare_digest(password.encode(), PASSWORD.encode())
    if not (ok_pw and check_totp(code)):
        failures.append(now)
        await asyncio.sleep(1)
        return login_page("Wrong password or code.")
    request.session.clear()
    request.session["auth"] = AUTH_VERSION
    return RedirectResponse("/", 303)


@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", 303)


# ---------------------------------------------------------------- pages


@app.get("/")
async def index(request: Request):
    if not logged_in(request):
        return RedirectResponse("/login", 303)
    return FileResponse(HERE / "static" / "index.html", headers={"Cache-Control": "no-store"})


# ---------------------------------------------------------------- API

api = Depends(require_auth)


class OpenTab(BaseModel):
    url: str


class Arm(BaseModel):
    lot: str = Field(min_length=1, max_length=20)
    max: float = Field(gt=0)
    debug: bool = False


class Click(BaseModel):
    x: float = Field(ge=0, le=1)  # fraction of the screenshot's width
    y: float = Field(ge=0, le=1)


class Keys(BaseModel):
    text: str = ""
    key: str = ""  # e.g. Enter, Tab, Backspace, Escape


class Scroll(BaseModel):
    dy: float


@app.get("/api/state", dependencies=[api])
async def state():
    tabs = await asyncio.gather(*(browser.tab_info(pid, p) for pid, p in list(browser.pages.items())))
    return {"tabs": tabs, "events": browser.events[-50:], "cap": MAX_BID_CAP, "headless": HEADLESS}


@app.post("/api/tabs", dependencies=[api])
async def open_tab(body: OpenTab):
    url = body.url.strip()
    if not url.startswith(("https://", "http://")):
        url = "https://" + url
    blank = [p for p in browser.pages.values() if p.url == "about:blank" and not p.is_closed()]
    page = blank[0] if blank else await browser.ctx.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        return {"ok": True, "warning": f"Opened, but the page was slow to load: {e.__class__.__name__}"}
    return {"ok": True}


@app.delete("/api/tabs/{pid}", dependencies=[api])
async def close_tab(pid: int):
    page = browser.get(pid)
    if len(browser.pages) == 1:
        await page.goto("about:blank")  # closing the last tab would close the browser
    else:
        await page.close()
    return {"ok": True}


@app.post("/api/tabs/{pid}/arm", dependencies=[api])
async def arm(pid: int, body: Arm):
    page = browser.get(pid)
    st = await browser.status(page)
    if not st or not st.get("site"):
        raise HTTPException(400, "This tab isn't a live bidding page (yet).")
    if MAX_BID_CAP and body.max > MAX_BID_CAP:
        raise HTTPException(400, f"Max £{body.max:g} is over the overall cap of £{MAX_BID_CAP:g} (MAX_BID_CAP).")
    return await page.evaluate("([l, m, d]) => window.__bidArm(l, m, d)", [body.lot.strip(), body.max, body.debug])


@app.post("/api/tabs/{pid}/stop", dependencies=[api])
async def stop(pid: int):
    page = browser.get(pid)
    return await page.evaluate("() => window.__bidStop ? window.__bidStop() : null")


@app.post("/api/stop-all", dependencies=[api])
async def stop_all():
    async def one(page):
        try:
            await asyncio.wait_for(page.evaluate("() => window.__bidStop && window.__bidStop('Stopped (stop all)')"), 3)
            return True
        except Exception:
            return False

    results = await asyncio.gather(*(one(p) for p in list(browser.pages.values())))
    return {"stopped": sum(results), "failed": results.count(False)}


# Remote view: lets you log in to the auction sites and look at the console from your phone.


@app.get("/api/tabs/{pid}/screenshot", dependencies=[api])
async def screenshot(pid: int):
    page = browser.get(pid)
    try:
        img = await page.screenshot(type="jpeg", quality=60, timeout=8000)
    except Exception as e:
        raise HTTPException(503, f"Couldn't capture this tab: {e.__class__.__name__}")
    return Response(img, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


async def viewport(page: Page):
    return await page.evaluate("() => [window.innerWidth, window.innerHeight]")


@app.post("/api/tabs/{pid}/click", dependencies=[api])
async def click(pid: int, body: Click):
    page = browser.get(pid)
    w, h = await viewport(page)
    await page.mouse.click(body.x * w, body.y * h)
    return {"ok": True}


@app.post("/api/tabs/{pid}/keys", dependencies=[api])
async def keys(pid: int, body: Keys):
    page = browser.get(pid)
    if body.text:
        await page.keyboard.type(body.text)
    if body.key:
        try:
            await page.keyboard.press(body.key)
        except Exception:
            raise HTTPException(400, f"Unknown key {body.key!r}")
    return {"ok": True}


@app.post("/api/tabs/{pid}/scroll", dependencies=[api])
async def scroll(pid: int, body: Scroll):
    page = browser.get(pid)
    w, h = await viewport(page)
    await page.mouse.move(w / 2, h / 2)
    await page.mouse.wheel(0, body.dy)
    return {"ok": True}


@app.post("/api/tabs/{pid}/{action}", dependencies=[api])
async def nav(pid: int, action: str):
    page = browser.get(pid)
    if action == "reload":
        await page.reload(wait_until="domcontentloaded")
    elif action == "back":
        await page.go_back(wait_until="domcontentloaded")
    elif action == "front":
        await page.bring_to_front()
    else:
        raise HTTPException(404)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT, proxy_headers=True)
