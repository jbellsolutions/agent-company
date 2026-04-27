# agent-company

Drop this repo into any project and stand up a complete multi-agent company in one command.

## What This Is

A 4-tier agent hierarchy that runs 24/7:

```
[You via Slack]
      ↓
[Meta-Orchestrator]   ← your ONLY interface; sovereign over all companies
      ↓
[CEO per Company]     ← full company context, routes to teams
      ↓
[Team Leads]          ← coordinate workers, break down tasks
      ↓
[Workers]             ← execute: prospecting, writing, outbound, posting
```

You never log into a dashboard. You DM the Slack bot. It delegates everything.

## LLM Routing (Cost-Optimized)

| Role | Model | Cost |
|---|---|---|
| Meta-Orchestrator | Claude Opus 4.7 (1M ctx) | ~$15/M tokens |
| Company CEOs | Claude Opus 4.7 or Sonnet 4.6 | varies |
| Team Leads | Claude Sonnet 4.6 | ~$3/M tokens |
| Workers | DeepSeek V4 Flash (via OpenRouter) | ~$0.30/M tokens |

Workers do 90% of the volume at ~10x lower cost.

## Quick Start

```bash
git clone https://github.com/jbellsolutions/agent-company
cd agent-company
cp .env.example .env
# Fill in your API keys in .env
./setup.sh                          # installs pip deps + creates SQLite DB
python interfaces/slack_bot.py      # connects to Slack via Socket Mode
```

Then DM your Slack bot: `set up the SDR fleet for fintech companies 50-200 employees`

**No Docker required.** Local DB is a single SQLite file (`agentcompany.db`).

## Example Flow

```
You → Slack: "Launch SDR campaign for fintech 50-200 employees"

Meta-Orchestrator → routes to Using AI to Scale CEO
CEO (Opus) → dispatches to SDR Lead
SDR Lead (Sonnet) → coordinates:
  Prospector (DeepSeek) → Apollo search → 50 leads
  Qualifier (DeepSeek)  → ICP scoring   → top 20
  Outbound (DeepSeek)   → Gmail send    → 20 personalized emails

CEO → reports back to Slack: "20 emails sent. 3 replies flagged as hot."
```

## Required API Keys

| Key | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `OPENROUTER_API_KEY` | openrouter.ai |
| `COMPOSIO_API_KEY` | composio.dev |
| `SLACK_BOT_TOKEN` | api.slack.com/apps |
| `DB_PATH` | Local file path (defaults to `./agentcompany.db`) |

## Fleets Available

- **SDR Fleet** — prospecting, qualification, personalized outbound (ship this first)
- **Content Fleet** — research, writing, distribution
- **Social Fleet** — monitoring, engagement, posting

## Deployment

**Local (default):** SQLite file. Just run `python interfaces/slack_bot.py` after `./setup.sh`.

**Railway (24/7):** push the repo, Railway uses `infra/Dockerfile`. Mount a volume so the SQLite file persists between deploys, or swap `DB_PATH` for a hosted Postgres URL (Neon free tier works) and update `memory.py`'s connection layer.

```bash
railway up   # one-shot deploy from this repo
```

## Repo Structure

```
agent-company/
├── company/
│   ├── ceo/          ← Opus 4.7 CEO per company
│   ├── leads/        ← Sonnet 4.6 team leads
│   └── workers/      ← DeepSeek workers (prospector, writer, outbound, poster)
├── tools/            ← Composio integrations
├── fleets/           ← Pre-built fleet configs (SDR, Content, Social)
├── interfaces/       ← Slack bot + CLI
├── memory/           ← Postgres schema
└── infra/            ← Railway + Docker configs
```

## Adding a New Company

DM the Meta-Orchestrator:
```
"Create a new company called Acme Corp. They sell B2B SaaS to mid-market retail."
```

The orchestrator creates the company context, spins up a CEO agent, and it's ready.
