from __future__ import annotations

import os
from typing import Any

# Role → Composio apps mapping
ROLE_TOOLS: dict[str, list[str]] = {
    "prospector": ["APOLLO"],
    "qualifier": [],                          # pure LLM scoring, no external tools needed
    "outbound": ["GMAIL", "LINKEDIN"],
    "writer": ["GOOGLESHEETS", "NOTION"],     # optional: for brief intake / doc storage
    "poster": ["LINKEDIN", "TWITTER"],
    "sdr_lead": ["APOLLO", "GMAIL", "LINKEDIN"],
    "content_lead": ["NOTION", "GOOGLESHEETS"],
    "social_lead": ["LINKEDIN", "TWITTER"],
}


def get_tools_for_role(role: str) -> list[Any]:
    """
    Return Composio OpenAI-format tools for the given worker/lead role.
    Returns [] if Composio is not configured or the role has no tools.
    """
    composio_key = os.environ.get("COMPOSIO_API_KEY", "")
    if not composio_key:
        return []

    app_names = ROLE_TOOLS.get(role, [])
    if not app_names:
        return []

    try:
        from composio_openai import ComposioToolSet, App

        toolset = ComposioToolSet(api_key=composio_key)
        apps = [getattr(App, name) for name in app_names if hasattr(App, name)]
        if not apps:
            return []
        return toolset.get_tools(apps=apps)  # type: ignore[return-value]
    except ImportError:
        # composio_openai not installed — graceful degradation
        return []
    except Exception:
        # Composio auth issue or network error — degrade gracefully
        return []


def list_connected_apps() -> list[str]:
    """Return list of connected Composio apps for the current API key."""
    composio_key = os.environ.get("COMPOSIO_API_KEY", "")
    if not composio_key:
        return []
    try:
        from composio_openai import ComposioToolSet
        toolset = ComposioToolSet(api_key=composio_key)
        # List connected accounts
        connections = toolset.client.connected_accounts.get()  # type: ignore[attr-defined]
        return [c.appName for c in connections]
    except Exception:
        return []
