-- agent-company SQLite schema

CREATE TABLE IF NOT EXISTS companies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    context     TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id   INTEGER REFERENCES companies(id),
    role         TEXT NOT NULL,           -- 'orchestrator', 'ceo', 'lead', 'worker', 'user'
    agent_name   TEXT,
    content      TEXT NOT NULL,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id   INTEGER REFERENCES companies(id),
    parent_id    INTEGER REFERENCES tasks(id),
    assigned_to  TEXT,                    -- 'sdr_lead', 'prospector', etc.
    status       TEXT DEFAULT 'pending',  -- pending, in_progress, completed, failed
    description  TEXT NOT NULL,
    result       TEXT,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS context_summaries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id   INTEGER REFERENCES companies(id),
    summary      TEXT NOT NULL,
    token_count  INTEGER,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_company ON conversations(company_id);
CREATE INDEX IF NOT EXISTS idx_tasks_company_status  ON tasks(company_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned        ON tasks(assigned_to, status);
