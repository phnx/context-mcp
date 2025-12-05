# test general functionality of MCP tools
import os
from pathlib import Path
import sys

import pytest
from pytest_asyncio import fixture

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "context-updater"))

# set before import
os.environ["IS_MCP_CONTEXT_UPDATER_TEST"] = "true"

from tools.memory_tools import (
    store_memory,
    retrieve_memory,
    update_memory,
    delete_memory,
)
from tools.travel_preference_tools import (
    store_travel_preference,
    retrieve_travel_preference,
    update_travel_preference,
    delete_travel_preference,
)

# Test database file path
TEST_DB_FILE = Path("test/test_memories.json")
TEST_DB_LOCK_FILE = Path("test/test_memories.json.lock")


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    # Remove test database file
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

        if TEST_DB_LOCK_FILE.exists():
            TEST_DB_LOCK_FILE.unlink()

        print("✓ Test database cleaned up")

    """Set test environment variable"""
    os.environ["IS_MCP_CONTEXT_UPDATER_TEST"] = "true"
    print(
        f"\n✓ Set IS_MCP_CONTEXT_UPDATER_TEST={os.environ.get('IS_MCP_CONTEXT_UPDATER_TEST')}"
    )
    yield
    os.environ.pop("IS_MCP_CONTEXT_UPDATER_TEST", None)
    print(f"\n✓ Unset IS_MCP_CONTEXT_UPDATER_TEST")

    # Remove test database file
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

        if TEST_DB_LOCK_FILE.exists():
            TEST_DB_LOCK_FILE.unlink()

        print("✓ Test database cleaned up")


@pytest.fixture(autouse=True)
def cleanup_test_db():
    """Clean test database before and after each test"""
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()
        if TEST_DB_LOCK_FILE.exists():
            TEST_DB_LOCK_FILE.unlink()

    yield

    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()
        if TEST_DB_LOCK_FILE.exists():
            TEST_DB_LOCK_FILE.unlink()


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return "test_user_123"


# ============================================================================
# Memory Tests
# ============================================================================


