# independent counter class for tool usage using SQLite
import sqlite3
from pathlib import Path
from typing import Dict

DB_FILE = Path("database/tool_analytic.db")


class ToolCounter:
    """Thread-safe tool usage counter using SQLite."""

    def __init__(self):
        """Initialize SQLite database and table."""
        self.db_file = DB_FILE
        self._ensure_table_exists()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table_exists(self):
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_stats (
                    tool_name TEXT PRIMARY KEY,
                    calls INTEGER DEFAULT 0,
                    tokens_in INTEGER DEFAULT 0,
                    tokens_out INTEGER DEFAULT 0
                )
                """
            )

    def increment_tool(
        self, tool_name: str, calls: int = 1, tokens_in: int = 0, tokens_out: int = 0
    ) -> Dict[str, int]:
        """Increment tool call count and tokens."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO tool_stats(tool_name, calls, tokens_in, tokens_out)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(tool_name) DO UPDATE SET
                    calls = calls + excluded.calls,
                    tokens_in = tokens_in + excluded.tokens_in,
                    tokens_out = tokens_out + excluded.tokens_out
                """,
                (tool_name, calls, tokens_in, tokens_out),
            )
            cursor = conn.execute(
                "SELECT calls, tokens_in, tokens_out FROM tool_stats WHERE tool_name = ?",
                (tool_name,),
            )
            row = cursor.fetchone()
            return dict(row)

    def get_tool_stats(self, tool_name: str) -> Dict[str, int]:
        """Get stats for a specific tool."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT calls, tokens_in, tokens_out FROM tool_stats WHERE tool_name = ?",
                (tool_name,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {"calls": 0, "tokens_in": 0, "tokens_out": 0}

    def get_all_stats(self) -> Dict[str, Dict[str, int]]:
        """Get stats for all tools."""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM tool_stats")
            return {
                row["tool_name"]: {
                    "calls": row["calls"],
                    "tokens_in": row["tokens_in"],
                    "tokens_out": row["tokens_out"],
                }
                for row in cursor.fetchall()
            }

    def reset_tool(self, tool_name: str) -> None:
        """Reset stats for a tool."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO tool_stats(tool_name, calls, tokens_in, tokens_out)
                VALUES (?, 0, 0, 0)
                ON CONFLICT(tool_name) DO UPDATE SET calls=0, tokens_in=0, tokens_out=0
                """,
                (tool_name,),
            )
