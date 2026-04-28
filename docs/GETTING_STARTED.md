# Getting Started — Your First Day

You have the bot running. Now what?

This is the 30-minute walkthrough from "bot is alive" to "first SDR campaign sent and reported back to Slack."

---

## Pre-flight checklist

Before you DM the bot, confirm:

- [ ] `python interfaces/slack_bot.py` is running (you see `⚡️ Bolt app is running!`)
- [ ] You can DM the bot in Slack (input box is active, not grayed out — see [SLACK_SETUP.md](SLACK_SETUP.md) if not)
- [ ] `.env` has `ANTHROPIC_API_KEY` and `OPENROUTER_API_KEY` filled in
- [ ] (Optional) `COMPOSIO_API_KEY` set + accounts connected for any tools you want to use

---

## Step 1 — Say hi

DM the bot:
```
hi
```

You should get a response within ~5 seconds. The Meta-Orchestrator is Opus 4.7; it'll greet you and probably ask what company you want to set up.

If nothing happens within 30 seconds, check the bot's terminal — there's almost certainly an error printed. Most common: missing API key, wrong model name, or rate limit.

---

## Step 2 — Create your first company

The orchestrator routes work to per-company CEOs. You need at least one company before you can do anything useful.

DM:
```
Create a company called Using AI to Scale.

We help founders build AI-powered sales teams. Our ICP is B2B SaaS
companies with 50-500 employees, post-Series A funding. Tone is
direct, ROI-focused, no marketing fluff. Primary outbound channel
is email + LinkedIn DMs.
```

The orchestrator will create the company in SQLite and confirm. You can verify:

```bash
sqlite3 agentcompany.db "SELECT id, name, substr(context, 1, 80) FROM companies;"
```

You should see one row.

---

## Step 3 — Run a test campaign in dry-run mode

If you don't have Composio configured yet, the SDR fleet runs in **dry-run mode** — it'll generate the prospects and emails but won't actually send them. Perfect for your first test.

DM:
```
Launch an SDR test campaign for Using AI to Scale.
Target: B2B SaaS companies, 100-300 employees, recently raised Series A.
Find 10 leads, qualify, draft personalized emails. Don't send — show me first.
```

What happens behind the scenes:

1. **Meta-Orchestrator (Opus 4.7)** sees the request, routes to your company's CEO.
2. **CEO (Opus 4.7)** breaks it into 3 tasks: prospect → qualify → draft.
3. **SDR Lead (Sonnet 4.6)** dispatches:
   - **Prospector** (DeepSeek) generates 10 plausible leads
   - **Qualifier** (DeepSeek) scores them by ICP fit
   - **Outbound** (DeepSeek) drafts personalized emails
4. **CEO** synthesizes the results into a report.
5. **Orchestrator** posts the report to your Slack DM.

Total wall time: 30-60 seconds. Total cost: ~$0.05.

---

## Step 4 — Inspect what just happened

Open a terminal and run:

```bash
cd ~/Desktop/agent-company

# See all messages from this session
sqlite3 agentcompany.db "
  SELECT role, agent_name, substr(content, 1, 120)
  FROM conversations
  ORDER BY id DESC LIMIT 20;
"

# See all tasks the CEO created
sqlite3 agentcompany.db "
  SELECT id, status, assigned_to, substr(description, 1, 80)
  FROM tasks ORDER BY id DESC LIMIT 10;
"
```

You'll see the full chain:
- Orchestrator's delegation to the CEO
- CEO's plan (with `[TASK:sdr_lead]` blocks)
- Lead's plan (with `[WORKER:prospector]` etc)
- Each worker's output

This is the source of truth. The Slack messages are summaries — the DB has the full reasoning.

---

## Step 5 — Connect Composio (when ready to send real messages)

Skip if you're still testing. When you want to actually send emails / post on LinkedIn:

1. Sign up at [app.composio.dev](https://app.composio.dev)
2. Get your API key, drop it in `.env` → `COMPOSIO_API_KEY=ak_...`
3. Connect your accounts via OAuth in the Composio dashboard:
   - Gmail (for outbound emails)
   - LinkedIn (for DMs and posts)
   - Apollo (for real prospect data)
4. Restart the bot: kill it, then `python interfaces/slack_bot.py`

Now the same SDR campaign command will hit real APIs. Workers detect Composio is available and switch out of dry-run mode automatically.

See [COMPOSIO.md](COMPOSIO.md) for the full setup.

---

## Step 6 — Run a real campaign

DM:
```
Launch an SDR campaign for Using AI to Scale.
Target: B2B SaaS, 100-300 employees, raised Series A in last 12 months.
Find 50 leads, qualify to top 20, send personalized intros via Gmail.
Report back when done.
```

The bot will execute. ~3-5 minutes for 20 sends. Cost: ~$0.30.

You'll get a Slack reply like:
```
✅ SDR Campaign Complete (Using AI to Scale)
• 50 leads prospected via Apollo
• 21 qualified (ICP score ≥ 50)
• 20 personalized intros sent via Gmail
• 1 reply received (flagged for review)
• Cost: $0.31

Top hot leads:
1. Jane Smith @ Acme Co (score: 89, replied within 4 min)
2. Bob Roberts @ XYZ Corp (score: 76, opened 3x)
3. ...
```

Check your Sent folder in Gmail — the emails are real.

---

## What to do next

- **Run more campaigns** — try different ICPs, different fleet types (Content, Social)
- **Add a second company** — see [PLAYBOOK.md](PLAYBOOK.md#adding-companies)
- **Customize prompts** — edit `company/ceo/system_prompt.md` to match your voice
- **Add a custom fleet** — see [ADDING_FLEETS.md](ADDING_FLEETS.md)
- **Deploy 24/7** — see [RUNNING_24_7.md](RUNNING_24_7.md)

---

## What can go wrong

| Symptom | Fix |
|---|---|
| Bot says "Something went wrong" | Check the bot's terminal for the actual error |
| `Could not resolve authentication method` | `ANTHROPIC_API_KEY` empty in env. We pass `override=True` to `load_dotenv` to fix this. |
| Worker returns nonsense JSON | DeepSeek occasionally produces invalid JSON. The qualifier worker auto-retries. |
| Emails don't send | Composio not configured, or Gmail account not connected. Check `composio list` in CLI. |
| Bot disconnects, reconnects | Normal Socket Mode behavior. The bolt app reconnects automatically. |
| Slack rate limits the bot | You're sending too many messages. Add delays in the bot's response logic. |

For deeper debugging, see [INSPECTING.md](INSPECTING.md).
