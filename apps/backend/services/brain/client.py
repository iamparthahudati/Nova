"""Calls to the Claude API: plain Q&A, and tool-routed requests.

Context comes exclusively from the Context Engine (2.8): one assemble() call
per turn yields the system prompt, the trimmed messages channel, and the exact
semantic memories injected — which reinforcement credits only if they survive
into the reply.
"""

import json
import urllib.request

from .config import ANTHROPIC_API_URL, CLAUDE_API_KEY, CLAUDE_MODEL
from .context_engine import assemble
from .reinforcement import reinforce
from .tools import ASSISTANT_TOOLS, ToolHandler
from .tools import execute as execute_tool


def _call_claude(body: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def ask(question: str, history: list[dict] | None = None) -> str:
    """Call Claude with optional conversation history for multi-turn context."""
    ctx = assemble(question, history)  # query-aware: recalls what's relevant now
    body = _call_claude(
        {
            "model": CLAUDE_MODEL,
            "max_tokens": 256,
            "system": ctx.system,
            "messages": ctx.messages + [{"role": "user", "content": question}],
        },
        timeout=15,
    )
    reply = body["content"][0]["text"].strip()
    reinforce(reply, ctx.memories)  # credit only memories used in the reply
    return reply


def route(
    transcript: str, handlers: dict[str, ToolHandler], history: list[dict] | None = None
) -> str:
    """Route a request via Claude tool use.

    Claude either calls a tool (action) or returns a text answer (conversation).
    `handlers` maps tool name -> a function taking the tool's input dict and
    returning the spoken response string. Returns the spoken response string
    in both cases.
    """
    ctx = assemble(transcript, history)  # query-aware: recalls what's relevant now
    body = _call_claude(
        {
            "model": CLAUDE_MODEL,
            "max_tokens": 512,
            "system": ctx.system,
            "tools": ASSISTANT_TOOLS,
            "tool_choice": {"type": "auto"},
            "messages": ctx.messages + [{"role": "user", "content": transcript}],
        },
        timeout=20,
    )

    stop_reason = body.get("stop_reason", "")
    content = body.get("content", [])

    if stop_reason == "tool_use":
        for block in content:
            if block.get("type") == "tool_use":
                print(f"[route] {block['name']} {block.get('input', {})}")
                reply = execute_tool(block["name"], block.get("input", {}), handlers)
                reinforce(reply, ctx.memories)
                return reply

    for block in content:
        if block.get("type") == "text":
            reply = block["text"].strip()
            reinforce(reply, ctx.memories)
            return reply
    return ""
