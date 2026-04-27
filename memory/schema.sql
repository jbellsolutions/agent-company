-- agent-company Postgres schema

CREATE TABLE IF NOT EXISTS companies (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    context     TEXT,                    -- company description, ICP, goals
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversations (
    id           SERIAL PRIMARY KEY,
    company_id   INTEGER REFERENCES companies(id),
    role         TEXT NOT NULL,          -- 'orchestrator', 'ceo', 'lead', 'worker', 'user'
    agent_name   TEXT,
    content      TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    id           SERIAL PRIMARY KEY,
    company_id   INTEGER REFERENCES companies(id),
    parent_id    INTEGER REFERENCES tasks(id),
    assigned_to  TEXT,                   -- agent role: 'sdr_lead', 'prospector', etc.
    status       TEXT DEFAULT 'pending', -- pending, in_progress, completed, failed
    description  TEXT NOT NULL,
    result       TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS context_summaries (
    id           SERIAL PRIMARY KEY,
    company_id   INTEGER REFERENCES companies(id),
    summary      TEXT NOT NULL,
    token_count  INTEGER,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_company ON conversations(company_id);
CREATE INDEX IF NOT EXISTS idx_tasks_company_status ON tasks(company_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to, status);
