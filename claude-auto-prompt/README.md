# Claude Auto-Prompt (Chrome extension)

Each time Claude finishes a response on claude.ai, this extension types your
chosen text into the message box and clicks send.

## Install
1. Open `chrome://extensions` and switch on **Developer mode** (top right).
2. Click **Load unpacked** and pick this `claude-auto-prompt` folder.
3. Pin the extension, open it, type your text, and flip **Auto-Prompt** on.
4. Reload any claude.ai tabs that were already open.

## Settings
- **Text**: what gets sent after each completed response.
- **Delay**: seconds to wait after a response finishes before sending.
- **Max runs per tab**: each tab stops after this many sends (0 = no limit),
  so it can't loop forever and burn through your usage. Switching
  Auto-Prompt off and on again resets every tab's count.

## Multiple tabs
Every open claude.ai tab runs on its own, including tabs in the background.
Chrome's Memory Saver can put long-unused background tabs to sleep, and a
sleeping tab can't send anything; if that happens, add `claude.ai` under
`chrome://settings/performance` → "Always keep these sites active".

## How it detects a finished run
While Claude is writing, the page shows a "Stop" button. When that button goes
away, the run counts as finished. If claude.ai changes its page layout, the
selectors in `content.js` (`findStopButton`, `findComposer`, `findSendButton`)
may need updating.
