from __future__ import annotations

SOCIAL_FLEET_CONFIG = {
    "name": "Social Fleet",
    "description": "Social media posting and engagement",
    "lead": "social_lead",
    "workers": ["poster"],
    "composio_apps": ["LINKEDIN", "TWITTER"],
    "example_prompt": (
        "Post 3 LinkedIn updates this week about AI in sales. Schedule: Mon, Wed, Fri."
    ),
}


def get_fleet_prompt(content: str, platforms: list[str]) -> str:
    platform_str = ", ".join(platforms)
    return (
        f"Activate the Social Fleet:\n\n"
        f"[TASK:social_lead] Post the following to {platform_str}:\n{content}"
    )
