from __future__ import annotations

import os
import re
from pathlib import Path

import anthropic

from company.ceo import memory as mem

OPUS = "claude-opus-4-7"
SONNET = "claude-sonnet-4-6"
SYSTEM_PROMPT_PATH = Path(__file__).parent / "system_prompt.md"


def _text(block: anthropic.types.ContentBlock) -> str:
    return block.text if isinstance(block, anthropic.types.TextBlock) else ""


class CEO:
    """
    Per-company CEO agent. Receives directives from the Meta-Orchestrator,
    breaks them into tasks for team leads, synthesizes results.
    """

    def __init__(self, company_id: int, company_name: str, company_context: str) -> None:
        self.company_id = company_id
        self.company_name = company_name
        self.company_context = company_context
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        # Use Opus for the primary company, Sonnet can be swapped in for client/project companies
        self.model = OPUS

    def _build_system_prompt(self) -> str:
        history = mem.get_recent_history(self.company_id, limit=30)
        history_text = "\n".join(
            f"[{h['agent_name'] or h['role']}]: {h['content'][:200]}"
            for h in history
        ) or "No history yet."

        active = mem.get_active_tasks(self.company_id)
        tasks_text = "\n".join(
            f"- [{t['status']}] {t['assigned_to']}: {t['description'][:120]}"
            for t in active
        ) or "No active tasks."

        template = SYSTEM_PROMPT_PATH.read_text()
        return (
            template
            .replace("{{COMPANY_NAME}}", self.company_name)
            .replace("{{COMPANY_CONTEXT}}", self.company_context or "No context provided.")
            .replace("{{RECENT_HISTORY}}", history_text)
            .replace("{{ACTIVE_TASKS}}", tasks_text)
        )

    def _dispatch_to_lead(self, lead_name: str, instruction: str) -> str:
        """Route a task to the appropriate lead and return its result."""
        from company.leads.sdr_lead import SDRLead
        from company.leads.content_lead import ContentLead
        from company.leads.social_lead import SocialLead

        task_id = mem.create_task(
            company_id=self.company_id,
            description=instruction,
            assigned_to=lead_name,
        )
        mem.update_task(task_id, "in_progress")

        lead_map = {
            "sdr_lead": SDRLead,
            "content_lead": ContentLead,
            "social_lead": SocialLead,
        }
        lead_class = lead_map.get(lead_name)
        if not lead_class:
            result = f"Unknown lead: {lead_name}"
        else:
            lead = lead_class(company_id=self.company_id)
            result = lead.run(instruction)

        mem.update_task(task_id, "completed", result=result[:2000])
        return result

    def run(self, directive: str) -> str:
        """Process a directive from the Meta-Orchestrator."""
        system_prompt = self._build_system_prompt()

        mem.save_message(self.company_id, "orchestrator", "meta-orchestrator", directive)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": directive}],
        )
        ceo_reply = _text(response.content[0])

        # Dispatch any [TASK:lead_name] blocks
        task_pattern = re.compile(r"\[TASK:(\w+)\]\s*(.+?)(?=\[TASK:|\Z)", re.DOTALL)
        task_results: list[str] = []

        for match in task_pattern.finditer(ceo_reply):
            lead_name = match.group(1).strip()
            instruction = match.group(2).strip()
            result = self._dispatch_to_lead(lead_name, instruction)
            task_results.append(f"[{lead_name} result]: {result}")

        if task_results:
            # Synthesize results
            synthesis_prompt = (
                f"Original directive: {directive}\n\n"
                f"Team results:\n" + "\n\n".join(task_results) + "\n\n"
                "Synthesize these results into a concise report for the Meta-Orchestrator. "
                "Include: what was accomplished, key outcomes, anything requiring founder approval."
            )
            synthesis = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": synthesis_prompt}],
            )
            final = _text(synthesis.content[0])
            mem.save_message(self.company_id, "ceo", f"CEO:{self.company_name}", final)
            return final

        mem.save_message(self.company_id, "ceo", f"CEO:{self.company_name}", ceo_reply)
        return ceo_reply
