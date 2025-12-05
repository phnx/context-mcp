"""
mcp tools for memory operations
"""

import logging
from datetime import datetime

from server_database import load_database, save_database
from server_datamodels import UserMemories, Memory

logger = logging.getLogger(__name__)


async def store_memory(user_id: str, key: str, value: str) -> dict:
    """
    Store general-purpose memories about the user (name, occupation, interests, etc).
    Use this for personal information that is NOT travel-related.

    Args:
        user_id: Unique identifier for the user
        key: Memory key (e.g., 'favourite_color', 'name')
        value: Memory value (string)

    Returns:
        Success message with memory details
    """
    database = load_database()

    if user_id not in database:
        database[user_id] = UserMemories(user_id=user_id)

    now = datetime.now().isoformat()
    database[user_id].memories[key] = Memory(
        key=key,
        value=value,
        created_at=database[user_id]
        .memories.get(key, Memory(key=key, value=value))
        .created_at,
        updated_at=now,
    )

    save_database(database)

    logger.debug("tool calling: store_memory")

    return {
        "status": "success",
        "user_id": user_id,
        "key": key,
        "value": value,
        "updated_at": now,
    }


async def retrieve_memory(user_id: str, key: str = None) -> dict:
    """
    Retrieve a specific memory or all memories for a user.

    Args:
        user_id: Unique identifier for the user
        key: Optional memory key. If not provided, returns all memories

    Returns:
        Memory or list of memories
    """
    database = load_database()

    logger.debug("tool calling: retrieve_memory")

    if user_id not in database:
        return {"status": "not_found", "message": f"User {user_id} not found"}

    if key:
        if key not in database[user_id].memories:
            return {"status": "not_found", "message": f"Memory key '{key}' not found"}

        memory = database[user_id].memories[key]
        return {
            "status": "success",
            "key": key,
            "value": memory.value,
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
        }

    # Return all memories
    memories = {
        k: {
            "value": v.value,
            "created_at": v.created_at,
            "updated_at": v.updated_at,
        }
        for k, v in database[user_id].memories.items()
    }

    return {
        "status": "success",
        "count": len(memories),
        "memories": memories,
    }


async def update_memory(user_id: str, key: str, value: str) -> dict:
    """
    Update an existing memory.

    Args:
        user_id: Unique identifier for the user
        key: Memory key to update
        value: New memory value

    Returns:
        Updated memory details
    """
    database = load_database()

    logger.debug("tool calling: update_memory")

    if user_id not in database or key not in database[user_id].memories:
        return {"status": "error", "message": f"Memory key '{key}' does not exist"}

    now = datetime.now().isoformat()
    memory = database[user_id].memories[key]
    memory.value = value
    memory.updated_at = now

    save_database(database)

    return {
        "status": "success",
        "key": key,
        "value": value,
        "updated_at": now,
    }


async def delete_memory(user_id: str, key: str) -> dict:
    """
    Delete a memory.

    Args:
        user_id: Unique identifier for the user
        key: Memory key to delete

    Returns:
        Success or error message
    """
    database = load_database()

    logger.debug("tool calling: delete_memory")

    if user_id not in database or key not in database[user_id].memories:
        return {"status": "error", "message": f"Memory key '{key}' not found"}

    del database[user_id].memories[key]
    save_database(database)

    return {"status": "success", "message": f"Memory '{key}' deleted"}
