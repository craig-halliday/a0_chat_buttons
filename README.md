# A0 Chat Buttons — Agent Zero plugin

Four chat controls in a single row on the chat input action bar: **Copy URL**, **Rename**, **Close** and **Stop**.

Agent Zero gives you *Pause* and *Nudge*, and chat management lives in the sidebar. What is missing is a fast row of controls attached to the chat you are actually reading. This plugin puts sharing, naming, dismissing and cancelling one click away from the message box.

![A0 Chat Buttons action bar](docs/action-bar.png)

## The four buttons

### Copy URL

Copies a deep link to the open chat (`?ctxid=...`) to the clipboard, so the conversation can be reopened in another tab, another browser or on another device. The link is built from the current page address with the chat id appended, which keeps it valid for whatever host and port you run Agent Zero on. Falls back to a hidden textarea when the Clipboard API is unavailable on non-secure origins.

### Rename

Opens a compact dialog pre-filled with the chat's current name. Type a new name and press `Enter`, or press `Escape` to cancel. Saving an empty field clears the custom name and restores the default `Chat #N` label.

The name is written to the chat's own `name` field through Agent Zero's chat persistence, so it survives a restart and shows up in the sidebar and the chat header. Repeated whitespace is collapsed and names are capped at 120 characters.

### Close

Clears the chat view and returns to the welcome screen without deleting anything. The conversation stays in the sidebar and can be reopened at any time. This is the "get this out of my face" action, not a destructive one.

### Stop

Cancels the agent process running in the active chat and returns it to idle. Beyond killing the agent's own task, it also:

- sends `SIGKILL` to child processes of the agent's active terminal sessions, which prevents orphaned pagers and long-running commands from lingering,
- sends `Ctrl+C` to those sessions,
- clears the paused flag,
- writes a `⛔ Process stopped by user.` warning into the chat log.

The button is greyed out and disabled while nothing is running, and turns red while a process is active. Only the chat you are looking at is affected.

## Behaviour notes

| Behaviour | Detail |
| --- | --- |
| Availability | All four buttons are disabled when no chat is open. The action bar only renders with an open chat, so nothing appears on the welcome screen. |
| Scope | Every action applies to the active chat only. Other chats are never touched. |
| Mobile | Below 768px the button labels hide and only the icons remain. |
| Feedback | Each action confirms with a notification toast, and errors are surfaced rather than swallowed. |

## Installation

1. Copy the `a0_chat_buttons` folder into `/a0/usr/plugins/`.
2. Enable **A0 Chat Buttons** in *Settings → Plugins*.
3. Reload the WebUI and open any chat.

No dependencies, no build step, no configuration and no settings screen.

## Requirements

- Agent Zero with the plugin system enabled.
- No external services, no network access, no API keys and no paid resources.

## Files

```text
a0_chat_buttons/
  plugin.yaml
  api/
    rename_chat.py            # saves a custom chat name
    stop_process.py           # cancels the running agent process
  extensions/webui/chat-input-bottom-actions-end/
    chat-buttons.html         # the four buttons, rename dialog and styles
  docs/
    action-bar.png            # screenshot used above
  webui/
    thumbnail.png             # plugin logo
```

## Limitations

- **Stop** sends `SIGKILL` to child processes, so unsaved state in a running interactive command is lost. That is the point of a cancel button.
- **Close** only clears the view. Use the sidebar to actually delete a chat.
- **Rename** changes the displayed name only; the chat id and its files are untouched.

## Uninstall

Disable or remove the plugin in *Settings → Plugins* and delete the `a0_chat_buttons` folder. Nothing is written outside the normal Agent Zero chat files, so no cleanup step is required. Chat names you set stay stored on those chats.

## License

MIT — see [LICENSE](LICENSE).
