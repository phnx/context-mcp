"""
MCP tools for memory operations (SQLite backend)
"""

import logging
from datetime import datetime

from server_database import (
    store_memory as db_store_memory,
    get_memories as db_get_memories,
    update_memory as db_update_memory,
    delete_memory as db_delete_memory,
)
from server_datamodels import Memory

logger = logging.getLogger(__name__)


async def store_memory(user_id: str, key: str, value: str) -> dict:
    """Store a general-purpose memory for a user."""
    now = datetime.now().isoformat()
    memory = Memory(key=key, value=value, created_at=now, updated_at=now)
    db_store_memory(user_id, memory)

    logger.debug("tool calling: store_memory")

    return {
        "status": "success",
        "user_id": user_id,
        "key": key,
        "value": value,
        "updated_at": now,
    }


async def retrieve_memory(user_id: str, key: str = None) -> dict:
    """Retrieve a specific memory or all memories for a user."""
    logger.debug("tool calling: retrieve_memory")

    memories = db_get_memories(user_id)

    if not memories:
        return {"status": "not_found", "message": f"User {user_id} not found"}

    if key:
        if key not in memories:
            return {"status": "not_found", "message": f"Memory key '{key}' not found"}
        memory = memories[key]
        return {
            "status": "success",
            "key": key,
            "value": memory.value,
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
        }

    # Return all memories
    all_memories = {
        k: {"value": v.value, "created_at": v.created_at, "updated_at": v.updated_at}
        for k, v in memories.items()
    }
    return {"status": "success", "count": len(all_memories), "memories": all_memories}


async def update_memory(user_id: str, key: str, value: str) -> dict:
    """Update an existing memory for a user."""
    logger.debug("tool calling: update_memory")

    memories = db_get_memories(user_id)
    if key not in memories:
        return {"status": "error", "message": f"Memory key '{key}' does not exist"}

    now = datetime.now().isoformat()
    memory = memories[key]
    memory.value = value
    memory.updated_at = now
    db_update_memory(user_id, memory)

    return {
        "status": "success",
        "key": key,
        "value": value,
        "updated_at": now,
    }


async def delete_memory(user_id: str, key: str) -> dict:
    """Delete a memory for a user."""
    logger.debug("tool calling: delete_memory")

    memories = db_get_memories(user_id)
    if key not in memories:
        return {"status": "error", "message": f"Memory key '{key}' not found"}

    db_delete_memory(user_id, key)
    return {"status": "success", "message": f"Memory '{key}' deleted"}
