# Operator Playbook

How to actually use this thing day-to-day.

This is a reference of common workflows. Keep it open in a tab, copy the patterns, adapt to your situation.

---

## How to talk to the bot

There are no slash commands, no buttons, no special syntax. You just say what you want in plain English. The Meta-Orchestrator interprets and routes.

Three rules of thumb:

1. **Be specific about which company.** If you have multiple, name it. ("Run an SDR campaign for Using AI to Scale" vs "for Acme Corp")
2. **Be specific about the ask.** "Find some leads" → 200 random results. "Find 20 fintech CFOs at companies 50-200 employees that raised Series A in last 6 months" → exactly what you wanted.
3. **Ask for confirmation when stakes are high.** "Draft these emails but don't send" gives you a review step before money goes out the door.

---

## SDR Workflows

### Find + qualify leads (no outreach yet)
```
Find 50 fintech companies in NYC, 100-300 employees,
that raised Series A or B in the last 12 months.
Qualify them by ICP fit. Show me the top 20 only — don't reach out.
```

### Personalized cold outreach
```
For Using AI to Scale: launch outbound to 20 leads.
Target: VP Sales or Head of Growth at B2B SaaS companies,
50-200 employees, Series A funded.
Reference something specific in each email. Subject line should
be a question, not a statement.
Send via Gmail.
```

### Follow-up sequences
```
For everyone who didn't reply to the SDR campaign last week,
send a follow-up. Reference the original email. Offer a single
piece of value (no second pitch). Send via Gmail.
```

### Replies triage
```
Pull all replies to my SDR campaigns from this week.
Categorize: positive (book the meeting), neutral (nurture),
negative (close the loop, polite goodbye), unsubscribe.
Draft replies for each. Don't send the negative or
unsubscribe categories — flag for me.
```

### LinkedIn DMs (instead of email)
```
Same target as the last SDR campaign, but reach out via LinkedIn DMs
instead of email. Connection request first, then a follow-up after they accept.
```

---

## Content Workflows

### LinkedIn post production
```
Write 3 LinkedIn posts for Using AI to Scale this week.
Theme: how AI agents change SDR economics.
One should be a contrarian take, one a personal story,
one a tactical how-to. 200 words each.
Don't post yet — show me first.
```

### Long-form blog post
```
Write a 1200-word blog post for Using AI to Scale on
"Why outbound SDRs cost $90K/year and AI agents do the same
work for $400/month." Include 3 data points, one customer
quote (you can mark it [PLACEHOLDER] for me to fill in),
and end with a CTA to book a strategy call.
```

### Cold email sequence templates
```
Build a 5-email sequence for B2B SaaS founders interested
in AI sales automation. Each email under 100 words.
Sequence: intro, social proof, objection handling, case study,
breakup. Save the templates to Notion.
```

### Newsletter
```
Pull the top 5 things I posted on LinkedIn this week.
Synthesize into a newsletter (700 words) with a single theme.
Add my voice — direct, opinionated, ROI-focused.
```

---

## Social Workflows

### Daily posts
```
Post today's LinkedIn update for Using AI to Scale.
Topic: [pick the most relevant thing from the news / my recent activity]
Format: hook → insight → CTA. 200 words.
Schedule for 8:30 AM ET.
```

### Engagement triage
```
Pull all comments and DMs on my LinkedIn posts from the last 48 hours.
Categorize: meaningful conversation, generic engagement, spam.
Draft thoughtful replies for the meaningful ones — don't post yet.
```

### Mention monitoring
```
Search for mentions of "AI sales automation" or "agent companies"
on LinkedIn and Twitter from the last 24 hours.
Flag the ones I should engage with (high engagement,
relevant to my ICP). Draft a comment for each.
```

---

## Multi-Company Workflows

### Adding a new company
```
Create a new company called Acme Corp.
They sell B2B SaaS to mid-market retail (200-2000 employees, NA).
Founder voice: consultative, slightly nerdy, ROI-focused but not pushy.
Primary outbound channel: LinkedIn. They don't use cold email.
```

The orchestrator persists this in SQLite and registers a new CEO. From now on, any request mentioning Acme Corp routes there.

### Cross-company comparison
```
For both Using AI to Scale and Acme Corp,
show me last week's SDR results: leads sent, replies, hot leads.
Which campaign performed better and why?
```

The Meta-Orchestrator sees both companies and synthesizes — this is the cross-portfolio routing power.

### Pause / resume a company
```
Pause all outbound for Acme Corp until further notice.
We're in a contract negotiation and don't want to muddy the waters.
```

