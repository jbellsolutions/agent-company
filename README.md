# agent-company

> **Drop-in autonomous AI company.** One Slack DM → a hierarchy of agents executes the work. Built for founders who refuse to spend their best hours on prospecting, outreach, and content production.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Made with Anthropic](https://img.shields.io/badge/AI-Claude%20Opus%204.7-purple.svg)](https://www.anthropic.com/)

---

## The 30-Second Pitch

You don't need another AI tool. You need an **AI team**.

This repo is a complete 4-tier agent company you can drop into any project:

- **You** talk to ONE agent (in Slack).
- That agent **routes** to the right CEO of the right business.
- The CEO **delegates** to team leads (SDR, Content, Social).
- Team leads **dispatch** workers that do the actual work — prospecting, writing, sending emails, posting to LinkedIn.
- Results flow back up. You see them in Slack. The whole company runs 24/7.

No dashboards to operate. No 17 SaaS subscriptions. No "AI tool" that turns out to be a glorified prompt template.

```
You DM the bot: "Launch SDR campaign for fintech 50-200 employees"
                            ↓
        Meta-Orchestrator routes to "Using AI to Scale" CEO
                            ↓
                      CEO calls SDR Lead
                            ↓
        Prospector finds 50 leads in Apollo (DeepSeek, ~$0.02)
                            ↓
        Qualifier scores them, filters to top 20 (DeepSeek, ~$0.01)
                            ↓
        Outbound writes 20 personalized emails (DeepSeek, ~$0.05)
                            ↓
                Sends via Gmail (Composio integration)
                            ↓
            CEO synthesizes results, reports back to you in Slack:
   "20 emails sent. 3 replies flagged as hot. Total cost: $0.31"
```

That's it. That's the product.

---

## Why This Exists

Every founder I know is buried in operational work that AI should already be handling:

- **Prospecting**: hours combing LinkedIn and Apollo for the right leads.
- **Outreach**: writing personalized emails one at a time.
- **Content**: trying to publish enough to stay top-of-mind.
- **Social**: monitoring mentions, engaging, replying.

Solo AI tools fix one of these in isolation. They don't talk to each other. They cost ~$200/mo each. None of them remember what the others did.

This repo flips the model: **one team, one interface, one source of truth**, with the right LLM for each job. The result is closer to hiring than buying software.

---

## The 4-Tier Hierarchy

```
                    ┌─────────────────┐
                    │   YOU (Slack)   │
                    └────────┬────────┘
                             ↓
              ┌──────────────────────────────┐
              │  Meta-Orchestrator (Opus 4.7)│  ← your only interface
              │  • knows ALL companies       │
              │  • routes, never executes    │
              └──────────────┬───────────────┘
                             ↓
        ┌────────────────────┼────────────────────┐
        ↓                    ↓                    ↓
  ┌──────────┐         ┌──────────┐         ┌──────────┐
  │ CEO: Co A│         │ CEO: Co B│         │ CEO: Co C│  ← per-company context
  │ Opus 4.7 │         │ Sonnet   │         │ Sonnet   │
  └─────┬────┘         └──────────┘         └──────────┘
        ↓
  ┌─────────────┬──────────────┬──────────────┐
  ↓             ↓              ↓              ↓
┌──────┐    ┌──────┐       ┌──────┐
│ SDR  │    │Content│      │Social│   ← Sonnet 4.6 leads
│ Lead │    │ Lead │       │ Lead │
└──┬───┘    └──┬───┘       └──┬───┘
   ↓           ↓               ↓
┌─────────┐ ┌─────────┐  ┌─────────┐
│Prospect │ │ Writer  │  │ Poster  │  ← DeepSeek workers
│Qualifier│ │ Poster  │  │         │     (~10x cheaper)
│Outbound │ │         │  │         │
└─────────┘ └─────────┘  └─────────┘
     ↓           ↓             ↓
  Composio: Apollo, Gmail, LinkedIn, Notion, Twitter
```

### Why this shape works

| Tier | Model | Cost / 1M tok | Job |
|---|---|---|---|
| Meta-Orchestrator | Claude Opus 4.7 (1M ctx) | ~$15 | Sees everything, routes everything |
| CEO | Opus 4.7 or Sonnet 4.6 | $15 / $3 | Holds full company context, breaks down work |
| Lead | Claude Sonnet 4.6 | ~$3 | Coordinates the team, plans tasks |
| Worker | DeepSeek V4 Flash (OpenRouter) | ~$0.30 | Does the actual high-volume work |

**Workers do 90% of the volume at 50× lower per-token cost than Opus.** A 50-lead SDR campaign costs cents, not dollars. That's how you make AI agents economically defensible.

---

## Storyboard: A Real Run

### Frame 1 — The DM
```
You → @AgentCompany
    "Launch an SDR campaign targeting fintech companies
     with 50-200 employees. Top 20 leads, personalized intros."
```

### Frame 2 — The Meta-Orchestrator decides
```
Meta-Orchestrator (Opus 4.7) thinks:
  → This belongs to "Using AI to Scale" (your primary business)
  → Delegating to its CEO
```

### Frame 3 — CEO breaks it down
```
CEO (Opus 4.7) writes the plan:

  [TASK:sdr_lead] Find 50 fintech companies, 50-200 employees,
                  return name + LinkedIn + headcount + primary contact
  [TASK:sdr_lead] Qualify all 50 by ICP fit; filter to top 20 (score ≥ 50)
  [TASK:sdr_lead] Write & send personalized intro emails to top 20
```

### Frame 4 — SDR Lead dispatches workers
```
SDR Lead (Sonnet 4.6):

  [WORKER:prospector] fintech, 50-200 employees, last 12 months funding signal
  [WORKER:qualifier]  <50 leads JSON> — score & filter
  [WORKER:outbound]   <top 20 leads> — write personalized email per lead, send via Gmail
```

### Frame 5 — Workers execute
```
Prospector  (DeepSeek)             → Apollo search → 50 leads (cost: $0.02)
Qualifier   (DeepSeek)             → ICP scoring  → top 20    (cost: $0.01)
Outbound    (DeepSeek + Composio)  → Gmail send   → 20 emails (cost: $0.05)
                                                     + tools:  $0.00
                                                     ─────────────
                                              Worker tier total: $0.08
```

### Frame 6 — CEO synthesizes
```
CEO (Opus 4.7) → "20 emails sent. 3 high-fit leads flagged for personal
                  follow-up. 1 reply already in Gmail. Total cost: $0.31."
```

### Frame 7 — You see it in Slack
```
@AgentCompany → DM
  ✅ SDR Campaign Complete
  • 50 leads prospected
  • 20 qualified (avg ICP score: 67)
  • 20 personalized emails sent
  • 1 reply received (flagged for your review)
  • Total cost: $0.31

  Want me to scale to 100 next? Or pivot to a different segment?
```

That's a campaign that previously took half a day. Now it's a Slack DM and pocket change.

---

## Quick Start (5 Minutes)

### 1. Clone & install
```bash
git clone https://github.com/jbellsolutions/agent-company
cd agent-company
cp .env.example .env
```

### 2. Add your API keys to `.env`
You need 4 keys (5 minutes total):

| Key | Where to get it | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/settings/keys) | Yes |
| `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) | Yes |
| `SLACK_BOT_TOKEN` + `SLACK_SIGNING_SECRET` + `SLACK_APP_TOKEN` | See [docs/SLACK_SETUP.md](docs/SLACK_SETUP.md) | Yes |
| `COMPOSIO_API_KEY` | [app.composio.dev/developers](https://app.composio.dev/developers) | No (dry-run mode without it) |

### 3. Run setup
```bash
./setup.sh
```
This installs Python deps and creates the local SQLite database (`agentcompany.db`). **No Docker, no Postgres daemon.**

### 4. Start the bot
```bash
python interfaces/slack_bot.py
```
You'll see:
```
INFO:__main__:Starting Slack bot in Socket Mode...
INFO:slack_bolt.App:⚡️ Bolt app is running!
```

### 5. DM your bot
Open Slack → find your bot in DMs → message it:

```
Create a company called Using AI to Scale.
We help founders build AI-powered sales teams targeting B2B SaaS.
ICP: 50-500 person companies, post-Series A.
```

Then:
```
Launch an SDR campaign for fintech companies, 50-200 employees.
Top 20 leads, personalized intros.
```

The bot routes the request, the CEO breaks it down, workers execute, results come back.

---

## Adding a New Company

DM the bot:
```
Create a new company called Acme Corp.
They sell B2B SaaS to mid-market retail. ICP: 200-2000 employee
retailers in North America. Tone: consultative, ROI-focused.
```

The Meta-Orchestrator creates the company row, registers a CEO agent, and it's live. From now on, any request mentioning Acme Corp routes to that CEO.

You can run **multiple companies in parallel** from one repo. The orchestrator keeps them isolated and routes correctly.

---

## Adding a New Fleet

A "fleet" is a Lead + its workers. The repo ships with three:

- **SDR Fleet** — `prospector`, `qualifier`, `outbound`
- **Content Fleet** — `writer`, `poster`
- **Social Fleet** — `poster`

To add your own (e.g., a Customer Success fleet):

1. Add a new lead in `company/leads/cs_lead.py` (subclass `BaseLead`).
2. Add workers in `company/workers/` (subclass `BaseWorker`).
3. Register the lead in `company/ceo/agent.py` `_dispatch_to_lead` map.
4. Update Composio app mapping in `tools/composio_setup.py`.

The hierarchy handles the rest. New fleet appears to the CEO as just another team to call with `[TASK:cs_lead]`.

---

## What You Get

- ✅ **Multi-agent hierarchy** with real inter-agent communication
- ✅ **Cost-optimized model routing** (Opus where it matters, DeepSeek for volume)
- ✅ **1000+ SaaS integrations** via Composio (Apollo, Gmail, LinkedIn, HubSpot, Notion, Twitter, Slack, ...)
- ✅ **Persistent memory** across sessions (SQLite locally, Postgres on Railway)
- ✅ **Multi-company support** — run your own business + your clients' from one bot
- ✅ **Pre-built fleets** — SDR, Content, Social
- ✅ **Slack-native** — Socket Mode means no public URL, no port forwarding
- ✅ **Drop-in deployment** — `./setup.sh` and you're running

---

## Repo Structure

```
agent-company/
├── orchestrator/
│   ├── agent.py              ← Meta-Orchestrator (Opus 4.7) — sovereign
│   └── system_prompt.md
├── company/
│   ├── ceo/
│   │   ├── agent.py          ← Per-company CEO (Opus or Sonnet)
│   │   ├── memory.py         ← SQLite persistence layer
│   │   └── system_prompt.md
│   ├── leads/                ← Sonnet 4.6 team leads
│   │   ├── base_lead.py
│   │   ├── sdr_lead.py
│   │   ├── content_lead.py
│   │   └── social_lead.py
│   └── workers/              ← DeepSeek workers (via OpenRouter)
│       ├── base_worker.py
│       ├── prospector.py
│       ├── qualifier.py
│       ├── outbound.py
│       ├── writer.py
│       └── poster.py
├── tools/
│   └── composio_setup.py     ← Role → Composio app mapping
├── fleets/
│   ├── sdr_fleet.py          ← Pre-built fleet activation prompts
│   ├── content_fleet.py
│   └── social_fleet.py
├── interfaces/
│   ├── slack_bot.py          ← Slack Bolt + Socket Mode
│   └── cli.py                ← Local CLI for testing
├── memory/
│   └── schema.sql            ← SQLite schema
├── infra/
│   ├── Dockerfile            ← For Railway 24/7 deploy
│   └── railway.toml
├── docs/
│   ├── SLACK_SETUP.md        ← Step-by-step Slack app creation
│   ├── ARCHITECTURE.md       ← Deeper technical doc
│   └── ADDING_FLEETS.md      ← How to extend with new teams
├── setup.sh                  ← One-command setup
├── requirements.txt
├── .env.example
└── README.md (you are here)
```

---

## Cost Math

For a representative SDR week (5 campaigns × 50 leads each = 250 leads, 100 emails):

| Tier | Tokens (est.) | Cost |
|---|---|---|
| Meta-Orchestrator (Opus) | 50K | $0.75 |
| CEO (Opus) | 200K | $3.00 |
| SDR Lead (Sonnet) | 500K | $1.50 |
| Workers (DeepSeek) | 5M | $1.50 |
| **Total / week** | — | **~$6.75** |

Versus hiring an SDR contractor at ~$2,000/mo for the same volume.

The unit economics work because the cheap model does the bulk of the volume, and the expensive model only does the work that requires judgment.

---

## Deployment Options

### Local (default)
```bash
./setup.sh && python interfaces/slack_bot.py
```
SQLite file. Stays alive as long as your terminal does. For 24/7, use `nohup`, `screen`, `tmux`, or a Mac launchd plist.

### Railway (24/7 cloud)
```bash
railway up
```
Uses `infra/Dockerfile`. Persist `agentcompany.db` via Railway volume, OR swap to a hosted Postgres URL via Neon's free tier (the only file that changes is `company/ceo/memory.py`).

### DigitalOcean / VPS
Standard Python deploy. The repo has no Docker requirement; clone, pip install, run with systemd.

---

## Documentation

- **[Slack App Setup](docs/SLACK_SETUP.md)** — step-by-step app creation, scopes, tokens
- **[Architecture Deep Dive](docs/ARCHITECTURE.md)** — how the tiers communicate
- **[Adding New Fleets](docs/ADDING_FLEETS.md)** — extending with custom teams
- **[Composio Integration](docs/COMPOSIO.md)** — wiring tools to workers

---

## Roadmap

- [x] Meta-Orchestrator + CEO + Leads + Workers
- [x] SDR fleet (prospector, qualifier, outbound)
- [x] Content fleet (writer, poster)
- [x] Social fleet (poster)
- [x] Composio tool injection
- [x] Slack interface (Socket Mode)
- [x] SQLite local storage
- [ ] Customer Success fleet (renewals, upsells, NPS triage)
- [ ] Recruiting fleet (sourcing, screening, outreach)
- [ ] Memory compression at 80% context (auto-summary roll-ups)
- [ ] Web dashboard (read-only — for those who want a UI)
- [ ] Multi-tenant SaaS mode

---

## License

MIT

---

## Built By

[Justin Bellware](https://github.com/jbellsolutions) — founder of [Using AI to Scale](https://usingaitoscale.com)

If you ship something interesting on top of this, [@-mention me](https://twitter.com/jbellsolutions) — I want to see what you build.
