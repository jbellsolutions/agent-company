from __future__ import annotations

import json

from company.workers.base_worker import BaseWorker


class Qualifier(BaseWorker):
    """Scores leads by ICP fit and returns ranked, filtered list."""

    name = "qualifier"

    @property
    def system_prompt(self) -> str:
        return """You are a B2B lead qualification specialist.

Given a list of leads and qualification criteria, you score each lead on:
- Company fit (industry, headcount, funding stage, revenue signals): 0-40 points
- Contact fit (seniority, decision-making authority, role relevance): 0-30 points
- Timing signals (recent funding, hiring for sales roles, tech stack changes, job postings): 0-30 points

Return a JSON array sorted by score (highest first), including only leads scoring ≥ 50:
[
  {
    "company": "Acme Corp",
    "contact_name": "Jane Smith",
    "contact_title": "VP of Sales",
    "contact_linkedin": "linkedin.com/in/janesmith",
    "email": "jane@acme.com",
    "score": 87,
    "score_breakdown": {
      "company_fit": 35,
      "contact_fit": 28,
      "timing_signals": 24
    },
    "qualification_notes": "Series B funded, actively hiring SDRs, uses Salesforce"
  }
]

Be rigorous. A score below 50 means do not contact.
"""

    def run(self, task: str) -> str:
        result = self._call(
            f"Leads and criteria to qualify:\n\n{task}",
            max_tokens=4096,
        )
        # Validate it's parseable JSON — if not, ask for a fix
        try:
            json.loads(result)
        except json.JSONDecodeError:
            result = self._call(
                f"The following is not valid JSON. Fix it and return ONLY valid JSON:\n\n{result}",
                max_tokens=4096,
            )
        return result
