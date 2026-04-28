# Inspecting the Bot

How to see exactly what the agents are doing — and debug when things go sideways.

---

## The DB is the source of truth

The `agentcompany.db` SQLite file has 4 tables:

| Table | Holds |
|---|---|
| `companies` | One row per company you've created |
| `conversations` | Every message, from every agent, in every tier |
| `tasks` | Tasks the CEO and Leads created — status, assignment, result |
| `context_summaries` | Compressed history snapshots |

Every action the bot takes writes here. If something looks wrong in Slack, the answer is in the DB.

---

## Common queries

### What did the bot just do?
```bash
sqlite3 agentcompany.db "
  SELECT
    datetime(created_at, 'localtime') as ts,
    role,
    agent_name,
    substr(content, 1, 100) as snippet
  FROM conversations
  ORDER BY id DESC LIMIT 20;
"
```

### Full transcript for a specific company
```bash
sqlite3 agentcompany.db "
  SELECT
    datetime(c.created_at, 'localtime') as ts,
    c.role,
    c.agent_name,
    c.content
  FROM conversations c
  JOIN companies co ON c.company_id = co.id
  WHERE co.name = 'Using AI to Scale'
  ORDER BY c.id;
" | less
```

### What tasks ran today?
```bash
sqlite3 agentcompany.db "
  SELECT
    id,
    datetime(created_at, 'localtime') as started,
    status,
    assigned_to,
    substr(description, 1, 60) as task,
    substr(result, 1, 80) as result_snippet
  FROM tasks
  WHERE created_at >= DATE('now')
  ORDER BY id DESC;
"
```

### Tasks that failed
```bash
sqlite3 agentcompany.db "
  SELECT id, assigned_to, description, result
  FROM tasks
  WHERE status = 'failed'
  ORDER BY id DESC LIMIT 10;
"
```

### Stuck tasks (in_progress for > 5 min)
```bash
sqlite3 agentcompany.db "
  SELECT id, assigned_to, description,
         (julianday('now') - julianday(updated_at)) * 86400 as seconds_stuck
  FROM tasks
  WHERE status = 'in_progress'
  ORDER BY seconds_stuck DESC;
"
```

If anything's stuck, manually mark it failed:
```bash
sqlite3 agentcompany.db "UPDATE tasks SET status='failed' WHERE id=42;"
```

---

## Watching the bot live

In one terminal, follow the bot's stdout:
```bash
tail -f /private/tmp/.../tasks/<task-id>.output
```

(The path is in the message that confirmed the background process started.)

In another terminal, watch new conversations as they land:
```bash
watch -n 2 "sqlite3 agentcompany.db 'SELECT id, role, agent_name, substr(content, 1, 80) FROM conversations ORDER BY id DESC LIMIT 5;'"
```

You'll see new rows appear in real time as the bot processes a request through all 4 tiers.

---

## Reading the agent reasoning chain

Every layer of the hierarchy logs to the same `conversations` table. To see how a single user message propagated:

```bash
sqlite3 agentcompany.db "
  SELECT id, role, agent_name, content
  FROM conversations
  WHERE id BETWEEN 100 AND 130
  ORDER BY id;
"
```

You'll typically see:
1. `user` — your DM
2. `orchestrator` — Meta-Orchestrator's response (with `[DELEGATE:1:...]` marker)
3. `orchestrator` (the company memory) — `meta-orchestrator` writes the directive
4. `ceo` — CEO's plan (with `[TASK:sdr_lead]` markers)
5. `lead` — Lead's plan (with `[WORKER:prospector]` markers)
6. `worker` — each worker's output
7. `lead` — synthesized team result
8. `ceo` — final synthesized report
9. `orchestrator` — final reply to user

If a step is missing, you've found the broken link.

---

## Common failure modes

### "Worker returned bad JSON"
**Symptom**: Qualifier or Prospector worker output isn't valid JSON.
**Fix**: The `Qualifier` worker auto-retries. If it persists, the model's struggling — switch to a stronger DeepSeek variant or temporarily route to Sonnet.

```python
# In company/workers/base_worker.py
DEEPSEEK = "deepseek/deepseek-chat-v3.1"  # try the bigger sibling
```

### "CEO doesn't know about my new lead"
**Symptom**: You added a lead but CEO never dispatches to it.
**Fix**: Update `company/ceo/system_prompt.md` to include the new lead in the "Your Team" section. The CEO can only delegate to leads it's been told about.

### "Orchestrator routes to wrong company"
**Symptom**: You ask about Company A, bot acts on Company B.
**Fix**: The orchestrator picks the closest match. If your company contexts are similar, be explicit in the message ("for Acme Corp specifically"). Or re-write company contexts to be more distinct.

### "Bot replies with the literal `[DELEGATE:1:...]` text"
**Symptom**: The orchestrator emitted the marker but didn't dispatch.
**Cause**: The regex in `orchestrator/agent.py` `chat()` didn't match. Probably a syntax variation from the LLM.
**Fix**: Check the marker's exact format. The regex is `\[DELEGATE:(\d+):(.+?)\]` — the LLM must use square brackets, capital DELEGATE, integer ID, colon-separated.

### "Slack disconnects every 15 minutes"
**Normal**. Socket Mode reconnects automatically. You'll see "stale connection" + new session in the logs. No action needed.

### "Composio tool calls fail silently"
**Symptom**: Worker says "sent" but nothing arrived.
**Fix**: Run `composio list` to verify connections. Check the Composio dashboard for failed actions. Often it's an expired OAuth token — reconnect the account.

---

## Resetting state

### Wipe one company's history (keep the company)
```bash
sqlite3 agentcompany.db "
  DELETE FROM conversations WHERE company_id = 1;
  DELETE FROM tasks WHERE company_id = 1;
"
```

### Delete a company entirely
```bash
sqlite3 agentcompany.db "
  DELETE FROM conversations WHERE company_id = 1;
  DELETE FROM tasks WHERE company_id = 1;
  DELETE FROM context_summaries WHERE company_id = 1;
  DELETE FROM companies WHERE id = 1;
"
```

### Nuclear option — start fresh
```bash
rm agentcompany.db
./setup.sh   # recreates schema
```

You lose all history. The bot will boot with no companies registered.

---

## Logs vs DB — when to look where

| Looking for | Check |
|---|---|
| Bot crashed | bot stdout / stderr (the terminal it's running in) |
| Bot replied wrong | `conversations` table (see what each tier said) |
| Tool call failed | `tasks.result` field for that task (worker writes errors here) |
| Cost spike | Anthropic console + OpenRouter dashboard |
| Slack didn't see message | bot stdout (Slack errors print there) |
| Schema migration | bot stdout when `init_schema()` ran |

---

## Exporting data

For analytics or backup:

```bash
# Whole DB to CSV
sqlite3 -header -csv agentcompany.db "SELECT * FROM conversations;" > conversations.csv
sqlite3 -header -csv agentcompany.db "SELECT * FROM tasks;" > tasks.csv

# Just one company
sqlite3 -header -csv agentcompany.db "
  SELECT * FROM conversations WHERE company_id = 1;
" > company1_conversations.csv
```

Or use a SQLite GUI like [DB Browser for SQLite](https://sqlitebrowser.org/) — much friendlier than the CLI for ad-hoc exploration.
