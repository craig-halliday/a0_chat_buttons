// A0 Chat Buttons — rewind control on finished chat answers.
// Places a rewind button in the answer action bar, after the built-in
// Show more / Copy / Speak controls and after any Branch chat button.

import {
  createActionButton,
} from "/components/messages/action-buttons/simple-action-buttons.js";
import { callJsonApi } from "/js/api.js";
import {
  toastFrontendError,
  toastFrontendInfo,
  toastFrontendSuccess,
} from "/components/notifications/notification-store.js";

const PLUGIN_TITLE = "A0 Chat Buttons";
const ENDPOINT = "/plugins/a0_chat_buttons/truncate_chat";
const BUTTON_CLASS = "a0cb-rewind-button";
const STYLE_ID = "a0cb-rewind-styles";
const BAR_SELECTOR = ".message-agent-response > .step-action-buttons";

async function rewindTo(logNo) {
  const ctxid = globalThis.getContext?.();
  if (!ctxid) {
    toastFrontendError("Open a chat first.", PLUGIN_TITLE);
    return;
  }

  let res;
  try {
    res = await callJsonApi(ENDPOINT, { context: ctxid, log_no: logNo });
  } catch (e) {
    toastFrontendError("Could not rewind: " + e.message, PLUGIN_TITLE);
    return;
  }

  if (!res?.ok) {
    toastFrontendError(res?.error || res?.message || "Rewind failed", PLUGIN_TITLE);
    return;
  }

  if (!res.removed) {
    toastFrontendInfo("Nothing follows this answer.", PLUGIN_TITLE);
    return;
  }

  toastFrontendSuccess(
    `Removed ${res.removed} later message${res.removed === 1 ? "" : "s"}.`,
    PLUGIN_TITLE,
  );

  // Pull a fresh snapshot right away instead of waiting for the next push.
  if (typeof globalThis.poll === "function") globalThis.poll();
}

function makeButton(logNo) {
  const button = createActionButton(
    "history",
    "Rewind chat to this answer",
    () => rewindTo(logNo),
  );
  button.classList.add(BUTTON_CLASS);
  button.dataset.logNo = String(logNo);
  return button;
}

function placeButton(bar, logNo) {
  const existing = bar.querySelector(`.${BUTTON_CLASS}[data-log-no="${logNo}"]`);
  if (existing) {
    if (bar.lastElementChild !== existing) bar.appendChild(existing);
    return;
  }

  bar.querySelectorAll(`.${BUTTON_CLASS}`).forEach((el) => el.remove());
  const button = makeButton(logNo);
  bar.appendChild(button);

  // Neighbouring plugins can append after this run; stay rightmost.
  requestAnimationFrame(() => {
    if (button.isConnected && bar.lastElementChild !== button) {
      bar.appendChild(button);
    }
  });
}

function injectStylesOnce() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = `
    .${BUTTON_CLASS} { opacity: 0.85; }
    .${BUTTON_CLASS}:hover { opacity: 1; }
  `;
  document.head.appendChild(style);
}

export default async function injectRewindButton(context) {
  if (!context?.results?.length) return;
  injectStylesOnce();

  for (const { args, result } of context.results) {
    if (!result?.element || args?.no == null) continue;
    if (args?.type !== "response") continue;

    const root = result.element;
    const bars = root.matches?.(BAR_SELECTOR)
      ? [root]
      : root.querySelectorAll(BAR_SELECTOR);

    for (const bar of bars) placeButton(bar, args.no);
  }
}
