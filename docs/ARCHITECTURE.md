# Architecture

A walkthrough of how the 4 tiers actually communicate.

---

## The Tiers

```
[ User (Slack DM) ]
        ↓ user message
[ Meta-Orchestrator (Opus 4.7) ]
        ↓ [DELEGATE:company_id:instruction]
[ CEO (Opus 4.7 or Sonnet 4.6) ]
        ↓ [TASK:lead_name] description
[ Team Lead (Sonnet 4.6) ]
        ↓ [WORKER:worker_name] sub-task
[ Worker (DeepSeek V4 Flash via OpenRouter) ]
        ↓ tool calls (Composio: Apollo, Gmail, ...)
[ External APIs ]
```

Each tier writes its decisions in plain text (not function calls), with a structured marker like `[TASK:sdr_lead]` or `[WORKER:prospector]`. The next tier parses those markers and dispatches.

This is **deliberate**: it makes the whole pipeline debuggable in plain text. You can read every agent's reasoning by tailing the conversations table.

---

## Why each tier exists

### Meta-Orchestrator (Opus 4.7, 1M context)

**Job**: Be your single interface. Know which company any request belongs to. Never execute work.

**Why Opus + 1M context**: It has to remember all your companies, all active campaigns, all preferences across sessions. The 1M token context window means it can hold months of state without summarizing.

**Why never executes**: If the orchestrator does work directly, it accumulates context faster and burns money on the most expensive model. Strict separation keeps it lean.

### CEO (Opus 4.7 or Sonnet 4.6 per company)

**Job**: Hold a single company's full context (ICP, brand voice, current quarter goals, what's in flight). Translate business directives into team-level tasks.

**Why per-company**: Different companies have different voices, ICPs, and constraints. Putting them in one agent means context bleed and confused outputs. Each CEO is a fresh, focused conversation.

**Why Opus for primary, Sonnet for secondary**: Your main business deserves the smartest model. Client/project companies can use Sonnet for ~5× cost reduction with marginal quality loss.

### Team Leads (Sonnet 4.6)

**Job**: Coordinate a team of workers. Break a CEO directive into worker-sized tasks.

**Why Sonnet**: Coordination doesn't need 1M context — it needs reliable structured output and reasoning. Sonnet 4.6 is the sweet spot.

### Workers (DeepSeek V4 Flash via OpenRouter)

**Job**: Execute one specific task. Make Apollo searches, write emails, post to LinkedIn.

**Why DeepSeek**: ~50× cheaper per token than Opus. Workers do high-volume, narrow-scope tasks where DeepSeek's quality is comparable to Sonnet for ~10% of the cost.

**Why via OpenRouter**: One API key for DeepSeek + 100+ models. If DeepSeek has downtime, swap to Llama or Qwen by changing one string. No vendor lock-in.

---

## Data Flow Example

User message: `"Launch SDR campaign for fintech companies 50-200 employees"`

### 1. Meta-Orchestrator
```python
# orchestrator/agent.py — chat()
response = client.messages.create(
    model="claude-opus-4-7",
    system=system_prompt,  # includes list of all companies + active tasks
    messages=[{"role": "user", "content": user_message}],
)
# Output contains: [DELEGATE:1:Launch SDR campaign for fintech 50-200]
```

The system prompt lists all companies. Opus picks the right one and emits a delegation marker.

### 2. CEO
```python
# company/ceo/agent.py — run()
response = client.messages.create(
    model="claude-opus-4-7",
    system=ceo_system_prompt,  # includes recent history + active tasks
    messages=[{"role": "user", "content": directive}],
)
# Output contains: [TASK:sdr_lead] Find 50 fintech companies...
#                  [TASK:sdr_lead] Qualify to top 20...
#                  [TASK:sdr_lead] Send personalized emails...
```

Each `[TASK:...]` block is dispatched serially to its lead. Tasks are persisted to the `tasks` table.

### 3. Team Lead
```python
# company/leads/base_lead.py — run()
response = client.messages.create(
    model="claude-sonnet-4-6",
    system=lead_system_prompt,
    messages=[{"role": "user", "content": task}],
)
# Output contains: [WORKER:prospector] fintech, 50-200 employees...
#                  [WORKER:qualifier] <leads> — score
#                  [WORKER:outbound] <top 20> — send emails
```

### 4. Worker
```python
# company/workers/base_worker.py — _call()
response = OpenAI(base_url="https://openrouter.ai/api/v1").chat.completions.create(
    model="deepseek/deepseek-v4-flash",
    messages=[
        {"role": "system", "content": worker_system_prompt},
        {"role": "user", "content": worker_task},
    ],
    tools=composio_tools,  # if any
)
```

Workers may use Composio tools (Apollo, Gmail, LinkedIn, etc.) to call real APIs.

### 5. Synthesis bubbles back up
- Workers return text → Lead synthesizes into a "team result"
- Leads return summaries → CEO synthesizes into a "company report"
- CEO returns report → Meta-Orchestrator phrases it for Slack
- You see the final message in Slack

Every step writes to the `conversations` table. You can replay any campaign from the DB.

---

## Persistence Model

**SQLite locally**, schema in `memory/schema.sql`:

| Table | What it stores |
|---|---|
| `companies` | Each company you've created (name + context) |
| `conversations` | Every message in every tier (orchestrator, ceo, lead, worker) |
| `tasks` | Each task created by a CEO or lead — status, result, parent |
| `context_summaries` | Compressed history when context windows fill |

The `tasks` table is the **shared task queue**. Multiple agents can read it to understand what's in flight without hitting the LLM.

---

## State Across Restarts

When the bot restarts:

1. SQLite file is unchanged → all companies, tasks, history persist.
2. Meta-Orchestrator's system prompt is rebuilt from `list_companies()` + `get_active_tasks()` for each company.
3. Each CEO's system prompt is rebuilt from `get_recent_history(limit=30)`.

So context survives restarts without needing to re-explain anything.

---

## Why Not LangGraph / CrewAI / AutoGen?

This repo deliberately avoids those frameworks. Reasons:

- **Plain text protocols** are easier to debug than callbacks or graphs.
- **No magic** — every dispatch is a regex match in `base_lead.py`. You can read it in 5 minutes.
- **Cost control** — frameworks tend to inject extra LLM calls for "reflection" or "planning" that you can't easily kill.
- **Vendor neutrality** — Anthropic for the smart agents, OpenRouter for the cheap ones. No framework dependencies that lock you to a provider.

Frameworks are great for prototyping. This repo is built for production simplicity.

---

## Adding Observability

Right now, every conversation is in SQLite. To make it queryable:

```bash
sqlite3 agentcompany.db
> SELECT role, agent_name, content FROM conversations
  WHERE company_id = 1 ORDER BY id DESC LIMIT 20;
```

Or wire up:
- **Langfuse** — drop-in tracing (set `LANGFUSE_PUBLIC_KEY` env var, instrument `_call` methods)
- **OpenTelemetry** — Anthropic's SDK supports OTEL exports natively
- **A custom dashboard** — read from `conversations` and `tasks` tables; build whatever UI you want

The architecture leaves these as opt-in. Out of the box, the Slack messages + SQLite are enough.
