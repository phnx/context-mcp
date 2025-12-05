# test if model can hallucinate based on MCP data - a costly run
# must start server with IS_MCP_CONTEXT_UPDATER_TEST=true

import sys
from fastmcp import Client
from openai import OpenAI
import pytest
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "context-updater"))

# Set LLM Client
api_key = os.getenv("OPENAI_API_KEY")
llm_client = OpenAI(api_key=api_key)

from client_core import MemoryConversation


# Only run if explicitly enabled
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LLM_TESTS") != "true",
    reason="Skipped by default (costs money). Set RUN_LLM_TESTS=true to run",
)

TEST_DB_FILE = Path("test/test_memories.json")
TEST_DB_LOCK_FILE = Path("test/test_memories.json.lock")


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return "test_user_123"


@pytest.fixture(scope="session", autouse=True)
def setup_llm_test_env():
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


class TestLLMRealHallucination:
    """Test real LLM with actual tool integration"""

    def test_llm_stores_and_retrieves_memory(self, test_user_id):
        """Test that LLM can store and retrieve memory correctly"""
        conversation = MemoryConversation(llm_client=llm_client, user_id=test_user_id)

        # Tell LLM to store information
        response = conversation.chat(
            "My name is Alice and I work as a software engineer"
        )
        assert response  # Should get a response

        # Ask LLM to recall the information
        response = conversation.chat("What is my name and occupation?")

        # Verify LLM correctly recalls the data
        assert "Alice" in response, "LLM should recall name 'Alice'"
        assert "engineer" in response.lower(), "LLM should recall 'engineer'"

    def test_llm_stores_travel_preference(self, test_user_id):
        """Test that LLM correctly stores and recalls travel preferences"""
        conversation = MemoryConversation(llm_client=llm_client, user_id=test_user_id)

        # Tell LLM about travel preference
        response = conversation.chat(
            "My dream destination is Japan. I want to visit Tokyo and experience the culture."
        )
        assert response

        # Ask LLM to recall travel preference
        response = conversation.chat("Where is my dream destination?")

        # Verify LLM correctly recalls
        assert "Japan" in response, "LLM should recall 'Japan'"
        assert "Tokyo" in response or "destination" in response.lower()

    def test_llm_does_not_hallucinate_missing_data(self, test_user_id):
        """Test that LLM doesn't make up data that wasn't stored"""
        conversation = MemoryConversation(llm_client=llm_client, user_id=test_user_id)

        # Don't store any data, just ask
        response = conversation.chat("What is my favorite color?")

        # LLM should indicate it doesn't know, not hallucinate
        lower_response = response.lower()
        lower_response = lower_response.replace("’", "'")

        assert any(
            phrase in lower_response
            for phrase in [
                "don't know",
                "not found",
                "haven't told",
                "no information",
                "not stored",
                "don't have",
            ]
        ), f"LLM should not hallucinate. Response: {response}"

    def test_llm_distinguishes_between_multiple_preferences(self, test_user_id):
        """Test that LLM correctly handles multiple travel preferences"""
        conversation = MemoryConversation(llm_client=llm_client, user_id=test_user_id)

        # Store multiple preferences
        response = conversation.chat(
            "I have a budget of $3000 to $5000 for my trips. I prefer beach destinations."
        )
        assert response

        # Ask about specific preference
        response = conversation.chat("What's my travel budget range?")
        assert "$3000" in response or "3000" in response, "Should recall budget minimum"
        assert "$5000" in response or "5000" in response, "Should recall budget maximum"

        # Ask about another preference
        response = conversation.chat("What type of destinations do I prefer?")
        assert "beach" in response.lower(), "Should recall beach preference"

    def test_llm_updates_memory_correctly(self, test_user_id):
        """Test that LLM correctly updates memory when told new information"""
        conversation = MemoryConversation(llm_client=llm_client, user_id=test_user_id)

        # Store initial information
        response = conversation.chat("My favorite color is blue")
        assert response

        # Verify it was stored
        response = conversation.chat("What's my favorite color?")
        assert "blue" in response.lower()

        # Update the information
        response = conversation.chat("Actually, my favorite color is green")
        assert response

        # Verify it was updated
        response = conversation.chat("What's my favorite color now?")
        assert "green" in response.lower(), "Should recall updated color"
        assert "blue" not in response.lower(), "Should not recall old color"

    def test_llm_handles_complex_travel_preferences(self, test_user_id):
        """Test LLM with complex travel preference data"""
        conversation = MemoryConversation(llm_client=llm_client, user_id=test_user_id)

        # Store complex preference
        response = conversation.chat(
            "I love adventure travel. My preferred destinations are Thailand, Vietnam, and Indonesia. "
            "I prefer to travel in the dry season and my budget is between $2000 and $7000."
        )
        assert response

        # Ask about destinations
        response = conversation.chat("Which countries do I want to visit?")
        assert (
            "Thailand" in response or "Vietnam" in response or "Indonesia" in response
        )

        # Ask about travel style
        response = conversation.chat("What type of travel do I enjoy?")
        assert "adventure" in response.lower()

        # Ask about budget
        response = conversation.chat("What's my travel budget?")
        assert (
            "2000" in response
            or "7000" in response
            or "2,000" in response
            or "7,000" in response
        )

    def test_llm_does_not_confuse_users(self):
        """Test that LLM keeps data separate for different users"""
        user1_id = "test_user_alice"
        user2_id = "test_user_bob"

        # User 1 conversation
        conv1 = MemoryConversation(llm_client=llm_client, user_id=user1_id)
        response = conv1.chat("My name is Alice and I love beaches")
        assert response

        # User 2 conversation
        conv2 = MemoryConversation(llm_client=llm_client, user_id=user2_id)
        response = conv2.chat("My name is Bob and I love mountains")
        assert response

        # Verify User 1 doesn't recall User 2's data
        response = conv1.chat("What's my name?")
        assert "Alice" in response, "User 1 should recall Alice"
        assert "Bob" not in response, "User 1 should not recall Bob"

        # Verify User 2 doesn't recall User 1's data
        response = conv2.chat("What's my name?")
        assert "Bob" in response, "User 2 should recall Bob"
        assert "Alice" not in response, "User 2 should not recall Alice"

    def test_llm_recalls_multiple_memories(self, test_user_id):
        """Test that LLM can recall multiple stored memories"""
        conversation = MemoryConversation(llm_client=llm_client, user_id=test_user_id)

        # Store multiple pieces of information
        conversation.chat("My name is Charlie")
        conversation.chat("I'm a data scientist")
        conversation.chat("I live in San Francisco")
        conversation.chat("My favorite hobby is hiking")

        # Ask for all information
        response = conversation.chat("Tell me everything you know about me")

        # Verify multiple pieces are recalled
        assert "Charlie" in response, "Should recall name"
        assert "data scientist" in response.lower(), "Should recall occupation"
        assert "San Francisco" in response, "Should recall location"
        assert "hiking" in response.lower(), "Should recall hobby"

    @pytest.mark.order(0)
    def test_llm_empty_database_no_hallucination(self, test_user_id):
        """Test that LLM doesn't hallucinate when database is empty"""
        conversation = MemoryConversation(llm_client=llm_client, user_id=test_user_id)

        # Ask multiple questions without storing anything
        questions = [
            "What's my name?",
            "Where do I live?",
            "What's my favorite food?",
            "Tell me about my travel preferences",
        ]

        for question in questions:
            response = conversation.chat(question)
            lower_response = response.lower()
            lower_response = lower_response.replace("’", "'")

            # Should indicate no information, not hallucinate
            assert any(
                phrase in lower_response
                for phrase in [
                    "don't know",
                    "not found",
                    "haven't told",
                    "no information",
                    "not stored",
                    "i don't have",
                    "haven't shared",
                    "don't have",
                ]
            ), f"LLM hallucinated for '{question}'. Response: {response}"
