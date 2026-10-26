// Claude Auto-Prompt content script.
// Watches claude.ai for a response to finish, then types the configured
// text into the composer and clicks send.

const DEFAULTS = {
  enabled: false,
  message: "Keep going.",
  delaySeconds: 3,
  maxRuns: 20,
  sessionCount: 0,
  totalCount: 0,
  lastRun: null,
};

let settings = { ...DEFAULTS };
let wasStreaming = false;
let pendingTimer = null;
let sending = false;

chrome.storage.local.get(DEFAULTS, (s) => { settings = s; });
chrome.storage.onChanged.addListener((changes) => {
  for (const [k, { newValue }] of Object.entries(changes)) settings[k] = newValue;
  if (changes.enabled && !changes.enabled.newValue) cancelPending();
});

function isVisible(el) {
  return !!el && el.offsetParent !== null;
}

function findStopButton() {
  return [...document.querySelectorAll("button[aria-label]")].find(
    (b) => /stop/i.test(b.getAttribute("aria-label")) && isVisible(b)
  );
}

function isStreaming() {
  return !!findStopButton() || !!document.querySelector('[data-is-streaming="true"]');
}

function findComposer() {
  return (
    document.querySelector('div.ProseMirror[contenteditable="true"]') ||
    document.querySelector('[contenteditable="true"][role="textbox"]') ||
    document.querySelector('fieldset [contenteditable="true"]') ||
    document.querySelector("textarea")
  );
}

function findSendButton() {
  const byLabel = [...document.querySelectorAll("button[aria-label]")].find((b) =>
    /send/i.test(b.getAttribute("aria-label"))
  );
  if (byLabel) return byLabel;
  const composer = findComposer();
  const form = composer && composer.closest("fieldset, form");
  return form ? form.querySelector('button[type="submit"]') : null;
}

function insertText(el, text) {
  el.focus();
  if (el.tagName === "TEXTAREA") {
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set;
    setter.call(el, text);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    return;
  }
  // Select any existing content so we replace it, then insert like a user would.
  const range = document.createRange();
  range.selectNodeContents(el);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  if (!document.execCommand("insertText", false, text)) {
    el.textContent = text;
    el.dispatchEvent(new InputEvent("input", { bubbles: true, data: text, inputType: "insertText" }));
  }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitFor(fn, timeoutMs) {
  const end = Date.now() + timeoutMs;
  while (Date.now() < end) {
    const v = fn();
    if (v) return v;
    await sleep(150);
  }
  return null;
}

function cancelPending() {
  if (pendingTimer) clearTimeout(pendingTimer);
  pendingTimer = null;
}

async function sendPrompt() {
  pendingTimer = null;
  if (!settings.enabled || sending || isStreaming()) return;
  if (settings.maxRuns > 0 && settings.sessionCount >= settings.maxRuns) {
    chrome.storage.local.set({ enabled: false });
    return;
  }
  const text = (settings.message || "").trim();
  if (!text) return;

  const composer = findComposer();
  if (!composer) return;

  sending = true;
  try {
    insertText(composer, text);
    const btn = await waitFor(() => {
      const b = findSendButton();
      return b && !b.disabled ? b : null;
    }, 3000);
    if (btn) {
      btn.click();
    } else {
      composer.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", keyCode: 13, bubbles: true }));
    }
    const now = Date.now();
    chrome.storage.local.set({
      sessionCount: (settings.sessionCount || 0) + 1,
      totalCount: (settings.totalCount || 0) + 1,
      lastRun: now,
    });
  } finally {
    // Give Claude a moment to start streaming before we look again.
    await sleep(2000);
    sending = false;
  }
}

function tick() {
  const streaming = isStreaming();
  if (streaming) {
    wasStreaming = true;
    cancelPending();
    return;
  }
  if (wasStreaming && !sending) {
    wasStreaming = false;
    if (settings.enabled && !pendingTimer) {
      pendingTimer = setTimeout(sendPrompt, Math.max(0, Number(settings.delaySeconds) || 0) * 1000);
    }
  }
}

setInterval(tick, 500);
