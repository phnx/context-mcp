"""
MCP tools for travel preference operations (SQLite backend)
"""

import logging
from datetime import datetime
from typing import Optional, List

from server_database import (
    store_travel_preference as db_store_pref,
    get_travel_preferences as db_get_prefs,
    update_travel_preference as db_update_pref,
    delete_travel_preference as db_delete_pref,
)
from server_datamodels import TravelPreference

logger = logging.getLogger(__name__)


async def store_travel_preference(
    user_id: str,
    key: str,
    value: Optional[str] = None,
    values: Optional[List[str]] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    description: Optional[str] = None,
) -> dict:
    """Store travel preference for a user."""
    now = datetime.now().isoformat()
    pref = TravelPreference(
        key=key,
        value=value,
        values=values,
        min_value=min_value,
        max_value=max_value,
        description=description,
        created_at=now,
        updated_at=now,
    )
    db_store_pref(user_id, pref)

    logger.debug("tool calling: store_travel_preference")

    return {
        "status": "success",
        "user_id": user_id,
        "key": key,
        "preference": pref.model_dump(),
    }


async def retrieve_travel_preference(user_id: str, key: Optional[str] = None) -> dict:
    """Retrieve a travel preference or all preferences for a user."""
    logger.debug("tool calling: retrieve_travel_preference")

    prefs = db_get_prefs(user_id)

    if not prefs:
        return {"status": "not_found", "count": 0, "travel_preferences": {}}

    if key:
        if key not in prefs:
            return {"status": "not_found", "message": f"Preference '{key}' not found"}
        pref = prefs[key]
        return {"status": "success", "preference": pref.model_dump()}

    # Return all preferences
    all_prefs = {k: v.model_dump() for k, v in prefs.items()}
    return {
        "status": "success",
        "count": len(all_prefs),
        "travel_preferences": all_prefs,
    }


async def update_travel_preference(
    user_id: str,
    key: str,
    value: Optional[str] = None,
    values: Optional[List[str]] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    description: Optional[str] = None,
) -> dict:
    """Update an existing travel preference."""
    logger.debug("tool calling: update_travel_preference")

    prefs = db_get_prefs(user_id)
    if key not in prefs:
        return {"status": "error", "message": f"Preference '{key}' does not exist"}

    pref = prefs[key]

    if value is not None:
        pref.value = value
    if values is not None:
        pref.values = values
    if min_value is not None:
        pref.min_value = min_value
    if max_value is not None:
        pref.max_value = max_value
    if description is not None:
        pref.description = description
    pref.updated_at = datetime.now().isoformat()

    db_update_pref(user_id, pref)

    return {"status": "success", "key": key, "preference": pref.model_dump()}


async def delete_travel_preference(user_id: str, key: str) -> dict:
    """Delete a travel preference for a user."""
    logger.debug("tool calling: delete_travel_preference")

    prefs = db_get_prefs(user_id)
    if key not in prefs:
        return {"status": "error", "message": f"Preference '{key}' not found"}

    db_delete_pref(user_id, key)
    return {"status": "success", "message": f"Preference '{key}' deleted"}
