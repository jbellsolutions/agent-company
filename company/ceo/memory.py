from __future__ import annotations

import os
import sqlite3
from typing import Any

DEFAULT_DB_PATH = "agentcompany.db"


def _conn() -> sqlite3.Connection:
    db_path = os.environ.get("DB_PATH", DEFAULT_DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(schema_path: str = "memory/schema.sql") -> None:
    """Apply the schema file to the SQLite DB. Idempotent."""
    with open(schema_path, "r") as f:
        ddl = f.read()
    with _conn() as conn:
        conn.executescript(ddl)


def get_or_create_company(name: str, context: str = "") -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO companies (name, context) VALUES (?, ?) "
            "ON CONFLICT(name) DO UPDATE SET context = excluded.context "
            "RETURNING id",
            (name, context),
        )
        row = cur.fetchone()
        assert row is not None
        return int(row["id"])


def save_message(company_id: int, role: str, agent_name: str, content: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO conversations (company_id, role, agent_name, content) VALUES (?, ?, ?, ?)",
            (company_id, role, agent_name, content),
        )


def get_recent_history(company_id: int, limit: int = 50) -> list[dict[str, Any]]:
    with _conn() as conn:
        cur = conn.execute(
            "SELECT role, agent_name, content, created_at FROM conversations "
            "WHERE company_id = ? ORDER BY created_at DESC LIMIT ?",
            (company_id, limit),
        )
        rows = [dict(r) for r in cur.fetchall()]
        return list(reversed(rows))


def create_task(
    company_id: int,
    description: str,
    assigned_to: str,
    parent_id: int | None = None,
) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (company_id, description, assigned_to, parent_id) "
            "VALUES (?, ?, ?, ?) RETURNING id",
            (company_id, description, assigned_to, parent_id),
        )
        row = cur.fetchone()
        assert row is not None
        return int(row["id"])


def update_task(task_id: int, status: str, result: str | None = None) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE tasks SET status = ?, result = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, result, task_id),
        )


def get_active_tasks(company_id: int) -> list[dict[str, Any]]:
    with _conn() as conn:
        cur = conn.execute(
            "SELECT * FROM tasks WHERE company_id = ? AND status IN ('pending','in_progress') "
            "ORDER BY created_at",
            (company_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def list_companies() -> list[dict[str, Any]]:
    with _conn() as conn:
        cur = conn.execute("SELECT id, name, context FROM companies ORDER BY name")
        return [dict(r) for r in cur.fetchall()]


def save_context_summary(company_id: int, summary: str, token_count: int = 0) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO context_summaries (company_id, summary, token_count) VALUES (?, ?, ?)",
            (company_id, summary, token_count),
        )


def get_latest_summary(company_id: int) -> str | None:
    with _conn() as conn:
        cur = conn.execute(
            "SELECT summary FROM context_summaries WHERE company_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (company_id,),
        )
        row = cur.fetchone()
        return str(row["summary"]) if row else None
