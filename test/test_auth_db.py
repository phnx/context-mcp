# test_auth_db_secure.py
import os
from pathlib import Path
import sys
import time

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "context-updater"))

from utils.auth import AuthDB

# Enable test mode
os.environ["IS_MCP_CONTEXT_UPDATER_TEST"] = "true"


@pytest.fixture(scope="function")
def auth_db():
    # Ensure fresh DB for each test
    db = AuthDB()
    yield db
    # Clean up the test DB file after test
    db.conn.close()
    test_db = "test/auth_secure.db"
    try:
        os.remove(test_db)
    except FileNotFoundError:
        pass


def test_register(auth_db):
    # Register new user
    assert auth_db.register("alice", "password123") is True
    # Cannot register the same user again
    assert auth_db.register("alice", "password123") is False


def test_login_and_authenticate(auth_db):
    auth_db.register("bob", "secret")
    token = auth_db.login("bob", "secret")
    assert token is not None
    # Authenticate returns correct user_id
    assert auth_db.authenticate(token) == "bob"
    # Wrong password returns None
    assert auth_db.login("bob", "wrong") is None
    # Non-existent user returns None
    assert auth_db.login("nonexist", "pwd") is None


def test_token_expiry(auth_db):
    auth_db.register("carol", "pwd")
    token = auth_db.login("carol", "pwd")
    assert auth_db.authenticate(token) == "carol"
    # Manually expire token
    c = auth_db.conn.cursor()
    c.execute(
        "UPDATE tokens SET expires_at = ? WHERE token = ?", (time.time() - 1, token)
    )
    auth_db.conn.commit()
    assert auth_db.authenticate(token) is None  # expired token returns None


def test_revoke_token(auth_db):
    auth_db.register("dave", "pwd")
    token = auth_db.login("dave", "pwd")
    assert auth_db.authenticate(token) == "dave"
    auth_db.revoke_token(token)
    assert auth_db.authenticate(token) is None


def test_multiple_tokens(auth_db):
    auth_db.register("eve", "pwd")
    token1 = auth_db.login("eve", "pwd")
    token2 = auth_db.login("eve", "pwd")
    assert token1 != token2
    # Both tokens should authenticate correctly
    assert auth_db.authenticate(token1) == "eve"
    assert auth_db.authenticate(token2) == "eve"
    # Revoke one token, the other should still work
    auth_db.revoke_token(token1)
    assert auth_db.authenticate(token1) is None
    assert auth_db.authenticate(token2) == "eve"
