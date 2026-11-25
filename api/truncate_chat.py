"""Rewind a chat to a finished answer.

Deletes a chat result and everything after it from the current chat, in place.
The chat id is kept, so the next message continues from the trimmed context.
"""

import json
import uuid

from agent import Agent, AgentContext
from helpers import persist_chat
from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers.history import deserialize_history
from helpers.state_monitor_integration import mark_dirty_for_context


def _detach_response_ids(value: object) -> None:
    if isinstance(value, dict):
        metadata = value.get("metadata")
        responses = metadata.get("responses") if isinstance(metadata, dict) else None
        if isinstance(responses, dict):
            responses.pop("response_id", None)
            responses.pop("previous_response_id", None)
        for nested in value.values():
            _detach_response_ids(nested)
    elif isinstance(value, list):
        for nested in value:
            _detach_response_ids(nested)


def _trim_history_json(
    history_json: str, kept_ids: set[str], after_cut_ids: set[str]
) -> str:
    """Keep only history messages that survive the truncation cut."""
    if not history_json:
        return history_json

    hist = json.loads(history_json)
    keep = True

    def filter_messages(messages: list[dict]) -> list[dict]:
        nonlocal keep
        result = []
        for msg in messages:
            mid = msg.get("id", "")
            if mid and mid in after_cut_ids:
                keep = False
            elif mid and mid in kept_ids:
                keep = True
            if keep:
                result.append(msg)
        return result

    trimmed_topics = []
    for topic in hist.get("topics", []):
        if topic.get("summary"):
            trimmed_topics.append(topic)
            continue
        msgs = filter_messages(topic.get("messages", []))
        if msgs:
            topic["messages"] = msgs
            trimmed_topics.append(topic)
        if not keep:
            break
    hist["topics"] = trimmed_topics

    current = hist.get("current", {})
    if not current.get("summary") and keep:
        current["messages"] = filter_messages(current.get("messages", []))
    elif not keep:
        current["messages"] = []
    hist["current"] = current

    total = sum(
        len(t.get("messages", [])) for t in hist["topics"] if not t.get("summary")
    ) + len(hist.get("current", {}).get("messages", []))
    hist["counter"] = total
    _detach_response_ids(hist)

    return json.dumps(hist, ensure_ascii=False)


def _iter_agents(context: AgentContext):
    agent = context.agent0
    while agent:
        yield agent
        agent = agent.data.get(Agent.DATA_NAME_SUBORDINATE)


class TruncateChat(ApiHandler):
    """Delete a chat answer and everything after it from the current chat."""

    async def process(self, input: Input, request: Request) -> Output:
        ctxid = str(input.get("context", "") or "").strip()
        log_no = input.get("log_no")

        if not ctxid:
            return Response(status=400, response="Missing context id")
        if log_no is None:
            return Response(status=400, response="Missing log_no")

        context = AgentContext.get(ctxid)
        if not context:
            return Response(status=404, response="Chat not found")
        if context.is_running():
            return Response(status=409, response="The chat is still running")

        logs = list(context.log.logs)
        cut_idx = None
        for i, item in enumerate(logs):
            if item.no == log_no:
                cut_idx = i
                break
        if cut_idx is None:
            return Response(status=400, response="log_no not found in chat log")

        # Keep the clicked answer and everything before it; delete the rest.
        keep_count = cut_idx + 1

        kept_logs = logs[:keep_count]
        removed_logs = logs[keep_count:]

        # Nothing follows this answer: leave the chat untouched instead of
        # forcing a pointless full re-render.
        if not removed_logs:
            return {
                "ok": True,
                "context": context.id,
                "guid": context.log.guid,
                "removed": 0,
                "message": "Nothing to rewind.",
            }

        kept_ids = {item.id for item in kept_logs if item.id}
        # Keep wins if the same id shows up on both sides of the cut, so a
        # message the user kept is never dropped from agent memory.
        after_cut_ids = {item.id for item in removed_logs if item.id} - kept_ids

        log = context.log
        with log._lock:
            log.logs = kept_logs
            for index, item in enumerate(log.logs):
                item.no = index
            log.updates = list(range(len(log.logs)))
            # Rotating the guid makes every open tab drop its rendered state
            # and re-render from a full snapshot.
            log.guid = str(uuid.uuid4())

        for agent in _iter_agents(context):
            try:
                trimmed = _trim_history_json(
                    agent.history.serialize(), kept_ids, after_cut_ids
                )
                agent.history = deserialize_history(trimmed, agent)
            except Exception:
                agent.history = deserialize_history("", agent)
            agent.data.pop(Agent.DATA_NAME_RESPONSES_STATE, None)
            agent.data.pop(Agent.DATA_NAME_CTX_WINDOW, None)

        context.streaming_agent = context.agent0
        log.set_initial_progress()

        persist_chat.save_tmp_chat(context)

        try:
            mark_dirty_for_context(
                context.id, reason="a0_chat_buttons.truncate_chat"
            )
        except Exception:
            pass

        return {
            "ok": True,
            "context": context.id,
            "guid": log.guid,
            "removed": len(removed_logs),
            "message": "Chat rewound.",
        }
