# Adding a New Fleet

A fleet = one Lead + N Workers. The repo ships with three (SDR, Content, Social). Here's how to add your own.

We'll build a **Customer Success fleet** as the example.

---

## 1. Define the workers

Create `company/workers/cs_workers.py`:

```python
from __future__ import annotations
from company.workers.base_worker import BaseWorker


class RenewalsWorker(BaseWorker):
    """Identifies upcoming renewals and drafts personalized check-ins."""
    name = "renewals"

    @property
    def system_prompt(self) -> str:
        return """You are a Customer Success specialist focused on renewals.

For each upcoming renewal, you:
1. Look at the customer's usage data and last 90 days of activity
2. Identify expansion or risk signals
3. Draft a personalized check-in email
4. Tag the account: green (auto-renew), yellow (needs touch), red (at risk)

Return JSON: [{"customer": "...", "tag": "green|yellow|red", "email_draft": "..."}]
"""

    def run(self, task: str) -> str:
        return self._call(task, max_tokens=4096)


class NPSTriageWorker(BaseWorker):
    """Reads NPS responses, categorizes, drafts reply."""
    name = "nps_triage"

    @property
    def system_prompt(self) -> str:
        return """You triage NPS responses.

For each response:
- Promoters (9-10): draft a thank-you + ask for referral or testimonial
- Passives (7-8): draft a "what would make this a 10?" follow-up
- Detractors (0-6): flag for human follow-up; draft an apology + investigation request

Return JSON with: customer, score, category, draft_reply, escalate (bool)
"""

    def run(self, task: str) -> str:
        return self._call(task, max_tokens=4096)
```

---

## 2. Define the lead

Create `company/leads/cs_lead.py`:

```python
from __future__ import annotations
from company.leads.base_lead import BaseLead


class CSLead(BaseLead):
    name = "cs_lead"

    @property
    def system_prompt(self) -> str:
        return """You are the Customer Success Lead.

Your workers:
- **renewals** — checks upcoming renewals, drafts outreach, tags risk
- **nps_triage** — categorizes NPS responses, drafts replies

Dispatch with:
[WORKER:renewals] <customer list or date window>
[WORKER:nps_triage] <NPS responses to process>

Rules:
- Always escalate red-tagged accounts to the founder via the CEO
- Never auto-send renewal emails > $50K ARR without explicit approval
- Promoters get referral asks within 48 hours
"""

    def get_workers(self) -> list[str]:
        return ["renewals", "nps_triage"]
```

---

## 3. Register the workers in BaseLead's dispatch map

Edit `company/leads/base_lead.py`, in `_dispatch_worker`:

```python
from company.workers.cs_workers import RenewalsWorker, NPSTriageWorker

worker_map = {
    "prospector": Prospector,
    "qualifier": Qualifier,
    "outbound": OutboundWorker,
    "writer": WriterWorker,
    "poster": PosterWorker,
    "renewals": RenewalsWorker,        # ← add
    "nps_triage": NPSTriageWorker,     # ← add
}
```

---

## 4. Register the lead in CEO's dispatch map

Edit `company/ceo/agent.py`, in `_dispatch_to_lead`:

```python
from company.leads.cs_lead import CSLead

lead_map = {
    "sdr_lead": SDRLead,
    "content_lead": ContentLead,
    "social_lead": SocialLead,
    "cs_lead": CSLead,                 # ← add
}
```

---

## 5. (Optional) Wire up Composio tools

If your workers need to call external APIs, edit `tools/composio_setup.py`:

```python
ROLE_TOOLS: dict[str, list[str]] = {
    # ... existing entries
    "renewals": ["GMAIL", "HUBSPOT", "STRIPE"],   # to fetch contracts + send emails
    "nps_triage": ["GMAIL", "HUBSPOT"],
}
```

The worker base class auto-injects these tools when Composio is configured.

---

## 6. Update the CEO system prompt

Edit `company/ceo/system_prompt.md` — add the new lead to the "Your Team" section:

```markdown
## Your Team

- **SDR Lead** — prospecting, qualification, outbound
- **Content Lead** — research, writing, distribution
- **Social Lead** — monitoring, engagement, posting
- **CS Lead** — renewals, NPS triage, expansion         ← add
```

---

## 7. (Optional) Create a fleet activation prompt

Create `fleets/cs_fleet.py`:

```python
CS_FLEET_CONFIG = {
    "name": "Customer Success Fleet",
    "description": "Renewals, NPS triage, expansion outreach",
    "lead": "cs_lead",
    "workers": ["renewals", "nps_triage"],
    "composio_apps": ["GMAIL", "HUBSPOT", "STRIPE"],
}


def get_renewal_check_prompt(window_days: int = 30) -> str:
    return (
        f"Run a renewal check for the next {window_days} days.\n\n"
        f"[TASK:cs_lead] Pull all customers with renewal date in next {window_days} days. "
        f"Tag risk (green/yellow/red), draft check-in emails for yellow/red, escalate red to me."
    )
```

---

## 8. Test it

Restart the bot, then DM:
```
Run a renewal check for the next 30 days.
```

The Meta-Orchestrator routes to your CEO → CEO sees the new `[TASK:cs_lead]` syntax → dispatches to CSLead → CSLead breaks into worker tasks → workers execute.

That's it. New fleet, ~80 lines of code, no framework changes.

---

## Patterns to keep in mind

- **One responsibility per worker.** Don't make a "do everything" worker. Workers should be < 100 lines and have one clear input/output contract.
- **JSON output for downstream consumption.** If a worker's output feeds another worker (e.g., prospector → qualifier), use strict JSON. The qualifier example in `company/workers/qualifier.py` shows the validate-and-retry pattern.
- **Composio when there's a real integration; LLM when it's pure reasoning.** The `qualifier` worker is pure LLM (no tools); the `outbound` worker uses Composio Gmail. Pick based on the task.
- **Always update the CEO system prompt.** If the CEO doesn't know your new lead exists, it'll never delegate to it.
