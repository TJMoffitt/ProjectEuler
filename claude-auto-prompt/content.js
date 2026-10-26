// Claude Auto-Prompt content script.
// Watches claude.ai for a response to finish, then types the configured
// text into the composer and clicks send.
//
// Runs independently in every claude.ai tab. Chrome heavily throttles
// timers in background tabs (down to once a minute), so instead of polling
// we react to DOM changes with a MutationObserver, which keeps firing in
// hidden tabs.

const DEFAULTS = {
  enabled: false,
  message: "Keep going.",
  delaySeconds: 3,
  maxRuns: 20,
};

let settings = { ...DEFAULTS };
let wasStreaming = false;
let pendingTimer = null;
let sending = false;
let tabRuns = 0; // sends from this tab since Auto-Prompt was switched on

chrome.storage.local.get(DEFAULTS, (s) => {
  settings = s;
  check();
});
chrome.storage.onChanged.addListener((changes) => {
  for (const [k, { newValue }] of Object.entries(changes)) {
    if (k in DEFAULTS) settings[k] = newValue;
  }
  if (changes.enabled) {
    tabRuns = 0;
    if (!changes.enabled.newValue) cancelPending();
  }
});

function isVisible(el) {
  return !!el && el.getClientRects().length > 0;
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

function composerText(el) {
  return el.tagName === "TEXTAREA" ? el.value : el.innerText;
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
  document.execCommand("insertText", false, text);
  if (composerText(el).trim()) return;

  // In a background tab execCommand can be ignored; a synthetic paste
  // works because the editor reads the text from clipboardData.
  const data = new DataTransfer();
  data.setData("text/plain", text);
  el.dispatchEvent(new ClipboardEvent("paste", { clipboardData: data, bubbles: true, cancelable: true }));
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function cancelPending() {
  if (pendingTimer) clearTimeout(pendingTimer);
  pendingTimer = null;
}

async function sendPrompt() {
  pendingTimer = null;
  if (!settings.enabled || sending || isStreaming()) return;
  if (settings.maxRuns > 0 && tabRuns >= settings.maxRuns) return;
  const text = (settings.message || "").trim();
  if (!text) return;

  const composer = findComposer();
  if (!composer) return;

  sending = true;
  try {
    insertText(composer, text);
    // Let the editor re-render so the send button becomes enabled.
    await sleep(300);
    const btn = findSendButton();
    if (btn && !btn.disabled) {
      btn.click();
    } else {
      composer.dispatchEvent(
        new KeyboardEvent("keydown", { key: "Enter", code: "Enter", keyCode: 13, bubbles: true, cancelable: true })
      );
    }
    tabRuns++;
    // Counters are shared by every tab, so the background worker updates them.
    chrome.runtime.sendMessage({ type: "sent" });
  } finally {
    // Give Claude a moment to start streaming before we look again.
    await sleep(1500);
    sending = false;
    check();
  }
}

function check() {
  if (isStreaming()) {
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

// Coalesce bursts of DOM mutations (streaming produces many) into one check.
let checkQueued = false;
new MutationObserver(() => {
  if (checkQueued) return;
  checkQueued = true;
  queueMicrotask(() => {
    checkQueued = false;
    check();
  });
}).observe(document.documentElement, {
  childList: true,
  subtree: true,
  attributes: true,
  attributeFilter: ["aria-label", "data-is-streaming", "disabled"],
});
