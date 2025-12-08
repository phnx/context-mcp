# auth_db_secure.py
import os
import sqlite3
import time
import secrets

from passlib.context import CryptContext

TOKEN_EXPIRATION = 3600  # 1 hour

DB_FILE = "database/auth_secure.db"
TEST_DB_FILE = "test/auth_secure.db"


# Password hashing context (Argon2 preferred, fallback to bcrypt)
pwd_ctx = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def _get_db_path() -> str:
    is_test = os.environ.get("IS_MCP_CONTEXT_UPDATER_TEST", "false").lower() == "true"
    return TEST_DB_FILE if is_test else DB_FILE


class AuthDB:
    def __init__(self):
        self.conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()
        # Users table
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at REAL NOT NULL
        )
        """
        )
        # Tokens table
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        """
        )
        self.conn.commit()

    # -------------------
    # Core functions
    # -------------------
    def register(self, user_id: str, password: str) -> bool:
        c = self.conn.cursor()
        c.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone():
            return False  # user exists

        password_hash = pwd_ctx.hash(password)
        c.execute(
            "INSERT INTO users (user_id, password_hash, created_at) VALUES (?, ?, ?)",
            (user_id, password_hash, time.time()),
        )
        self.conn.commit()
        return True

    def login(self, user_id: str, password: str) -> str | None:
        c = self.conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if not row or not pwd_ctx.verify(password, row[0]):
            return None
        token = secrets.token_urlsafe(32)
        expires_at = time.time() + TOKEN_EXPIRATION
        c.execute(
            "INSERT INTO tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at),
        )
        self.conn.commit()
        return token

    def authenticate(self, token: str) -> str | None:
        c = self.conn.cursor()
        c.execute("SELECT user_id, expires_at FROM tokens WHERE token = ?", (token,))
        row = c.fetchone()
        if not row:
            return None
        user_id, expires_at = row
        if expires_at < time.time():
            # Token expired
            c.execute("DELETE FROM tokens WHERE token = ?", (token,))
            self.conn.commit()
            return None
        return user_id

    def revoke_token(self, token: str):
        c = self.conn.cursor()
        c.execute("DELETE FROM tokens WHERE token = ?", (token,))
        self.conn.commit()
