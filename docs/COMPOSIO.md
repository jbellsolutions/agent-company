# Composio Integration

Composio gives your workers access to 1000+ SaaS tools (Apollo, Gmail, LinkedIn, HubSpot, Notion, Slack, Stripe, etc.) through one unified API.

This repo wires Composio per-worker-role. Each worker only sees the tools it needs.

---

## Setup

### 1. Get an API key
- Sign up at **[app.composio.dev](https://app.composio.dev)**
- Developers → **API Keys** → create one
- Drop it in `.env`:
  ```
  COMPOSIO_API_KEY=ak_...
  ```

### 2. Connect your accounts
For each tool you want workers to use, you need to connect it once via OAuth in the Composio dashboard.

```bash
# Or via CLI:
pip install composio-cli
composio login
composio add gmail       # opens browser → Google OAuth
composio add linkedin    # opens browser → LinkedIn OAuth
composio add apollo      # API key flow
composio add hubspot
```

Each connection is account-level, so the bot acts on your behalf when calling these.

---

## How tools get assigned

`tools/composio_setup.py` maps each role to the apps it can use:

```python
ROLE_TOOLS: dict[str, list[str]] = {
    "prospector":  ["APOLLO"],
    "qualifier":   [],                            # pure LLM, no tools
    "outbound":    ["GMAIL", "LINKEDIN"],
    "writer":      ["GOOGLESHEETS", "NOTION"],
    "poster":      ["LINKEDIN", "TWITTER"],
    "sdr_lead":    ["APOLLO", "GMAIL", "LINKEDIN"],
    "content_lead":["NOTION", "GOOGLESHEETS"],
    "social_lead": ["LINKEDIN", "TWITTER"],
}
```

When a worker is invoked, `get_tools_for_role(worker.name)` returns the OpenAI-format tool schemas, which are passed into the OpenRouter call.

---

## Adding a new tool

1. **Connect the account** in Composio (`composio add stripe`)
2. **Update `ROLE_TOOLS`** in `tools/composio_setup.py`:
   ```python
   "renewals": ["GMAIL", "HUBSPOT", "STRIPE"],
   ```
3. The next worker run will auto-include the new tool. No code changes in the worker.

---

## Graceful degradation

If `COMPOSIO_API_KEY` isn't set, `get_tools_for_role()` returns `[]`. Workers fall back to **dry-run mode** — they generate the email/post content but don't actually send/publish.

This makes it safe to:
- Develop locally without a Composio key
- Show the system to a prospect without sending real emails
- Test prompt changes without risking spam

---

## Available apps (most-used)

| Category | Composio app names |
|---|---|
| Sales | `APOLLO`, `HUBSPOT`, `SALESFORCE`, `OUTREACH`, `LEMLIST` |
| Email | `GMAIL`, `OUTLOOK` |
| Social | `LINKEDIN`, `TWITTER`, `FACEBOOK`, `INSTAGRAM` |
| Docs | `NOTION`, `GOOGLEDOCS`, `GOOGLESHEETS`, `CONFLUENCE` |
| Comms | `SLACK`, `DISCORD`, `MICROSOFTTEAMS` |
| Payments | `STRIPE`, `PAYPAL` |
| CRM | `HUBSPOT`, `SALESFORCE`, `PIPEDRIVE`, `ATTIO` |
| Project mgmt | `LINEAR`, `JIRA`, `ASANA`, `TRELLO` |
| Dev | `GITHUB`, `GITLAB`, `LINEAR` |

Full list at **[composio.dev/apps](https://composio.dev/apps)** (1000+).

---

## Cost

Composio itself is free up to 10,000 actions/month. Past that, ~$0.001/action. The bigger cost is the underlying SaaS subscriptions (Apollo, HubSpot, etc.) — Composio just gives you one API to talk to them.

---

## Troubleshooting

**Worker says "no tools available" even though COMPOSIO_API_KEY is set.**
- The role might not have an entry in `ROLE_TOOLS`.
- The Composio app names might be wrong (must match `App.GMAIL` etc. exactly).
- The account might not be connected (check `composio list` or the dashboard).

**Tool calls fail with auth errors.**
- Reconnect the account: `composio remove gmail && composio add gmail`.
- Check the connection status in the Composio dashboard.

**Want to see what tools were actually injected?**
```python
from tools.composio_setup import get_tools_for_role
print(get_tools_for_role("outbound"))
```