class TestMemoryTools:
    """Test general memory tools"""

    @pytest.mark.asyncio
    async def test_store_memory(self, test_user_id):
        """Test storing a memory"""
        result = await store_memory(test_user_id, "name", "Alice")

        assert result["status"] == "success"
        assert result["user_id"] == test_user_id
        assert result["key"] == "name"
        assert result["value"] == "Alice"

    @pytest.mark.asyncio
    async def test_retrieve_memory_single(self, test_user_id):
        """Test retrieving a single memory"""
        await store_memory(test_user_id, "name", "Alice")
        result = await retrieve_memory(test_user_id, "name")

        assert result["status"] == "success"
        assert result["value"] == "Alice"
        assert result["key"] == "name"

    @pytest.mark.asyncio
    async def test_retrieve_memory_all(self, test_user_id):
        """Test retrieving all memories"""
        await store_memory(test_user_id, "name", "Alice")
        await store_memory(test_user_id, "age", "30")
        await store_memory(test_user_id, "job", "Engineer")

        result = await retrieve_memory(test_user_id)

        assert result["status"] == "success"
        assert result["count"] == 3
        assert "name" in result["memories"]
        assert "age" in result["memories"]
        assert "job" in result["memories"]

    @pytest.mark.asyncio
    async def test_retrieve_memory_not_found(self, test_user_id):
        """Test retrieving non-existent memory"""
        result = await retrieve_memory(test_user_id, "nonexistent")

        assert result["status"] == "not_found"
        assert "not found" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_update_memory(self, test_user_id):
        """Test updating a memory"""
        await store_memory(test_user_id, "name", "Alice")
        result = await update_memory(test_user_id, "name", "Alice Smith")

        assert result["status"] == "success"
        assert result["value"] == "Alice Smith"

        # Verify it was updated
        retrieved = await retrieve_memory(test_user_id, "name")
        assert retrieved["value"] == "Alice Smith"

    @pytest.mark.asyncio
    async def test_update_memory_not_found(self, test_user_id):
        """Test updating non-existent memory"""
        result = await update_memory(test_user_id, "nonexistent", "value")

        assert result["status"] == "error"
        assert "does not exist" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_memory(self, test_user_id):
        """Test deleting a memory"""
        await store_memory(test_user_id, "name", "Alice")
        result = await delete_memory(test_user_id, "name")

        assert result["status"] == "success"

        # Verify it was deleted
        retrieved = await retrieve_memory(test_user_id, "name")
        assert retrieved["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self, test_user_id):
        """Test deleting non-existent memory"""
        result = await delete_memory(test_user_id, "nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()


# ============================================================================
# Travel Preference Tests
# ============================================================================


class TestTravelPreferenceTools:
    """Test travel preference tools"""

    @pytest.mark.asyncio
    async def test_store_travel_preference_single_value(self, test_user_id):
        """Test storing travel preference with single value"""
        result = await store_travel_preference(
            test_user_id, "favorite_destination", value="Europe"
        )

        assert result["status"] == "success"
        assert result["key"] == "favorite_destination"
        assert result["preference"]["value"] == "Europe"

    @pytest.mark.asyncio
    async def test_store_travel_preference_multiple_values(self, test_user_id):
        """Test storing travel preference with multiple values"""
        result = await store_travel_preference(
            test_user_id,
            "preferred_destinations",
            values=["Europe", "Japan", "Thailand"],
        )

        assert result["status"] == "success"
        assert result["preference"]["values"] == ["Europe", "Japan", "Thailand"]

    @pytest.mark.asyncio
    async def test_store_travel_preference_budget_range(self, test_user_id):
        """Test storing travel preference with budget range"""
        result = await store_travel_preference(
            test_user_id,
            "budget",
            min_value=1000.0,
            max_value=5000.0,
            description="Budget per trip",
        )

        assert result["status"] == "success"
        assert result["preference"]["min_value"] == 1000.0
        assert result["preference"]["max_value"] == 5000.0
        assert result["preference"]["description"] == "Budget per trip"

    @pytest.mark.asyncio
    async def test_store_travel_preference_all_fields(self, test_user_id):
        """Test storing travel preference with all fields"""
        result = await store_travel_preference(
            test_user_id,
            "trip_details",
            value="Summer vacation",
            values=["Beach", "Mountain"],
            min_value=2000.0,
            max_value=8000.0,
            description="Ideal summer trip",
        )

        assert result["status"] == "success"
        pref = result["preference"]
        assert pref["value"] == "Summer vacation"
        assert pref["values"] == ["Beach", "Mountain"]
        assert pref["min_value"] == 2000.0
        assert pref["max_value"] == 8000.0
        assert pref["description"] == "Ideal summer trip"

    @pytest.mark.asyncio
    async def test_retrieve_travel_preference_single(self, test_user_id):
        """Test retrieving single travel preference"""
        await store_travel_preference(
            test_user_id, "favorite_destination", value="Europe"
        )
        result = await retrieve_travel_preference(test_user_id, "favorite_destination")

        assert result["status"] == "success"
        assert result["preference"]["value"] == "Europe"

    @pytest.mark.asyncio
    async def test_retrieve_travel_preference_all(self, test_user_id):
        """Test retrieving all travel preferences"""
        await store_travel_preference(test_user_id, "destination", value="Europe")
        await store_travel_preference(
            test_user_id, "budget", min_value=1000.0, max_value=5000.0
        )
        await store_travel_preference(test_user_id, "style", value="Adventure")

        result = await retrieve_travel_preference(test_user_id)

        assert result["status"] == "success"
        assert result["count"] == 3
        assert "destination" in result["travel_preferences"]
        assert "budget" in result["travel_preferences"]
        assert "style" in result["travel_preferences"]

    @pytest.mark.asyncio
    async def test_retrieve_travel_preference_not_found(self, test_user_id):
        """Test retrieving non-existent travel preference"""
        result = await retrieve_travel_preference(test_user_id, "nonexistent")

        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_update_travel_preference_single_value(self, test_user_id):
        """Test updating travel preference with single value"""
        await store_travel_preference(test_user_id, "destination", value="Europe")
        result = await update_travel_preference(
            test_user_id, "destination", value="Asia"
        )

        assert result["status"] == "success"
        assert result["preference"]["value"] == "Asia"

        # Verify update persisted
        retrieved = await retrieve_travel_preference(test_user_id, "destination")
        assert retrieved["preference"]["value"] == "Asia"

    @pytest.mark.asyncio
    async def test_update_travel_preference_multiple_values(self, test_user_id):
        """Test updating travel preference with multiple values"""
        await store_travel_preference(test_user_id, "destinations", values=["Europe"])
        result = await update_travel_preference(
            test_user_id, "destinations", values=["Europe", "Asia", "Africa"]
        )

        assert result["status"] == "success"
        assert result["preference"]["values"] == ["Europe", "Asia", "Africa"]

    @pytest.mark.asyncio
    async def test_update_travel_preference_budget_range(self, test_user_id):
        """Test updating travel preference budget range"""
        await store_travel_preference(
            test_user_id, "budget", min_value=1000.0, max_value=5000.0
        )
        result = await update_travel_preference(
            test_user_id, "budget", min_value=2000.0, max_value=10000.0
        )

        assert result["status"] == "success"
        assert result["preference"]["min_value"] == 2000.0
        assert result["preference"]["max_value"] == 10000.0

    @pytest.mark.asyncio
    async def test_update_travel_preference_not_found(self, test_user_id):
        """Test updating non-existent travel preference"""
        result = await update_travel_preference(
            test_user_id, "nonexistent", value="value"
        )

        assert result["status"] == "error"
        assert "does not exist" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_travel_preference(self, test_user_id):
        """Test deleting travel preference"""
        await store_travel_preference(test_user_id, "destination", value="Europe")
        result = await delete_travel_preference(test_user_id, "destination")

        assert result["status"] == "success"

        # Verify deletion
        retrieved = await retrieve_travel_preference(test_user_id, "destination")
        assert retrieved["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_delete_travel_preference_not_found(self, test_user_id):
        """Test deleting non-existent travel preference"""
        result = await delete_travel_preference(test_user_id, "nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_travel_preference_timestamps(self, test_user_id):
        """Test that timestamps are set correctly"""
        result = await store_travel_preference(
            test_user_id, "destination", value="Europe"
        )

        pref = result["preference"]
        assert "created_at" in pref
        assert "updated_at" in pref
        assert pref["created_at"] == pref["updated_at"]

    @pytest.mark.asyncio
    async def test_travel_preference_timestamps_on_update(self, test_user_id):
        """Test that updated_at changes on update but created_at stays same"""
        import time

        store_result = await store_travel_preference(
            test_user_id, "destination", value="Europe"
        )
        created_at = store_result["preference"]["created_at"]

        time.sleep(0.1)  # Small delay to ensure timestamp difference

        update_result = await update_travel_preference(
            test_user_id, "destination", value="Asia"
        )
        updated_at = update_result["preference"]["updated_at"]

        assert created_at == update_result["preference"]["created_at"]
        assert updated_at > created_at

    @pytest.mark.asyncio
    async def test_multiple_users_isolated(self):
        """Test that preferences are isolated between users"""
        user1 = "user_1"
        user2 = "user_2"

        await store_travel_preference(user1, "destination", value="Europe")
        await store_travel_preference(user2, "destination", value="Asia")

        result1 = await retrieve_travel_preference(user1, "destination")
        result2 = await retrieve_travel_preference(user2, "destination")

        assert result1["preference"]["value"] == "Europe"
        assert result2["preference"]["value"] == "Asia"

    @pytest.mark.asyncio
    async def test_overwrite_travel_preference(self, test_user_id):
        """Test that storing with same key overwrites previous value"""
        await store_travel_preference(test_user_id, "destination", value="Europe")
        await store_travel_preference(test_user_id, "destination", value="Asia")

        result = await retrieve_travel_preference(test_user_id, "destination")

        assert result["preference"]["value"] == "Asia"

        # Verify only one entry exists
        all_prefs = await retrieve_travel_preference(test_user_id)
        assert all_prefs["count"] == 1

    @pytest.mark.asyncio
    async def test_travel_preference_with_empty_values(self, test_user_id):
        """Test storing travel preference with empty/null values"""
        result = await store_travel_preference(test_user_id, "destination")

        assert result["status"] == "success"
        pref = result["preference"]
        assert pref["value"] is None
        assert pref["values"] is None
        assert pref["min_value"] is None
        assert pref["max_value"] is None

    @pytest.mark.asyncio
    async def test_travel_preference_description_only(self, test_user_id):
        """Test storing travel preference with only description"""
        result = await store_travel_preference(
            test_user_id,
            "travel_notes",
            description="Prefer off-season travel for better prices",
        )

        assert result["status"] == "success"
        assert (
            result["preference"]["description"]
            == "Prefer off-season travel for better prices"
        )

    @pytest.mark.asyncio
    async def test_travel_preference_mixed_values_and_range(self, test_user_id):
        """Test storing with both values list and budget range"""
        result = await store_travel_preference(
            test_user_id,
            "trip_options",
            values=["Beach", "Mountain", "City"],
            min_value=1500.0,
            max_value=7500.0,
            description="Flexible trip options with budget",
        )

        assert result["status"] == "success"
        pref = result["preference"]
        assert len(pref["values"]) == 3
        assert pref["min_value"] == 1500.0
        assert pref["max_value"] == 7500.0

    @pytest.mark.asyncio
    async def test_retrieve_empty_travel_preferences(self, test_user_id):
        """Test retrieving travel preferences when none exist"""
        result = await retrieve_travel_preference(test_user_id)

        assert result["status"] == "not_found"
        assert result["count"] == 0
        assert result["travel_preferences"] == {}

    @pytest.mark.asyncio
    async def test_delete_all_travel_preferences(self, test_user_id):
        """Test deleting all travel preferences one by one"""
        keys = ["destination", "budget", "style"]

        for key in keys:
            await store_travel_preference(test_user_id, key, value="test")

        # Verify all stored
        result = await retrieve_travel_preference(test_user_id)
        assert result["count"] == 3

        # Delete all
        for key in keys:
            await delete_travel_preference(test_user_id, key)

        # Verify all deleted
        result = await retrieve_travel_preference(test_user_id)
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_travel_preference_special_characters(self, test_user_id):
        """Test storing travel preference with special characters"""
        result = await store_travel_preference(
            test_user_id,
            "destination",
            value="São Paulo, Brazil 🇧🇷",
            description="Love the beaches & culture!",
        )

        assert result["status"] == "success"
        assert "São Paulo" in result["preference"]["value"]
        assert "🇧🇷" in result["preference"]["value"]

    @pytest.mark.asyncio
    async def test_travel_preference_large_values_list(self, test_user_id):
        """Test storing travel preference with large list of values"""
        destinations = [
            "Europe",
            "Asia",
            "Africa",
            "Americas",
            "Oceania",
            "Japan",
            "Thailand",
            "Vietnam",
            "Indonesia",
            "Philippines",
        ]

        result = await store_travel_preference(
            test_user_id, "bucket_list", values=destinations
        )

        assert result["status"] == "success"
        assert len(result["preference"]["values"]) == 10
        assert result["preference"]["values"] == destinations
