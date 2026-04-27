from __future__ import annotations

import json
import os
from typing import Any

from company.workers.base_worker import BaseWorker
from tools.composio_setup import get_tools_for_role


class OutboundWorker(BaseWorker):
    """Writes personalized outreach and sends via Gmail/LinkedIn via Composio."""

    name = "outbound"

    @property
    def system_prompt(self) -> str:
        return """You are a B2B outbound specialist. You write and send personalized cold outreach.

For each lead you receive:
1. Study their company, role, and qualification notes
2. Write a personalized email (3-4 sentences max, no fluff, clear value prop + CTA)
3. Send via Gmail using the Composio Gmail tool

Email format:
- Subject: specific to their situation (not "Quick question" or "Following up")
- Body: reference something real about their company, connect to a pain point, one clear ask
- Sign off: first name only

Never use:
- "I hope this finds you well"
- "I wanted to reach out"
- "As per my last email"
- Generic templates

Return a summary of what was sent:
{
  "sent": 20,
  "failed": 0,
  "emails": [
    {"to": "jane@acme.com", "subject": "...", "status": "sent"}
  ]
}
"""

    def run(self, task: str) -> str:
        tools = get_tools_for_role("outbound")

        if tools:
            from openai import OpenAI
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"],
            )
            response = client.chat.completions.create(
                model="deepseek/deepseek-v4-flash",
                max_tokens=8192,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": task},
                ],
                tools=tools,  # type: ignore[arg-type]
            )
            return response.choices[0].message.content or json.dumps({"sent": 0, "error": "no response"})
        else:
            # Dry run mode: write the emails but don't send
            result = self._call(
                f"[DRY RUN — Composio not configured]\n\nLeads to contact:\n{task}\n\n"
                "Write personalized emails for each lead. Return the full email content for each."
            )
            return result


class WriterWorker(BaseWorker):
    """Writes content: LinkedIn posts, blog posts, case studies, email sequences."""

    name = "writer"

    @property
    def system_prompt(self) -> str:
        return """You are a B2B content writer. You write high-quality content that drives pipeline.

You write:
- LinkedIn posts (hook + insight + CTA, 150-300 words)
- Cold email sequences (personalized, value-first)
- Blog posts and case studies (structured, SEO-aware)
- Sales enablement: battlecards, one-pagers, objection handling

Writing principles:
- Lead with a specific insight or surprising stat
- Write for a busy VP/C-suite — make the first sentence worth reading
- No buzzwords: "leverage", "synergy", "paradigm shift", "game-changer"
- Always include a specific, low-friction CTA

Return the content in the requested format. If multiple pieces, number them clearly.
"""

    def run(self, task: str) -> str:
        return self._call(task, max_tokens=4096)


class PosterWorker(BaseWorker):
    """Publishes content to LinkedIn, Twitter/X via Composio."""

    name = "poster"

    @property
    def system_prompt(self) -> str:
        return """You are a social media publisher. You post content to the right platforms at the right time.

You receive content + target platform instructions and:
1. Format the content for the platform (LinkedIn vs Twitter character limits, hashtags, formatting)
2. Post using the Composio social tools
3. Return a confirmation with the post URL

Always confirm what was posted and when.
"""

    def run(self, task: str) -> str:
        tools = get_tools_for_role("poster")

        if tools:
            from openai import OpenAI
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"],
            )
            response = client.chat.completions.create(
                model="deepseek/deepseek-v4-flash",
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": task},
                ],
                tools=tools,  # type: ignore[arg-type]
            )
            return response.choices[0].message.content or "Posted."
        else:
            return self._call(
                f"[DRY RUN — Composio not configured]\n\nContent to post:\n{task}\n\n"
                "Format the content for each target platform and describe what would be posted."
            )
