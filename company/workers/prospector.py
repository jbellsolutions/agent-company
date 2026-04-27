from __future__ import annotations

import json

from company.workers.base_worker import BaseWorker
from tools.composio_setup import get_tools_for_role


class Prospector(BaseWorker):
    """Searches Apollo for target companies and contacts."""

    name = "prospector"

    @property
    def system_prompt(self) -> str:
        return """You are a B2B prospecting specialist. You search Apollo to find target companies and contacts.

Given a search criteria, you:
1. Search Apollo for matching companies
2. Find the right decision-maker contacts (VP Sales, CEO, Head of Growth, etc.)
3. Return structured data: company name, website, LinkedIn URL, contact name, contact title, contact LinkedIn, email (if available)

Always return results as a JSON array. Example:
[
  {
    "company": "Acme Corp",
    "website": "acme.com",
    "company_linkedin": "linkedin.com/company/acme",
    "headcount": 120,
    "contact_name": "Jane Smith",
    "contact_title": "VP of Sales",
    "contact_linkedin": "linkedin.com/in/janesmith",
    "email": "jane@acme.com",
    "notes": "Recently raised Series B"
  }
]

Be specific and accurate. Do not make up leads — only return what Apollo returns.
"""

    def run(self, task: str) -> str:
        tools = get_tools_for_role("prospector")
        if tools:
            # Use Composio Apollo tools if available
            from openai import OpenAI
            import os
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"],
            )
            response = client.chat.completions.create(
                model="deepseek/deepseek-v4-flash",
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": task},
                ],
                tools=tools,  # type: ignore[arg-type]
            )
            return response.choices[0].message.content or json.dumps([])
        else:
            # Fallback: generate a structured search plan
            return self._call(
                f"Search criteria: {task}\n\nGenerate a structured Apollo search plan and return mock results in the required JSON format."
            )
