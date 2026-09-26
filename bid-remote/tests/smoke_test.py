"""End-to-end check against a fake EasyLive console: python tests/smoke_test.py

Starts the app headless on a spare port with a throwaway profile, logs in, opens the fake page,
arms lot 12 up to £20 and checks it bids 12, 16, 20, never over the max, and stops when lot 13 opens.
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
APP = HERE.parent
PAGE_PORT, APP_PORT = 8765, 8766


def wait_for(fn, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        try:
            result = fn()
            if result:
                return result
        except Exception:
            pass
        time.sleep(0.25)
    raise AssertionError("timed out")


def main():
    profile = tempfile.mkdtemp()
    env = {**os.environ, "BID_PASSWORD": "smoke-test-password", "SESSION_SECRET": "x" * 32, "HEADLESS": "true",
           "BROWSER_PROFILE": profile, "BID_LOG": os.path.join(profile, "bids.log"), "PORT": str(APP_PORT), "MAX_BID_CAP": "100", "BID_TOTP_SECRET": ""}
    pages = subprocess.Popen([sys.executable, "-m", "http.server", str(PAGE_PORT), "-d", str(HERE)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    server = subprocess.Popen([sys.executable, str(APP / "app.py")], env=env, cwd=APP)
    try:
        c = httpx.Client(base_url=f"http://127.0.0.1:{APP_PORT}", timeout=30)
        wait_for(lambda: c.get("/login").status_code == 200)

        assert c.get("/api/state").status_code == 401, "API must need a login"
        assert c.post("/login", data={"password": "wrong"}).status_code == 401
        assert c.post("/login", data={"password": "smoke-test-password"}).status_code == 303
        assert c.get("/").status_code == 200

        c.post("/api/tabs", json={"url": f"http://127.0.0.1:{PAGE_PORT}/fake_easylive.html"}).raise_for_status()
        tab = wait_for(lambda: next(t for t in c.get("/api/state").json()["tabs"]
                                    if t["status"] and t["status"]["site"] == "EasyLive"))
        tid = tab["id"]

        r = c.post(f"/api/tabs/{tid}/arm", json={"lot": "12", "max": 500})
        assert r.status_code == 400 and "cap" in r.text, "overall cap must be enforced"

        c.post(f"/api/tabs/{tid}/arm", json={"lot": "12", "max": 20}).raise_for_status()
        st = wait_for(lambda: (s := next(t for t in c.get("/api/state").json()["tabs"] if t["id"] == tid)["status"])
                      and not s["cfg"]["armed"] and s)
        events = c.get("/api/state").json()["events"]
        bids = [e["ask"] for e in events if e["type"] == "bid"]
        print("bids:", bids, "| stopped with:", st["lastMessage"])
        assert bids == [12, 16, 20], bids
        assert "closed" in st["lastMessage"]

        shot = c.get(f"/api/tabs/{tid}/screenshot")
        assert shot.status_code == 200 and shot.content[:2] == b"\xff\xd8", "screenshot should be a JPEG"
        assert c.post("/api/stop-all").json()["failed"] == 0
        print("OK")
    finally:
        server.terminate()
        pages.terminate()
        server.wait(10)


if __name__ == "__main__":
    main()
