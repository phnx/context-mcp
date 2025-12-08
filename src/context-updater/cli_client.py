import argparse
import os
from pathlib import Path
from getpass import getpass

from utils.sanitization import sanitize_user_id
from client_core import MemoryConversation
from llm_client import LLMClient, OpenAIAdapter
from utils.auth import AuthDB


# Initialize LLM client
llm_client: LLMClient = OpenAIAdapter(
    model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY")
)


TOKEN_FILE = Path.home() / ".context_mcp_app_token"

auth = AuthDB()


# -------------------------------
# Token handling helpers
# -------------------------------
def save_token(token: str):
    TOKEN_FILE.write_text(token)


def load_token() -> str | None:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return None


def clear_token():
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


# -------------------------------
# Authentication flow
# -------------------------------
def ensure_authenticated() -> str:
    """Ensure the user is logged in. If token exists, reuse it."""
    token = load_token()

    if token:
        user_id = auth.authenticate(token)
        if user_id:
            print(f"✔ Logged in as {user_id}")
            return user_id

        print("⚠ Your session expired. Please login again.")
        clear_token()

    # Prompt user to login manually
    while True:
        print("\n=== Login Required ===")
        user_id = sanitize_user_id(input("User ID: ").strip())
        password = getpass("Password: ").strip()

        token = auth.login(user_id, password)
        if token:
            save_token(token)
            print(f"✔ Login successful! Welcome {user_id}.")
            return user_id

        print("❌ Invalid credentials. Please try again.\n")


def register_flow():
    print("\n=== Register New Account ===")
    user_id = sanitize_user_id(input("Choose user ID: ").strip())
    password = getpass("Choose password: ").strip()

    if auth.register(user_id, password):
        print("✔ Registration successful. You may now login.")
    else:
        print("❌ User already exists.")


def logout_flow():
    token = load_token()
    if token:
        auth.revoke_token(token)
        clear_token()
    print("✔ Logged out.")


# ============================================================================
# Interactive CLI with OpenAI
# ============================================================================


def interactive_chat(user_id: str):
    """Run interactive chat session with memory"""
    print(f"\n{'='*60}")
    print(f"Memory Chat - User: {user_id}")
    print(f"{'='*60}")
    print("Type 'quit' to exit, 'clear' to clear history\n")

    conversation = MemoryConversation(
        llm_client=llm_client,
        user_id=user_id.lower(),
        debug_mode=debug_mode,
    )

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("Goodbye!")
                break

            if user_input.lower() == "clear":
                conversation.clear_history()
                print("✓ Conversation history cleared\n")
                continue

            print("\n🤖 Assistant: ", end="", flush=True)
            response = conversation.chat(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break

        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":

    global debug_mode

    parser = argparse.ArgumentParser(description="Available parameters")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode to display tool callings",
    )

    parser.add_argument(
        "--register",
        action="store_true",
        help="Register a new account",
    )
    parser.add_argument(
        "--logout",
        action="store_true",
        help="Logout and clear token",
    )

    args = parser.parse_args()
    debug_mode = args.debug

    # Extra commands
    if args.register:
        register_flow()
        exit()

    if args.logout:
        logout_flow()
        exit()

    user_id = ensure_authenticated()
    interactive_chat(user_id)
