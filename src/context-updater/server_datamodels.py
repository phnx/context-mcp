from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Data Models
# ============================================================================


class Memory(BaseModel):
    """Individual memory entry for general-purpose"""

    key: str
    value: Any
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class TravelPreference(BaseModel):
    """Individual travel preference entry"""

    key: str  # e.g., "preferred_destinations"
    value: Optional[str] = None  # e.g., "Europe"
    values: Optional[List[str]] = None  # e.g., ["Europe", "Japan"]
    min_value: Optional[float] = None  # e.g., min budget
    max_value: Optional[float] = None  # e.g., max budget
    description: Optional[str] = None  # Human-readable note
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class UserMemories(BaseModel):
    """All memories for a single user"""

    user_id: str
    memories: dict[str, Memory] = Field(default_factory=dict)
    travel_preferences: dict[str, TravelPreference] = Field(default_factory=dict)
