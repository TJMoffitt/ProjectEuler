// Keeps the shared counters in one place so several tabs sending at
// once don't overwrite each other's increments.

let queue = Promise.resolve();

chrome.runtime.onMessage.addListener((msg) => {
  if (msg?.type !== "sent") return;
  queue = queue.then(async () => {
    const { sessionCount = 0, totalCount = 0 } = await chrome.storage.local.get(["sessionCount", "totalCount"]);
    await chrome.storage.local.set({
      sessionCount: sessionCount + 1,
      totalCount: totalCount + 1,
      lastRun: Date.now(),
    });
  });
});
