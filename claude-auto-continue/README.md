# Claude Auto-Continue (Chrome extension)

Automatically types `continue` (or any message you choose) into the claude.ai
chat box and presses Enter, up to a set number of times. Each time it waits
until Claude has finished responding before sending the next message.

## Install

1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top right).
3. Click **Load unpacked** and select this `claude-auto-continue` folder.

## Use

1. Open a conversation on https://claude.ai.
2. Click the extension icon.
3. Set **Number of times**, the **Message** (default `continue`) and how long
   to wait after Claude finishes before sending (default 3 seconds).
4. Click **Start**. A small counter appears in the bottom-right of the page
   with a **Stop** button; you can also stop from the popup.

The run stops automatically once the count is reached, or if the chat box
can't be found. Reloading the page also stops it.

## How it works

`content.js` polls the page: while Claude's "Stop response" button is visible
it treats Claude as busy. Once Claude has been idle for the chosen delay, it
inserts the message into the chat box, presses Enter (falling back to the send
button), and waits for the next reply to begin before counting again.

If claude.ai changes its markup, the selectors at the top of `content.js`
(`STOP_SELECTORS`, `SEND_SELECTORS`, `getInput`) are the place to update.
