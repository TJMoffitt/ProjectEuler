// Bid Clicker, adapted from the browser extension's content.js to run inside a Playwright-controlled browser.
// Injected into every page; only does anything on an EasyLive / Saleroom live bidding console.
// The server drives it through window.__bidArm / __bidStop / __bidStatus and hears about bids via __bidReport.
(() => {
  if (window.top !== window) return; // main frame only
  if (window.__bidClicker) return;   // already running in this page
  window.__bidClicker = true;

  const report = (event) => { try { window.__bidReport && window.__bidReport(event); } catch {} };

  // Each tab keeps its own settings in sessionStorage: separate per tab, and survives a page refresh
  const KEY = "bidClicker";
  const saved = (() => { try { return JSON.parse(sessionStorage.getItem(KEY)) || {}; } catch { return {}; } })();

  let cfg = { armed: false, lot: "", max: 0, debug: false, ...saved.cfg };
  let log = saved.log || [];                   // debug log for this tab (last 30 lines)
  let lastMessage = saved.lastMessage || "";   // why it last stopped
  let lastClickedAsk = saved.lastClickedAsk ?? null; // the amount we last bid, so we never bid it twice
  let seenTarget = saved.seenTarget || false;  // true once our lot has come up, so we can stop when it moves on
  let lastLogged = "";
  let lastBadge = "";
  let lastColour = "#555";
  let live = {};                               // last reading of the bidding console, for the dashboard

  function save() {
    try {
      sessionStorage.setItem(KEY, JSON.stringify({ cfg, log, lastMessage, lastClickedAsk, seenTarget }));
    } catch {}
  }

  const $ = (sel) => document.querySelector(sel);
  const text = (sel) => ($(sel)?.textContent || "").replace(/\s+/g, " ").trim();

  // "BID NOW £1,250" / "1,250" -> 1250
  const money = (t) => {
    const m = (t || "").replace(/,/g, "").match(/(\d+(?:\.\d+)?)/);
    return m ? parseFloat(m[1]) : null;
  };

  const isShown = (el) =>
    el && !el.disabled && getComputedStyle(el).display !== "none" &&
    getComputedStyle(el).visibility !== "hidden" && el.offsetParent !== null;

  // Each site: how to read the live lot, bid button, asking price, current price and status text
  const SITES = [
    {
      name: "EasyLive",
      detect: () => $("#bid-live-bid-btn"),
      read: () => ({
        lot: (text("#bid-live-lot-no strong").match(/Lot\s+(\S+)/i) || [])[1],
        btn: $("#bid-live-bid-btn"),
        ask: money(text("#bid-live-bid-btn")),
        current: money(text(".bid-live-current-bid .current-bid")),
        status: text(".bid-live-current-bid .h4"),
      }),
    },
    {
      name: "Saleroom",
      detect: () => $("#bid-button") && $("#asking-price"),
      read: () => ({
        lot: text("#lot-number"),
        btn: $("#bid-button"),
        ask: money(text("#asking-price")),
        current: money(text("#hammer-price")),
        status: [
          text("#auction-message-content"),
          isShown($("#outbid-message")) ? "OUTBID " + text("#outbid-message-text") : "",
        ].filter(Boolean).join(" | "),
      }),
    },
  ];

  // On-page status badge (visible in the dashboard's screenshots)
  let badge;
  function setBadge(msg, colour = "#333") {
    if (!badge) {
      badge = document.createElement("div");
      Object.assign(badge.style, {
        position: "fixed", bottom: "12px", left: "12px", zIndex: 2147483647,
        padding: "6px 10px", borderRadius: "4px", color: "#fff",
        font: "600 15px system-ui, sans-serif", boxShadow: "0 2px 8px rgba(0,0,0,.4)", pointerEvents: "none", maxWidth: "420px",
      });
      document.body.appendChild(badge);
    }
    const full = "Bid Clicker" + (cfg.debug ? " [DEBUG]" : "") + ": " + msg;
    const bg = cfg.debug && colour !== "#555" ? "#b26a00" : colour;
    lastBadge = msg;
    lastColour = bg;
    if (badge.textContent !== full) badge.textContent = full;
    if (badge.style.background !== bg) badge.style.background = bg;
    if (cfg.debug && cfg.armed) debugLog(msg);
  }

  // Timestamped log to the console and this tab's dashboard log, only when the message changes
  function debugLog(msg) {
    if (msg === lastLogged) return;
    lastLogged = msg;
    const line = `${new Date().toLocaleTimeString()}  ${msg}`;
    console.log("[Bid Clicker]", line);
    log = log.concat(line).slice(-30);
    save();
  }

  function disarm(message) {
    const wasArmed = cfg.armed;
    cfg.armed = false;
    lastMessage = message;
    save();
    setBadge(message, "#555");
    if (wasArmed) report({ type: "disarm", lot: cfg.lot, message });
  }

  function tick() {
    const site = SITES.find((s) => s.detect());
    if (!site) return; // not a live bidding console

    const { lot, btn, ask, current, status } = site.read();
    live = { lot: lot || "", ask, current, status };

    if (!cfg.armed) { setBadge(lastMessage || "off", "#555"); return; }

    const target = String(cfg.lot).trim().toUpperCase();
    const liveLot = (lot || "").toUpperCase();

    if (liveLot !== target) {
      if (seenTarget) disarm(`Lot ${target} has closed — stopped`);
      else setBadge(`waiting for lot ${target} (now on ${liveLot || "?"}), max £${cfg.max}`, "#1f5fa8");
      return;
    }
    if (!seenTarget) { seenTarget = true; save(); }

    if (!isShown(btn)) { setBadge(`lot ${target} live — no bid button right now`, "#1f5fa8"); return; }
    if (ask == null) return;

    if (ask > cfg.max) {
      setBadge(`asking £${ask} is over your max £${cfg.max} — not bidding`, "#b42318");
      return;
    }

    // Leading if the page says so, or if the current price is our last bid and nothing says someone else has it
    const s = status.toUpperCase();
    const leading =
      /\bYOU/.test(s) ||
      (lastClickedAsk !== null && current === lastClickedAsk &&
        !/COMPETING|ROOM|FLOOR|ASKING|OUTBID|COMMISSION/.test(s));

    if (leading) { setBadge(`you lead at £${current} (max £${cfg.max}) — "${status}"`, "#1a7f37"); return; }

    // Already bid this amount and the page hasn't moved on yet — wait
    if (ask === lastClickedAsk) {
      setBadge(`${cfg.debug ? "would have bid" : "bid"} £${ask} — waiting for the page to update (max £${cfg.max})`, "#1a7f37");
      return;
    }

    lastClickedAsk = ask;
    save();
    if (cfg.debug) {
      setBadge(`WOULD bid £${ask} on lot ${target} (current £${current}, "${status}", max £${cfg.max})`);
      report({ type: "would-bid", lot: target, ask, current, max: cfg.max, status });
      return;
    }
    btn.click();
    setBadge(`bid £${ask} on lot ${target} (max £${cfg.max})`, "#1a7f37");
    report({ type: "bid", lot: target, ask, current, max: cfg.max, status });
  }

  function statusObj() {
    const site = SITES.find((s) => s.detect());
    return {
      site: site ? site.name : null, cfg, log, lastMessage, badge: lastBadge, colour: lastColour,
      live, title: document.title,
    };
  }

  // Control surface the server calls with page.evaluate()
  window.__bidArm = (lot, max, debug) => {
    cfg = { armed: true, lot: String(lot), max: Number(max), debug: !!debug };
    lastClickedAsk = null; seenTarget = false; lastLogged = ""; log = []; lastMessage = "";
    save();
    report({ type: "arm", lot: cfg.lot, max: cfg.max, debug: cfg.debug });
    tick();
    return statusObj();
  };
  window.__bidStop = (message) => { disarm(message || "Stopped by you"); return statusObj(); };
  window.__bidStatus = () => statusObj();

  function start() {
    // React to the auction's live updates straight away; the interval is a backup.
    new MutationObserver((muts) => {
      if (muts.some((m) => !badge || !badge.contains(m.target))) tick();
    }).observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ["style", "class", "disabled"] });
    setInterval(tick, 250);
    console.log("[Bid Clicker] loaded on", location.hostname);
    tick();
  }

  // Injected before the page has a body, so wait for it
  if (document.body) start();
  else document.addEventListener("DOMContentLoaded", start, { once: true });
})();
