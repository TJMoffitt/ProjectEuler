const $ = (id) => document.getElementById(id);
let tabId;

function render(state) {
  if (!state) return;
  $("status").textContent = `${state.status} (${state.sent}/${state.max})`;
  $("start").disabled = state.running;
  $("stop").disabled = !state.running;
}

async function sendToTab(msg) {
  try {
    return await chrome.tabs.sendMessage(tabId, msg);
  } catch {
    // Content script not loaded yet (e.g. tab was open before install): inject it.
    await chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] });
    return chrome.tabs.sendMessage(tabId, msg);
  }
}

async function init() {
  const saved = await chrome.storage.sync.get(["max", "message", "delay"]);
  if (saved.max) $("max").value = saved.max;
  if (saved.message) $("message").value = saved.message;
  if (saved.delay !== undefined) $("delay").value = saved.delay;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  tabId = tab?.id;
  try {
    render(await sendToTab({ type: "status" }));
  } catch {
    $("status").textContent = "Open a claude.ai chat in this tab.";
    $("start").disabled = $("stop").disabled = true;
  }
}

$("start").addEventListener("click", async () => {
  const max = parseInt($("max").value, 10) || 1;
  const message = $("message").value.trim() || "continue";
  const delay = parseFloat($("delay").value) || 0;
  await chrome.storage.sync.set({ max, message, delay });
  render(await sendToTab({ type: "start", max, message, delayMs: delay * 1000 }));
});

$("stop").addEventListener("click", async () => {
  render(await sendToTab({ type: "stop" }));
});

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === "state" && sender.tab?.id === tabId) render(msg.state);
});

init();
