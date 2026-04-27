from __future__ import annotations

SDR_FLEET_CONFIG = {
    "name": "SDR Fleet",
    "description": "Outbound sales development: prospecting, qualification, personalized outreach",
    "lead": "sdr_lead",
    "workers": ["prospector", "qualifier", "outbound"],
    "composio_apps": ["APOLLO", "GMAIL", "LINKEDIN"],
    "example_prompt": (
        "Launch an SDR campaign targeting fintech companies with 50-200 employees. "
        "Find 50 leads, qualify to top 20 by ICP fit, send personalized intro emails."
    ),
}


def get_fleet_prompt(
    industry: str,
    headcount_min: int,
    headcount_max: int,
    additional_criteria: str = "",
) -> str:
    """Generate a structured SDR fleet activation prompt for the CEO."""
    return (
        f"Activate the SDR fleet for the following campaign:\n\n"
        f"Target: {industry} companies, {headcount_min}-{headcount_max} employees\n"
        f"Additional criteria: {additional_criteria or 'None'}\n\n"
        f"Steps:\n"
        f"1. [TASK:sdr_lead] Prospect: Find 50 {industry} companies "
        f"with {headcount_min}-{headcount_max} employees. "
        f"Return company name, LinkedIn URL, estimated headcount, primary contact.\n"
        f"2. [TASK:sdr_lead] Qualify: Score all 50 leads by ICP fit. Filter to top 20 scoring ≥50.\n"
        f"3. [TASK:sdr_lead] Outbound: Write and send personalized intro emails to all 20 qualified leads.\n\n"
        f"Report back: total prospected, total qualified, emails sent, any replies or flags."
    )
