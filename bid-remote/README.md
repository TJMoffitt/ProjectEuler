# Bid Remote

The Bid Clicker extension, turned into a web page you can use from your phone or anywhere else.
The bidding itself runs in a real Chromium browser on your home PC or a server, controlled by
[Playwright](https://playwright.dev/python/). The page talks to a small [FastAPI](https://fastapi.tiangolo.com/) server that drives the browser.

```
Phone / laptop ──HTTPS + login──▶ app.py (FastAPI) ──Playwright──▶ Chromium, logged in to EasyLive / Saleroom
                                                                   └─ bidder.js in every tab (same logic as the extension)
```

What you get on the control page:

- **Open an auction**: paste the live bidding URL and it opens in the controlled browser.
- **One card per tab**: the live lot, current price and asking price; set the lot and max bid; **Arm**, **Stop** and **Debug mode**.
  This is exactly what the extension popup did, and it still stops itself when your lot closes.
- **View**: a live screenshot of the tab. Tap on it to click there, type text, press keys and scroll.
  Use this to log in to the auction sites and tick "Follow" when there's no screen attached.
- **Stop all**, an **Activity** feed of every arm, bid and stop, and `bids.log` on disk as a permanent record.
- An optional **overall cap** (`MAX_BID_CAP`), so no tab can be armed above a set amount.

> ⚠️ Every real click is a legally binding bid. Try **Debug mode** first on a live sale; it logs what it *would* bid.
> Check EasyLive's and the-saleroom's terms on automated bidding: it's your account at risk.

## Files

| File | What it is |
|---|---|
| `app.py` | Server: login, browser control, API |
| `bidder.js` | The extension's `content.js`, with the Chrome messaging swapped for functions the server calls |
| `static/index.html` | The control page |
| `tests/smoke_test.py` | End-to-end test against `tests/fake_easylive.html` |

## Setup (home PC, Windows)

You need Python 3.10+ from python.org; tick "Add to PATH" when you install it.

```bat
cd bid-remote
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
copy .env.example .env
notepad .env
```

In `.env`, set `BID_PASSWORD` and `SESSION_SECRET` (the file explains how). `BID_TOTP_SECRET` and
`MAX_BID_CAP` are recommended too.

Start it by double-clicking `start.bat`, or by running `python app.py`. A Chromium window opens, and so does
the control page at <http://localhost:8000>.

**The first time only**, log in to EasyLive and the-saleroom in that Chromium window (tick "remember me").
The logins are kept in the `profile/` folder, so this is a one-off. Leave the window open; minimising it is fine.

Stop Windows from sleeping while it runs: Settings → System → Power → Sleep → Never (at least while plugged in).

On macOS or Linux it's the same, using `source .venv/bin/activate`, `cp` and `./start.sh`.

## Reaching it from anywhere

The server only listens on the machine itself (`HOST=127.0.0.1`), which is deliberate. Don't port-forward it
on your router. Pick one of these:

### Option A: Tailscale (recommended, private)

Only your own devices can reach it.

1. Install [Tailscale](https://tailscale.com/download) on the PC and your phone, and sign in to the same account on both.
2. On the PC, run:
   ```
   tailscale serve --bg 8000
   ```
3. On your phone, open `https://<pc-name>.<your-tailnet>.ts.net`. The exact address is shown by `tailscale serve status`.
4. Set `COOKIE_SECURE=true` in `.env` and restart the app.

### Option B: Cloudflare Tunnel + Access (a public URL, still locked down)

Use this if you want a normal web address you can open from any device.

1. Put a domain on Cloudflare (free plan), and install `cloudflared`.
2. Zero Trust dashboard → Networks → Tunnels → create a tunnel, pointing `bid.yourdomain.com` → `http://localhost:8000`.
3. Zero Trust → Access → Applications → add `bid.yourdomain.com`, with a policy that allows only your email.
   Cloudflare then asks for an email code before anyone even sees the login page.
4. Set `COOKIE_SECURE=true`.

Either way, the app's own password (plus the authenticator code, if you set `BID_TOTP_SECRET`) is a second lock.
After 10 wrong attempts in 15 minutes, logins are locked for 15 minutes.

## Running on a server instead

This works on any small Linux VPS (Ubuntu, 2 GB RAM); choose a UK region.

```bash
sudo apt install -y python3-venv
cd bid-remote && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium
cp .env.example .env && nano .env      # set HEADLESS=true
./start.sh
```

Then set up Tailscale or Cloudflare Tunnel exactly as above. Since there's no screen, log in to the auction sites
through **View** on the control page: tap the fields, type into the box, and press Enter.

To keep it running after you log out, use a systemd unit:

```ini
# /etc/systemd/system/bid-remote.service
[Unit]
Description=Bid Remote
After=network-online.target

[Service]
User=YOURUSER
WorkingDirectory=/home/YOURUSER/bid-remote
ExecStart=/home/YOURUSER/bid-remote/.venv/bin/python app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable it with `sudo systemctl enable --now bid-remote`.

Caveats compared with a home PC: auction sites see a datacentre IP rather than your home one, so expect more
"are you human" checks or new-device emails. A headless browser is also easier for sites to spot. If that becomes
a problem, run it headed under a virtual display: `sudo apt install xvfb`, then set `HEADLESS=false` and change
`ExecStart` to `xvfb-run -a .venv/bin/python app.py`.

## Using it

1. **Open** the live bidding page for a sale (the page with the BID button).
2. On its card, enter the lot number and max bid, then press **Arm**. It waits until your lot comes up, bids whenever
   the asking price is at or under your max and someone else leads, and stops when the lot closes.
3. You can arm several tabs at once, one lot per auction tab, just like the extension.
4. If a site logs you out or shows a popup, use **View** to sort it out.

## Test

The test starts the app headless with a throwaway profile, opens a fake EasyLive console, arms lot 12 up to £20,
and checks that it bids £12, £16 and £20 against a rival, never goes over the max, and stops when lot 13 opens:

```bash
python tests/smoke_test.py
```

## Keeping it in step with the sites

If EasyLive or Saleroom change their page layout, the selectors in `bidder.js` (the `SITES` list) need updating.
These are the same selectors as in the extension, so a fix to one applies to the other.
