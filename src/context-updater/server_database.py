import json
import os
from pathlib import Path

from filelock import FileLock
from server_datamodels import UserMemories, Memory, TravelPreference

# Database file path
DB_FILE = Path("database/memories.json")
DB_LOCK_FILE = Path("database/memories.json.lock")

# Test database file path
TEST_DB_FILE = Path("test/test_memories.json")
TEST_DB_LOCK_FILE = Path("test/test_memories.json.lock")

# Check env vars for test environment
is_test = os.environ.get("IS_MCP_CONTEXT_UPDATER_TEST", "false").lower() == "true"

# ============================================================================
# Helper Functions
# ============================================================================


def _get_db_paths() -> tuple[Path, Path]:
    """Get database and lock file paths based on environment."""
    if is_test:
        return TEST_DB_FILE, TEST_DB_LOCK_FILE
    else:
        return DB_FILE, DB_LOCK_FILE


def _ensure_db_file_exists(db_path: Path) -> None:
    """Ensure database file and directory exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        db_path.write_text(json.dumps({}))


# ============================================================================
# Database Operations
# ============================================================================


def load_database() -> dict[str, UserMemories]:
    """Load all memories from JSON file (thread-safe)."""
    db_path, lock_path = _get_db_paths()
    _ensure_db_file_exists(db_path)

    lock = FileLock(str(lock_path), timeout=10)

    try:
        with lock:
            with open(db_path, "r") as f:
                data = json.load(f)

            return {
                user_id: UserMemories(
                    user_id=user_id,
                    memories={
                        k: Memory(**v) for k, v in user_data.get("memories", {}).items()
                    },
                    travel_preferences={
                        k: TravelPreference(**v)
                        for k, v in user_data.get("travel_preferences", {}).items()
                    },
                )
                for user_id, user_data in data.items()
            }
    except (json.JSONDecodeError, ValueError):
        return {}


def save_database(database: dict[str, UserMemories]) -> None:
    """Save all memories to JSON file (thread-safe)."""
    db_path, lock_path = _get_db_paths()
    _ensure_db_file_exists(db_path)

    lock = FileLock(str(lock_path), timeout=10)

    with lock:
        data = {
            user_id: {
                "user_id": user_id,
                "memories": {k: v.model_dump() for k, v in user_data.memories.items()},
                "travel_preferences": {
                    k: v.model_dump() for k, v in user_data.travel_preferences.items()
                },
            }
            for user_id, user_data in database.items()
        }

        # Write atomically using temp file
        temp_file = db_path.with_suffix(".json.tmp")
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        temp_file.replace(db_path)


def get_user_memories(user_id: str) -> UserMemories:
    """Get or create user memories"""
    database = load_database()
    if user_id not in database:
        database[user_id] = UserMemories(user_id=user_id)
        save_database(database)

    return database[user_id]
