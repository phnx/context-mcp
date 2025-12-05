"""
mcp tools for travel preference operations
"""

import logging
from datetime import datetime
from typing import Optional, List

from server_database import load_database, save_database
from server_datamodels import UserMemories, TravelPreference

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
    """
    Store travel preference for a user.

    Args:
        user_id: Unique identifier for the user
        key: Preference key (e.g., 'favorite_destination', 'budget')
        value: Single preference value
        values: Multiple preference values
        min_value: Minimum value (e.g., budget minimum)
        max_value: Maximum value (e.g., budget maximum)
        description: Description of the preference

    Returns:
        Success message with preference details
    """
    database = load_database()

    if user_id not in database:
        database[user_id] = UserMemories(user_id=user_id)

    now = datetime.now().isoformat()
    database[user_id].travel_preferences[key] = TravelPreference(
        key=key,
        value=value,
        values=values,
        min_value=min_value,
        max_value=max_value,
        description=description,
        created_at=now,
        updated_at=now,
    )

    save_database(database)

    logger.debug("tool calling: store_travel_preference")

    return {
        "status": "success",
        "user_id": user_id,
        "key": key,
        "preference": {
            "value": value,
            "values": values,
            "min_value": min_value,
            "max_value": max_value,
            "description": description,
            "created_at": now,
            "updated_at": now,
        },
    }


async def retrieve_travel_preference(user_id: str, key: Optional[str] = None) -> dict:
    """
    Retrieve travel preference or all preferences for a user.

    Args:
        user_id: Unique identifier for the user
        key: Optional preference key. If not provided, returns all preferences

    Returns:
        Travel preference or list of preferences
    """
    database = load_database()

    logger.debug("tool calling: retrieve_travel_preference")

    if user_id not in database:
        return {
            "status": "not_found",
            "count": 0,
            "travel_preferences": {},
        }

    if key:
        if key not in database[user_id].travel_preferences:
            return {"status": "not_found", "message": f"Preference '{key}' not found"}

        pref = database[user_id].travel_preferences[key]
        return {
            "status": "success",
            "preference": {
                "value": pref.value,
                "values": pref.values,
                "min_value": pref.min_value,
                "max_value": pref.max_value,
                "description": pref.description,
                "created_at": pref.created_at,
                "updated_at": pref.updated_at,
            },
        }

    # Return all preferences
    prefs = {
        k: {
            "value": v.value,
            "values": v.values,
            "min_value": v.min_value,
            "max_value": v.max_value,
            "description": v.description,
            "created_at": v.created_at,
            "updated_at": v.updated_at,
        }
        for k, v in database[user_id].travel_preferences.items()
    }

    return {
        "status": "success",
        "count": len(prefs),
        "travel_preferences": prefs,
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
    """
    Update an existing travel preference.

    Args:
        user_id: Unique identifier for the user
        key: Preference key to update
        value: Updated single value
        values: Updated multiple values
        min_value: Updated minimum value
        max_value: Updated maximum value
        description: Updated description

    Returns:
        Updated preference details
    """
    database = load_database()

    logger.debug("tool calling: update_travel_preference")

    if user_id not in database or key not in database[user_id].travel_preferences:
        return {"status": "error", "message": f"Preference '{key}' does not exist"}

    now = datetime.now().isoformat()
    pref = database[user_id].travel_preferences[key]

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

    pref.updated_at = now

    save_database(database)

    return {
        "status": "success",
        "key": key,
        "preference": {
            "value": pref.value,
            "values": pref.values,
            "min_value": pref.min_value,
            "max_value": pref.max_value,
            "description": pref.description,
            "created_at": pref.created_at,
            "updated_at": pref.updated_at,
        },
    }


async def delete_travel_preference(user_id: str, key: str) -> dict:
    """
    Delete a travel preference.

    Args:
        user_id: Unique identifier for the user
        key: Preference key to delete

    Returns:
        Success or error message
    """
    database = load_database()

    logger.debug("tool calling: delete_travel_preference")

    if user_id not in database or key not in database[user_id].travel_preferences:
        return {"status": "error", "message": f"Preference '{key}' not found"}

    del database[user_id].travel_preferences[key]
    save_database(database)

    return {"status": "success", "message": f"Preference '{key}' deleted"}
