// Runs on claude.ai. Waits for Claude to finish responding, then types the
// message into the chat box and sends it, until the target count is reached.
(() => {
  if (window.__claudeAutoContinue) return;
  window.__claudeAutoContinue = true;

  const state = {
    running: false,
    sent: 0,
    max: 0,
    message: "continue",
    delayMs: 3000,
    status: "Idle",
  };
  let runId = 0;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const STOP_SELECTORS = [
    'button[aria-label="Stop response"]',
    'button[aria-label="Stop generating"]',
    'button[data-testid="stop-button"]',
  ].join(",");

  const SEND_SELECTORS = [
    'button[aria-label="Send message"]',
    'button[aria-label="Send Message"]',
    'button[data-testid="send-button"]',
  ].join(",");

  function getInput() {
    return (
      document.querySelector('div.ProseMirror[contenteditable="true"]') ||
      document.querySelector('[contenteditable="true"][role="textbox"]') ||
      document.querySelector("fieldset [contenteditable='true']") ||
      document.querySelector("textarea")
    );
  }

  function isGenerating() {
    return !!document.querySelector(STOP_SELECTORS);
  }

  // ---------- on-page overlay ----------
  let overlay;
  function renderOverlay() {
    if (!state.running && state.sent === 0) {
      overlay?.remove();
      overlay = null;
      return;
    }
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;bottom:16px;right:16px;z-index:2147483647;" +
        "background:#1f1e1d;color:#fff;font:13px system-ui,sans-serif;" +
        "padding:8px 12px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.3);" +
        "display:flex;gap:10px;align-items:center;";
      const text = document.createElement("span");
      const btn = document.createElement("button");
      btn.style.cssText =
        "background:#d97757;color:#fff;border:0;border-radius:5px;" +
        "padding:3px 8px;cursor:pointer;font:inherit;";
      btn.addEventListener("click", () => (state.running ? stop("Stopped") : hideOverlay()));
      overlay.append(text, btn);
      document.body.appendChild(overlay);
    }
    overlay.firstChild.textContent = `Auto-continue ${state.sent}/${state.max} — ${state.status}`;
    overlay.lastChild.textContent = state.running ? "Stop" : "×";
  }
  function hideOverlay() {
    state.sent = 0;
    renderOverlay();
  }

  function update(patch) {
    Object.assign(state, patch);
    renderOverlay();
    chrome.runtime.sendMessage({ type: "state", state: { ...state } }).catch(() => {});
  }

  // ---------- typing + sending ----------
  function typeMessage(input, text) {
    input.focus();
    if (input.tagName === "TEXTAREA") {
      const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set;
      setter.call(input, text);
      input.dispatchEvent(new Event("input", { bubbles: true }));
      return;
    }
    // Contenteditable (ProseMirror): select existing content and replace it.
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(input);
    sel.removeAllRanges();
    sel.addRange(range);
    if (!document.execCommand("insertText", false, text)) {
      input.textContent = text;
      input.dispatchEvent(new InputEvent("input", { bubbles: true, data: text, inputType: "insertText" }));
    }
  }

  function pressEnter(input) {
    const opts = { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true, cancelable: true };
    input.dispatchEvent(new KeyboardEvent("keydown", opts));
    input.dispatchEvent(new KeyboardEvent("keypress", opts));
    input.dispatchEvent(new KeyboardEvent("keyup", opts));
  }

  async function send(text) {
    const input = getInput();
    if (!input) throw new Error("Chat box not found");
    typeMessage(input, text);
    await sleep(300);
    pressEnter(input);
    await sleep(500);
    // If Enter didn't submit (text still in the box), click the send button.
    const stillThere = (input.value ?? input.textContent ?? "").trim() === text.trim();
    if (stillThere) {
      const btn = document.querySelector(SEND_SELECTORS);
      if (btn && !btn.disabled) btn.click();
    }
  }

  // Resolves once Claude has been idle (not generating, chat box present)
  // for `delayMs` continuously. Returns false if the run was cancelled.
  async function waitForIdle(id) {
    let idleSince = null;
    while (id === runId) {
      if (!isGenerating() && getInput()) {
        idleSince ??= Date.now();
        if (Date.now() - idleSince >= state.delayMs) return true;
      } else {
        idleSince = null;
      }
      await sleep(250);
    }
    return false;
  }

  // After sending, wait (up to 15s) for Claude to start responding so we
  // don't mistake the gap before the reply for "idle".
  async function waitForStart(id) {
    const deadline = Date.now() + 15000;
    while (id === runId && Date.now() < deadline) {
      if (isGenerating()) return;
      await sleep(250);
    }
  }

  async function run(id) {
    while (id === runId && state.sent < state.max) {
      update({ status: "Waiting for Claude to finish…" });
      if (!(await waitForIdle(id))) return;
      try {
        update({ status: `Sending "${state.message}"…` });
        await send(state.message);
      } catch (e) {
        stop(`Error: ${e.message}`);
        return;
      }
      update({ sent: state.sent + 1, status: "Waiting for reply to start…" });
      await waitForStart(id);
    }
    if (id === runId) stop("Done");
  }

  function start({ max, message, delayMs }) {
    runId++;
    update({
      running: true,
      sent: 0,
      max: Math.max(1, Number(max) || 1),
      message: message || "continue",
      delayMs: Math.max(0, Number(delayMs) || 0),
      status: "Starting…",
    });
    run(runId);
  }

  function stop(status = "Stopped") {
    runId++;
    update({ running: false, status });
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type === "start") start(msg);
    else if (msg.type === "stop") stop();
    sendResponse({ ...state });
  });
})();
