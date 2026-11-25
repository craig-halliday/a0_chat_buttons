# A0 Chat Buttons — Agent Zero plugin

Four buttons — **Copy URL**, **Rename**, **Close** and **Stop** — sit in a single row on the chat input action bar. A **chat name chip** with inline rename sits in the model strip, and **Rewind** sits on every finished answer.

Agent Zero gives you *Pause* and *Nudge*, and chat management lives in the sidebar. What is missing is a fast row of controls attached to the chat you are actually reading. This plugin puts sharing, naming, dismissing and cancelling one click away from the message box.

![A0 Chat Buttons action bar](docs/action-bar.png)

## The buttons

### Copy URL

Copies a deep link to the open chat (`?ctxid=...`) to the clipboard, so the conversation can be reopened in another tab, another browser or on another device. The link is built from the current page address with the chat id appended, which keeps it valid for whatever host and port you run Agent Zero on. Falls back to a hidden textarea when the Clipboard API is unavailable on non-secure origins.

### Chat name and inline rename

![Chat name chip](docs/chat-name-chip.png)

The active chat's name is shown as a compact chip at the end of the model/context strip, prefixed with the owning project's full title in the project's colour when the chat belongs to a project (resolved from the projects list, since the chat context carries only a shortened title), next to the model selector and the context-window ring. Long project titles and chat names are ellipsised instead of pushing the strip wider, and only the pencil carries a hover tooltip.

A pencil button sits inside the chip, so the chat can be renamed without leaving the row you are reading. Rename is confined to that pencil: clicking the name text never opens a dialog.

Clicking the project name or the chat name instead opens a small panel showing both in full, which matters because both are ellipsised in the strip. The same click also reveals the chat in the sidebar — it scrolls the row into view and flashes it — so a long chat title that is cut off in the header can be found in the list immediately. This reveal only runs when the sidebar is open; with the sidebar collapsed the panel says so instead of forcing the sidebar open.

The name is read from `$store.chats.selectedContext` through the store's `displayName()` helper, so it follows renames, parent-context labels and the default `Chat #N` fallback reactively, and it updates the sidebar and header at the same time.

This chip is a WebUI extension mounted on the `model-context-strip-end` extension point, so it appears only when the bundled model selector strip is rendered. When that strip is hidden (no chat open, or the `_model_config` strip disabled), the chip is hidden with it and the Rename button on the action bar remains the fallback.

### Rename

Opens a compact dialog pre-filled with the chat's current name. Type a new name and press `Enter`, or press `Escape` to cancel. Saving an empty field clears the custom name and restores the default `Chat #N` label.

The name is written to the chat's own `name` field through Agent Zero's chat persistence, so it survives a restart and shows up in the sidebar and the chat header. Repeated whitespace is collapsed and names are capped at 120 characters.

### Close

Clears the chat view and returns to the welcome screen without deleting anything. The conversation stays in the sidebar and can be reopened at any time.

### Stop

Cancels the agent process running in the active chat and returns it to idle. Beyond killing the agent's own task, it also:

- sends `SIGKILL` to child processes of the agent's active terminal sessions, which prevents orphaned pagers and long-running commands from lingering,
- sends `Ctrl+C` to those sessions,
- clears the paused flag,
- writes a `⛔ Process stopped by user.` warning into the chat log.

The button is greyed out and disabled while nothing is running, and turns red while a process is active. Only the chat you are looking at is affected.

### Rewind

Sits on every finished answer, to the right of the built-in *Show more*, *Copy* and *Speak* controls. Clicking it keeps that answer, deletes every message that came after it, and leaves the chat itself in place with the same id, name and sidebar position.

The deleted turns are removed from the agent's memory as well as the visible chat, so the next message continues from the trimmed context rather than from work you just discarded. The log id is rotated, which makes every open tab drop its rendered history and repaint from a fresh snapshot.

Three rules keep it predictable:

- nothing is deleted while the chat is still generating,
- if nothing follows the clicked answer the chat is left untouched, and
- the answer you clicked always survives.

This is the destructive sibling of *Branch chat*: branching copies the chat and keeps the original, rewind trims the chat you are already in.

## Behaviour notes

| Behaviour | Detail |
| --- | --- |
| Availability | The input-bar buttons are disabled when no chat is open. The action bar only renders with an open chat, so nothing appears on the welcome screen. |
| Rewind placement | The Rewind button only appears on finished answers, never on process, tool or status rows. |
| Scope | Every action applies to the active chat only. Other chats are never touched. |
| Mobile | Below 768px the button labels hide and only the icons remain. |
| Feedback | Each action confirms with a notification toast, and errors are surfaced rather than swallowed. |

## Requirements

- Agent Zero with the plugin system enabled.
- No external services, no network access, no API keys and no paid resources.
- No dependencies, no build step, no configuration and no settings screen.
- No Python dependencies, so the plugin ships no `hooks.py`: there is nothing to install, migrate or clean up. Enabling and disabling it in *Settings → Plugins* is the whole lifecycle.

## Version history

- **1.3.0** — Copy URL, Rename, Close and Stop controls on the chat input action bar.
- **1.4.0** — Rewind control on finished answers, with history trimming for the agent's memory.
- **1.5.0** — Active chat name chip in the model context strip, with inline rename.
- **1.6.0** — Project prefix on the chip, shown in the project's colour; removed the competing chat-name hover tooltip.
- **1.7.0** — Project prefix resolves the full project title from the projects list and follows project changes reactively. **First public release.**
- **1.8.0** — Rename is confined to the pencil; clicking the project or chat name reveals both in full and highlights the chat in the sidebar list.
- **1.8.1** — Sidebar reveal checks the real sidebar state; a collapsed sidebar shows a hint instead of silently failing.

## Files

```text
a0_chat_buttons/
  plugin.yaml
  api/
    rename_chat.py            # saves a custom chat name
    stop_process.py           # cancels the running agent process
    truncate_chat.py          # deletes an answer and everything after it
  extensions/webui/chat-input-bottom-actions-end/
    chat-buttons.html         # the input-bar buttons, rename dialog and styles
  extensions/webui/model-context-strip-end/
    chat-name.html            # active chat name chip with inline rename
  extensions/webui/set_messages_after_loop/
    inject-rewind-button.js   # the Rewind button on finished answers
  docs/
    action-bar.png            # action bar screenshot
    chat-name-chip.png        # chat name chip screenshot
  webui/
    thumbnail.png             # plugin logo
```

## Limitations

- **Stop** sends `SIGKILL` to child processes, so unsaved state in a running interactive command is lost. That is the point of a cancel button.
- **Close** only clears the view. Use the sidebar to actually delete a chat.
- **Rename** changes the displayed name only; the chat id and its files are untouched.
- **Rewind** is destructive by design: the deleted turns are gone from the chat and from the agent's memory. Use *Branch chat* instead when you want to keep the original.

## Uninstall

Disable or remove the plugin in *Settings → Plugins* and delete the `a0_chat_buttons` folder. Nothing is written outside the normal Agent Zero chat files, so no cleanup step is required. Chat names you set stay stored on those chats.

## License

MIT — see [LICENSE](LICENSE).
