from helpers.api import ApiHandler, Request, Response
from agent import AgentContext
from helpers.persist_chat import save_tmp_chat

MAX_NAME_LENGTH = 120


class RenameChat(ApiHandler):
    """Rename a chat by storing a custom name on its context."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = str(input.get("context", "") or "").strip()
        name = input.get("name", "")

        if not ctxid:
            return Response(status=400, response="Missing context id")
        if not isinstance(name, str):
            return Response(status=400, response="The name must be a string")

        name = " ".join(name.split())
        if len(name) > MAX_NAME_LENGTH:
            return Response(
                status=400,
                response=f"The name is too long (max {MAX_NAME_LENGTH} characters)",
            )

        ctx = AgentContext.get(ctxid)
        if not ctx:
            return Response(status=404, response="Chat not found")

        # An empty name clears the custom label and restores the default.
        ctx.name = name or None
        save_tmp_chat(ctx)

        try:
            from helpers.state_monitor_integration import mark_dirty_for_context

            mark_dirty_for_context(ctx.id, reason="a0_chat_buttons.rename_chat")
        except Exception:
            pass

        return {"ok": True, "context": ctx.id, "name": ctx.name or ""}
