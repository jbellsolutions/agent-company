from __future__ import annotations

CONTENT_FLEET_CONFIG = {
    "name": "Content Fleet",
    "description": "Content production and distribution: research, writing, publishing",
    "lead": "content_lead",
    "workers": ["writer", "poster"],
    "composio_apps": ["NOTION", "GOOGLESHEETS", "LINKEDIN", "TWITTER"],
    "example_prompt": (
        "Create 3 LinkedIn posts about how AI is changing outbound sales. "
        "Research angle: time savings + personalization at scale. Publish on LinkedIn."
    ),
}


def get_fleet_prompt(topic: str, platforms: list[str], piece_count: int = 1) -> str:
    platform_str = ", ".join(platforms)
    return (
        f"Activate the Content Fleet:\n\n"
        f"Topic: {topic}\n"
        f"Pieces: {piece_count}\n"
        f"Platforms: {platform_str}\n\n"
        f"[TASK:content_lead] Research and write {piece_count} content piece(s) about: {topic}. "
        f"Optimize for {platform_str}. Once written, post to all platforms."
    )
