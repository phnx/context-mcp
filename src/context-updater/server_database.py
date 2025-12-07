import os
import sqlite3
import json
from pathlib import Path
from typing import Any

from server_datamodels import UserMemories, Memory, TravelPreference

# Database paths
DB_FILE = Path("database/memories.db")
TEST_DB_FILE = Path("test/test_memories.db")
is_test = os.environ.get("IS_MCP_CONTEXT_UPDATER_TEST", "false").lower() == "true"


def _get_db_path() -> Path:
    return TEST_DB_FILE if is_test else DB_FILE


def _get_connection() -> sqlite3.Connection:
    """Return SQLite connection and ensure tables exist."""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                user_id TEXT,
                key TEXT,
                content TEXT,
                PRIMARY KEY (user_id, key)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS travel_preferences (
                user_id TEXT,
                key TEXT,
                content TEXT,
                PRIMARY KEY (user_id, key)
            )
            """
        )
    return conn


# ==========================
# Memory CRUD Operations
# ==========================


def store_memory(user_id: str, memory: Memory) -> None:
    conn = _get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO memories (user_id, key, content)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, key) DO UPDATE SET content=excluded.content
            """,
            (user_id, memory.key, memory.model_dump_json()),
        )
    conn.close()


def get_memories(user_id: str) -> dict[str, Memory]:
    conn = _get_connection()
    rows = conn.execute(
        "SELECT key, content FROM memories WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return {
        row["key"]: Memory.model_validate(json.loads(row["content"])) for row in rows
    }


def update_memory(user_id: str, memory: Memory) -> None:
    conn = _get_connection()
    with conn:
        conn.execute(
            """
            UPDATE memories
            SET content = ?
            WHERE user_id = ? AND key = ?
            """,
            (memory.model_dump_json(), user_id, memory.key),
        )
    conn.close()


def delete_memory(user_id: str, key: str) -> None:
    conn = _get_connection()
    with conn:
        conn.execute(
            "DELETE FROM memories WHERE user_id = ? AND key = ?", (user_id, key)
        )
    conn.close()


# ==========================
# Travel Preferences CRUD
# ==========================


def store_travel_preference(user_id: str, pref: TravelPreference) -> None:
    conn = _get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO travel_preferences (user_id, key, content)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, key) DO UPDATE SET content=excluded.content
            """,
            (user_id, pref.key, pref.model_dump_json()),
        )
    conn.close()


def get_travel_preferences(user_id: str) -> dict[str, TravelPreference]:
    conn = _get_connection()
    rows = conn.execute(
        "SELECT key, content FROM travel_preferences WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return {
        row["key"]: TravelPreference.model_validate(json.loads(row["content"]))
        for row in rows
    }


def update_travel_preference(user_id: str, pref: TravelPreference) -> None:
    conn = _get_connection()
    with conn:
        conn.execute(
            """
            UPDATE travel_preferences
            SET content = ?
            WHERE user_id = ? AND key = ?
            """,
            (pref.model_dump_json(), user_id, pref.key),
        )
    conn.close()


def delete_travel_preference(user_id: str, key: str) -> None:
    conn = _get_connection()
    with conn:
        conn.execute(
            "DELETE FROM travel_preferences WHERE user_id = ? AND key = ?",
            (user_id, key),
        )
    conn.close()


# ==========================
# Database Overview
# ==========================


def get_database_overview() -> dict[str, Any]:
    """Return top-level overview: total users + counts per user."""
    conn = _get_connection()
    users = set(
        row["user_id"]
        for row in conn.execute(
            "SELECT user_id FROM memories UNION SELECT user_id FROM travel_preferences"
        ).fetchall()
    )
    overview = []
    for user_id in users:
        memories_count = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        prefs_count = conn.execute(
            "SELECT COUNT(*) FROM travel_preferences WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        overview.append(
            {
                "user_id_prefix": f"{user_id[:2]}...",
                "memories_count": memories_count,
                "travel_preferences_count": prefs_count,
            }
        )
    conn.close()
    return {"total_users": len(users), "users": overview}


def get_all_users() -> dict:
    """
    Returns all users with their memory and travel preference counts.
    Output:
        {
            "user1": {"memory_count": 5, "travel_pref_count": 3},
            "user2": {"memory_count": 2, "travel_pref_count": 0},
        }
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Count memories per user
    cursor.execute(
        "SELECT user_id, COUNT(*) as memory_count FROM memories GROUP BY user_id"
    )
    memory_counts = {row["user_id"]: row["memory_count"] for row in cursor.fetchall()}

    # Count travel preferences per user
    cursor.execute(
        "SELECT user_id, COUNT(*) as travel_pref_count FROM travel_preferences GROUP BY user_id"
    )
    pref_counts = {
        row["user_id"]: row["travel_pref_count"] for row in cursor.fetchall()
    }

    # Combine results
    all_users = {}
    user_ids = set(memory_counts) | set(pref_counts)
    for uid in user_ids:
        all_users[uid] = {
            "memory_count": memory_counts.get(uid, 0),
            "travel_pref_count": pref_counts.get(uid, 0),
        }

    conn.close()
    return all_users