The orchestrator marks the company as paused in memory; CEO won't dispatch outbound tasks until you say resume.

### Move a campaign between companies
```
The fintech SDR campaign you ran for Using AI to Scale —
adapt it for Acme Corp's retail ICP. Different industry, but
same campaign mechanics. Show me the adapted version before sending.
```

---

## Approval & Safety Patterns

### Always-confirm-before-sending
Edit `company/leads/sdr_lead.py` system prompt → add:
```
ALWAYS draft and show emails before sending unless the user explicitly
says "send it" or "ship". Default to draft mode.
```

### Daily send caps
In your `.env`:
```
SDR_DAILY_SEND_CAP=20
```
Then in `sdr_lead.py` system prompt: `Never exceed SDR_DAILY_SEND_CAP per company per day.`

### Founder approval for high-value leads
```
For any lead with score ≥ 85 OR company with ≥ 500 employees,
flag for my personal review before sending. I'll handle these myself.
```

The CEO will set those aside; smaller leads still get the auto-treatment.

---

## Memory & Context Tips

### Remind the bot of long-term context
The CEO's system prompt is rebuilt from `companies.context` each turn. To update:
```
For Using AI to Scale, update the company context:
We just pivoted ICP to focus on Series B+ companies (was Series A).
Update everything going forward.
```

The orchestrator updates the row; future CEO conversations include the new context.

### Compress old conversations
After ~50 turns, the CEO's history starts taking real context. Periodically:
```
For Using AI to Scale, summarize what we've done in the last
30 days into a single paragraph. Save as the latest context summary.
```

This stores a compressed summary in `context_summaries`. The CEO loads the latest one + recent 30 messages, freeing context.

---

## Cost Monitoring

### Quick check
```bash
sqlite3 agentcompany.db "
  SELECT
    DATE(created_at) as day,
    COUNT(*) as msgs,
    SUM(LENGTH(content)) / 4 as approx_tokens
  FROM conversations
  WHERE created_at >= DATE('now', '-7 days')
  GROUP BY day
  ORDER BY day;
"
```

This gives you message volume per day. Multiply token estimates by the model rates in [README.md](../README.md#cost-math).

### Spend alerts
- Anthropic console: console.anthropic.com → Usage → set alert at $X/day
- OpenRouter dashboard: openrouter.ai → set spend cap

If you blow past your alert, the bot keeps running but you'll get an email. For hard caps, set them on each provider's dashboard.

---

## Debugging an unexpected response

When the bot does something weird, the chain is:

1. **Read the bot's stdout** — the actual exception is there
2. **Check `conversations` table** — see exactly what each agent said
3. **Check `tasks` table** — see which tasks fired and which failed
4. **Re-run the same prompt** — sometimes it's a cold-start hiccup

```bash
# What did the orchestrator decide to do?
sqlite3 agentcompany.db "
  SELECT id, role, agent_name, content
  FROM conversations
  ORDER BY id DESC LIMIT 5;
"

# What tasks fired?
sqlite3 agentcompany.db "
  SELECT id, status, assigned_to, substr(description, 1, 60), substr(result, 1, 80)
  FROM tasks ORDER BY id DESC LIMIT 10;
"
```

See [INSPECTING.md](INSPECTING.md) for more debugging recipes.

---

## What NOT to do

- **Don't send to every prompt with `send it` first** — the bot will. It's literal. Always run a test campaign in dry-run before going live.
- **Don't share `.env`** — it's gitignored, but be careful with screenshots.
- **Don't run two `slack_bot.py` instances** — they'll fight over Socket Mode connections. Use one.
- **Don't put your `agentcompany.db` in iCloud Drive** — SQLite locking gets weird. Keep it in `~/Desktop/agent-company/` or move outside iCloud sync.

---

## Cheat Sheet

| Goal | Say to the bot |
|---|---|
| New company | `Create a company called X. They do Y. ICP is Z.` |
| Find leads | `Find 50 [industry] companies, [size], [signal]. Don't reach out yet.` |
| Send outbound | `Send personalized intros to those 20. Subject = question. Via Gmail.` |
| Draft content | `Write 3 LinkedIn posts on [topic]. 200 words each. Don't post.` |
| Post content | `Post the third one I just approved. Schedule for tomorrow 8:30 AM ET.` |
| Triage replies | `Pull replies from this week. Categorize. Draft responses.` |
| Cross-company | `Compare last week's SDR results across all companies.` |
| Pause work | `Pause all outbound for [company] until I say resume.` |
| Status | `What's running right now across all companies?` |
| Daily report | `Summarize what got done today.` |
