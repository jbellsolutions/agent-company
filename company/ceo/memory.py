from __future__ import annotations

import os
from typing import Any

import psycopg2
import psycopg2.extras


def _conn() -> psycopg2.extensions.connection:
    return psycopg2.connect(os.environ["DATABASE_URL"])


def get_or_create_company(name: str, context: str = "") -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO companies (name, context)
                VALUES (%s, %s)
                ON CONFLICT (name) DO UPDATE SET context = EXCLUDED.context
                RETURNING id
                """,
                (name, context),
            )
            row = cur.fetchone()
            assert row is not None
            return int(row[0])


def save_message(company_id: int, role: str, agent_name: str, content: str) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO conversations (company_id, role, agent_name, content) VALUES (%s, %s, %s, %s)",
                (company_id, role, agent_name, content),
            )


def get_recent_history(company_id: int, limit: int = 50) -> list[Any]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT role, agent_name, content, created_at
                FROM conversations
                WHERE company_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (company_id, limit),
            )
            rows = cur.fetchall()
            return list(reversed(rows))


def create_task(
    company_id: int,
    description: str,
    assigned_to: str,
    parent_id: int | None = None,
) -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (company_id, description, assigned_to, parent_id) VALUES (%s, %s, %s, %s) RETURNING id",
                (company_id, description, assigned_to, parent_id),
            )
            row = cur.fetchone()
            assert row is not None
            return int(row[0])


def update_task(task_id: int, status: str, result: str | None = None) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET status=%s, result=%s, updated_at=NOW() WHERE id=%s",
                (status, result, task_id),
            )


def get_active_tasks(company_id: int) -> list[Any]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM tasks WHERE company_id=%s AND status IN ('pending','in_progress') ORDER BY created_at",
                (company_id,),
            )
            return cur.fetchall()


def list_companies() -> list[Any]:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, name, context FROM companies ORDER BY name")
            return cur.fetchall()


def save_context_summary(company_id: int, summary: str, token_count: int = 0) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO context_summaries (company_id, summary, token_count) VALUES (%s, %s, %s)",
                (company_id, summary, token_count),
            )


def get_latest_summary(company_id: int) -> str | None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT summary FROM context_summaries WHERE company_id=%s ORDER BY created_at DESC LIMIT 1",
                (company_id,),
            )
            row = cur.fetchone()
            return str(row[0]) if row else None
