from __future__ import annotations

import os
from abc import ABC, abstractmethod

import anthropic

from company.ceo import memory as mem

SONNET = "claude-sonnet-4-6"


def _text(block: anthropic.types.ContentBlock) -> str:
    return block.text if isinstance(block, anthropic.types.TextBlock) else ""


class BaseLead(ABC):
    """
    Sonnet-powered team lead. Receives tasks from CEO, coordinates workers.
    """

    name: str = "base_lead"

    def __init__(self, company_id: int) -> None:
        self.company_id = company_id
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    @abstractmethod
    def get_workers(self) -> list[str]:
        """Return list of worker names this lead can dispatch."""
        ...

    def _dispatch_worker(self, worker_name: str, task: str) -> str:
        """Instantiate the right worker and run the task."""
        from company.workers.prospector import Prospector
        from company.workers.qualifier import Qualifier
        from company.workers.outbound import OutboundWorker
        from company.workers.writer import WriterWorker
        from company.workers.poster import PosterWorker

        worker_map = {
            "prospector": Prospector,
            "qualifier": Qualifier,
            "outbound": OutboundWorker,
            "writer": WriterWorker,
            "poster": PosterWorker,
        }
        worker_class = worker_map.get(worker_name)
        if not worker_class:
            return f"Unknown worker: {worker_name}"

        task_id = mem.create_task(
            company_id=self.company_id,
            description=task,
            assigned_to=worker_name,
        )
        mem.update_task(task_id, "in_progress")

        worker = worker_class(company_id=self.company_id)
        result = worker.run(task)

        mem.update_task(task_id, "completed", result=result[:2000])
        return result

    def run(self, task: str) -> str:
        """Process a task from the CEO. Break it down, dispatch workers, synthesize."""
        import re

        response = self.client.messages.create(
            model=SONNET,
            max_tokens=1024,
            system=self.system_prompt,
            messages=[{"role": "user", "content": task}],
        )
        lead_plan = _text(response.content[0])

        # Dispatch [WORKER:name] blocks
        worker_pattern = re.compile(r"\[WORKER:(\w+)\]\s*(.+?)(?=\[WORKER:|\Z)", re.DOTALL)
        worker_results: list[str] = []

        for match in worker_pattern.finditer(lead_plan):
            worker_name = match.group(1).strip()
            worker_task = match.group(2).strip()
            result = self._dispatch_worker(worker_name, worker_task)
            worker_results.append(f"[{worker_name}]: {result}")

        if worker_results:
            synthesis = self.client.messages.create(
                model=SONNET,
                max_tokens=512,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Task: {task}\n\nWorker results:\n"
                            + "\n\n".join(worker_results)
                            + "\n\nSummarize outcomes for the CEO in 3-5 bullet points."
                        ),
                    }
                ],
            )
            return _text(synthesis.content[0])

        return lead_plan
