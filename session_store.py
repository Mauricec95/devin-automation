import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from config import DATABASE_PATH

logger = logging.getLogger(__name__)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                issue_number INTEGER NOT NULL,
                issue_title TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                pr_url TEXT,
                pr_number INTEGER,
                error TEXT,
                started_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                duration_seconds INTEGER
            )
        """)
        conn.commit()
    logger.info("Database initialised at %s", DATABASE_PATH)


def create_session(
    session_id: str,
    issue_number: int,
    issue_title: str,
    issue_type: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO sessions
                (session_id, issue_number, issue_title, issue_type, status, started_at, updated_at)
            VALUES (?, ?, ?, ?, 'running', ?, ?)
            """,
            (session_id, issue_number, issue_title, issue_type, now, now),
        )
        conn.commit()
    logger.info(
        json.dumps({"event": "session_created", "session_id": session_id, "issue": issue_number})
    )


def update_session_status(
    session_id: str,
    status: str,
    pr_url: Optional[str] = None,
    pr_number: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT started_at FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()

        duration = None
        completed_at = None
        if row and status in ("success", "failed"):
            started = datetime.fromisoformat(row["started_at"])
            completed_at = now
            duration = int((datetime.now(timezone.utc) - started).total_seconds())

        conn.execute(
            """
            UPDATE sessions
            SET status = ?, pr_url = ?, pr_number = ?, error = ?,
                updated_at = ?, completed_at = ?, duration_seconds = ?
            WHERE session_id = ?
            """,
            (status, pr_url, pr_number, error, now, completed_at, duration, session_id),
        )
        conn.commit()
    logger.info(
        json.dumps({"event": "session_updated", "session_id": session_id, "status": status})
    )


def get_all_sessions() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_session(session_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
    return dict(row) if row else None
