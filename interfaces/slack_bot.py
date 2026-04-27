"""
Slack bot interface for the Meta-Orchestrator.

User DMs the bot → Meta-Orchestrator processes → reply in thread.

Setup:
  1. Create a Slack app at api.slack.com/apps
  2. Enable Socket Mode (for local dev) or Events API (for Railway/server)
  3. Add bot scopes: app_mentions:read, im:history, im:read, im:write, chat:write
  4. Set SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_APP_TOKEN in .env
  5. Run: python interfaces/slack_bot.py
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path so `orchestrator.*` and `company.*` resolve when
# running this file directly (`python interfaces/slack_bot.py`).
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(override=True)

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from orchestrator.agent import MetaOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)

orchestrator = MetaOrchestrator()

# Track per-user conversation history (in-memory; Postgres-backed for production)
_conversation_history: dict[str, list[dict[str, str]]] = {}


def _get_history(user_id: str) -> list[dict[str, str]]:
    if user_id not in _conversation_history:
        _conversation_history[user_id] = []
    return _conversation_history[user_id]


def _append_history(user_id: str, role: str, content: str) -> None:
    history = _get_history(user_id)
    history.append({"role": role, "content": content})
    # Keep last 20 turns to stay within context
    if len(history) > 40:
        _conversation_history[user_id] = history[-40:]


@app.event("message")
def handle_dm(event: dict, say: object) -> None:
    """Handle direct messages to the bot."""
    # Ignore bot messages and non-DMs
    if event.get("bot_id") or event.get("channel_type") != "im":
        return

    user_id = event.get("user", "unknown")
    user_text = event.get("text", "").strip()

    if not user_text:
        return

    logger.info(f"DM from {user_id}: {user_text[:80]}")

    # Post "thinking" indicator
    assert callable(say)
    say(text="_Thinking..._", thread_ts=event.get("ts"))

    history = _get_history(user_id)
    _append_history(user_id, "user", user_text)

    try:
        response = orchestrator.chat(user_text, history=history)
    except Exception as exc:
        logger.exception("Orchestrator error")
        response = f"Something went wrong: {exc}"

    _append_history(user_id, "assistant", response)

    say(text=response, thread_ts=event.get("ts"))


@app.event("app_mention")
def handle_mention(event: dict, say: object) -> None:
    """Handle @mentions in channels."""
    user_id = event.get("user", "unknown")
    # Strip the bot mention from the text
    text = event.get("text", "")
    # Remove <@BOTID> prefix
    import re
    user_text = re.sub(r"<@\w+>\s*", "", text).strip()

    if not user_text:
        assert callable(say)
        say(text="Yes? What do you need?", thread_ts=event.get("ts"))
        return

    history = _get_history(user_id)
    _append_history(user_id, "user", user_text)

    try:
        response = orchestrator.chat(user_text, history=history)
    except Exception as exc:
        logger.exception("Orchestrator error")
        response = f"Something went wrong: {exc}"

    _append_history(user_id, "assistant", response)
    assert callable(say)
    say(text=response, thread_ts=event.get("ts"))


if __name__ == "__main__":
    app_token = os.environ.get("SLACK_APP_TOKEN", "")
    if app_token:
        # Socket Mode — no public URL needed (good for local dev)
        handler = SocketModeHandler(app, app_token)
        logger.info("Starting Slack bot in Socket Mode...")
        handler.start()
    else:
        # HTTP mode — needs a public URL (for Railway/server deploy)
        logger.info("Starting Slack bot in HTTP mode on port 3000...")
        app.start(port=3000)
