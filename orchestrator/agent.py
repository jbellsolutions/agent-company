from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import anthropic

from company.ceo import memory as mem
from company.ceo.agent import CEO

OPUS = "claude-opus-4-7"
SYSTEM_PROMPT_PATH = Path(__file__).parent / "system_prompt.md"


class MetaOrchestrator:
    """
    Sovereign orchestrator. Routes all requests to the right company CEO.
    Never executes work itself.
    """

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._ceo_cache: dict[int, CEO] = {}

    def _build_system_prompt(self) -> str:
        companies = mem.list_companies()
        company_list = "\n".join(
            f"- {c['name']} (id={c['id']}): {c['context'][:100]}..." if c["context"] else f"- {c['name']} (id={c['id']})"
            for c in companies
        ) or "No companies yet. Create one by asking me to set up a company."

        active_tasks: list[str] = []
        for company in companies:
            tasks = mem.get_active_tasks(company["id"])
            for t in tasks:
                active_tasks.append(f"[{company['name']}] {t['assigned_to']}: {t['description'][:80]}")

        task_list = "\n".join(active_tasks) or "No active tasks."

        template = SYSTEM_PROMPT_PATH.read_text()
        return template.replace("{{COMPANY_LIST}}", company_list).replace("{{ACTIVE_TASKS}}", task_list)

    def _get_ceo(self, company_id: int, company_name: str, company_context: str) -> CEO:
        if company_id not in self._ceo_cache:
            self._ceo_cache[company_id] = CEO(
                company_id=company_id,
                company_name=company_name,
                company_context=company_context,
            )
        return self._ceo_cache[company_id]

    def _route_to_ceo(self, company_id: int, instruction: str) -> str:
        companies = mem.list_companies()
        company = next((c for c in companies if c["id"] == company_id), None)
        if not company:
            return f"Company id={company_id} not found."
        ceo = self._get_ceo(company_id, company["name"], company["context"] or "")
        return ceo.run(instruction)

    def _identify_company(self, user_message: str, companies: list[Any]) -> int | None:
        """Ask Claude to pick the right company from the message."""
        if not companies:
            return None
        if len(companies) == 1:
            return int(companies[0]["id"])

        company_descriptions = "\n".join(
            f"{c['id']}: {c['name']} — {c['context'][:100] if c['context'] else 'no context'}"
            for c in companies
        )
        response = self.client.messages.create(
            model=OPUS,
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Given this message: \"{user_message}\"\n\n"
                        f"Which company id is most relevant? Reply with ONLY the integer id, or 0 if none fit.\n\n"
                        f"{company_descriptions}"
                    ),
                }
            ],
        )
        try:
            block = response.content[0]
            text = block.text if hasattr(block, "text") else ""
            company_id = int(text.strip())
            return company_id if company_id > 0 else None
        except (ValueError, IndexError):
            return None

    def chat(self, user_message: str, history: list[dict[str, str]] | None = None) -> str:
        import re
        system_prompt = self._build_system_prompt()

        messages: list[dict[str, str]] = list(history or [])
        messages.append({"role": "user", "content": user_message})

        # Let Opus decide how to respond / which company to engage
        response = self.client.messages.create(
            model=OPUS,
            max_tokens=2048,
            system=system_prompt,
            messages=messages,  # type: ignore[arg-type]
        )
        block = response.content[0]
        orchestrator_reply = block.text if hasattr(block, "text") else ""

        # Check if orchestrator decided to delegate to a CEO
        # Simple heuristic: if reply contains [DELEGATE:company_id:instruction]
        if "[DELEGATE:" in orchestrator_reply:
            match = re.search(r"\[DELEGATE:(\d+):(.+?)\]", orchestrator_reply, re.DOTALL)
            if match:
                company_id = int(match.group(1))
                instruction = match.group(2).strip()
                ceo_result = self._route_to_ceo(company_id, instruction)
                # Feed CEO result back to orchestrator for synthesis
                messages.append({"role": "assistant", "content": orchestrator_reply})
                messages.append({"role": "user", "content": f"CEO result: {ceo_result}"})
                final_response = self.client.messages.create(
                    model=OPUS,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=messages,  # type: ignore[arg-type]
                )
                final_block = final_response.content[0]
                return final_block.text if hasattr(final_block, "text") else orchestrator_reply

        return orchestrator_reply

    def create_company(self, name: str, context: str) -> int:
        company_id = mem.get_or_create_company(name, context)
        return company_id

    def handle_slack_message(self, user_text: str, slack_user: str) -> str:
        result = self.chat(user_text)
        mem.save_message(
            company_id=0,
            role="user",
            agent_name=slack_user,
            content=user_text,
        ) if False else None  # global log — schema requires company_id; skip for now
        return result
