const DEFAULTS = {
  enabled: false,
  message: "Keep going.",
  delaySeconds: 5,
  maxRuns: 20,
  sessionCount: 0,
  totalCount: 0,
  lastRun: null,
};

const $ = (id) => document.getElementById(id);

function ago(ts) {
  const s = Math.round((Date.now() - ts) / 1000);
  if (s < 60) return `${s} seconds ago`;
  const m = Math.round(s / 60);
  if (m < 60) return `${m} minute${m === 1 ? "" : "s"} ago`;
  const h = Math.round(m / 60);
  return `${h} hour${h === 1 ? "" : "s"} ago`;
}

function render(s) {
  $("enabled").checked = s.enabled;
  document.body.classList.toggle("on", s.enabled);
  $("status").firstChild.textContent = s.enabled ? "Watching for completed runs " : "Idle ";
  $("session").textContent = s.sessionCount;
  $("total").textContent = s.totalCount;
  $("last").textContent = s.lastRun ? `Last auto-prompt: ${ago(s.lastRun)}` : "No auto-prompts yet";
}

chrome.storage.local.get(DEFAULTS, (s) => {
  $("message").value = s.message;
  $("delay").value = s.delaySeconds;
  $("maxRuns").value = s.maxRuns;
  render(s);
});

chrome.storage.onChanged.addListener(() => chrome.storage.local.get(DEFAULTS, render));

$("enabled").addEventListener("change", (e) => {
  const on = e.target.checked;
  // Turning it on starts a fresh session so the max-runs limit applies anew.
  chrome.storage.local.set(on ? { enabled: true, sessionCount: 0 } : { enabled: false });
});
$("message").addEventListener("input", (e) => chrome.storage.local.set({ message: e.target.value }));
$("delay").addEventListener("change", (e) => chrome.storage.local.set({ delaySeconds: Math.max(2, +e.target.value || 0) }));
$("maxRuns").addEventListener("change", (e) => chrome.storage.local.set({ maxRuns: Math.max(2, +e.target.value || 0) }));
$("reset").addEventListener("click", () => chrome.storage.local.set({ sessionCount: 0 }));
