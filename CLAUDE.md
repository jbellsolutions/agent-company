# Agent Company — Claude Code Instructions

## Architecture

4-tier hierarchy: Meta-Orchestrator → CEO → Team Lead → Worker

- **Meta-Orchestrator** (`orchestrator/agent.py`): Claude Opus 4.7. Sovereign. Routes to CEOs.
- **CEO** (`company/ceo/agent.py`): Claude Opus 4.7 or Sonnet 4.6. Per-company context.
- **Leads** (`company/leads/*.py`): Claude Sonnet 4.6. SDR, Content, Social.
- **Workers** (`company/workers/*.py`): DeepSeek V4 Flash via OpenRouter. Execute tasks.

## Running Locally

```bash
cp .env.example .env             # fill in keys first
./setup.sh                       # pip install + create SQLite DB
python interfaces/slack_bot.py   # Slack bot via Socket Mode
# or:
python interfaces/cli.py --interactive
```

No Docker / no Postgres daemon. Local DB is `agentcompany.db` (SQLite, stdlib).

## Key Files

- `orchestrator/agent.py` — Meta-Orchestrator (modify routing logic here)
- `company/ceo/system_prompt.md` — CEO behavior (edit to tune company voice)
- `company/workers/base_worker.py` — Worker base class (OpenRouter + DeepSeek config)
- `tools/composio_setup.py` — Tool injection per worker role
- `memory/schema.sql` — Postgres schema

## Adding a New Worker

1. Inherit from `BaseWorker` in `company/workers/base_worker.py`
2. Override `system_prompt` and `tools` list
3. Register in the appropriate lead (`company/leads/sdr_lead.py` etc.)

## Environment

All config via `.env`. Never hardcode keys. `DATABASE_URL` is auto-set by Railway on deploy.

## Model IDs

```python
OPUS = "claude-opus-4-7"
SONNET = "claude-sonnet-4-6"
DEEPSEEK = "deepseek/deepseek-v4-flash"  # via OpenRouter
```
