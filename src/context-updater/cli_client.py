import argparse
import os
from pathlib import Path
from getpass import getpass

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel


from utils.sanitization import sanitize_user_id
from client_core import MemoryConversation
from llm_client import LLMClient, OpenAIAdapter
from utils.auth import AuthDB

console = Console()

# available cli commands
COMMANDS = ["/clear", "/tool_stats", "/logout", "/register", "/quit"]
CHAT_RETURN_SIGNAL = {"logout": "logout", "quit": "quit", "register": "register"}


# Prompt toolkit style
style = Style.from_dict(
    {
        "completion": "italic dim",
    }
)


class CommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        for cmd in COMMANDS:
            if cmd.startswith(text):
                yield Completion(
                    cmd, start_position=-len(text), style="class:completion"
                )


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

    while True:
        user_id = sanitize_user_id(input("Choose user ID: ").strip())
        password = getpass("Choose password: ").strip()

        if auth.register(user_id, password):
            print("✔ Registration successful. You may now login.")
            break
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

role_label = {
    "user": "🫵 You",
    "assistant": "🤖 Assistant",
    "system": "💻 System",
}
role_border = {
    "user": "green",
    "assistant": "blue",
    "system": "yellow",
}


def interactive_chat(user_id: str):
    """Run interactive chat session with memory"""

    session = PromptSession()
    all_messages = []
    all_messages.append(
        {
            "role": "system",
            "content": f"""\
{'='*60}
Memory Chat - User: {user_id}
{'='*60} 
Type '/quit' to exit, '/clear' to clear history, '/tool_stats' to see recent tool calls, '/logout' to logout, '/register' to create new user""",
        }
    )

    conversation = MemoryConversation(llm_client=llm_client, user_id=user_id.lower())

    while True:
        try:

            console.clear()

            for msg in all_messages:
                title = role_label[msg["role"]]
                console.print(
                    Panel(
                        msg["content"],
                        title=title,
                        expand=True,
                        border_style="green" if msg["role"] == "user" else "blue",
                    )
                )

            user_input = session.prompt("> ", completer=CommandCompleter(), style=style)
            user_input = user_input.strip()

            if user_input in COMMANDS:
                if user_input == "/clear":
                    all_messages = []
                    conversation.clear_history()

                elif user_input == "/tool_stats":
                    all_messages.append(
                        {
                            "role": "system",
                            "content": f"Recently used tools: {", ".join(conversation.tool_usage[-3:][::-1] + ["..."])}",
                        }
                    )

                elif user_input == "/logout":
                    console.print("Logout!", style="bold yellow")
                    return CHAT_RETURN_SIGNAL["logout"]

                elif user_input == "/quit":
                    console.print("Goodbye!", style="bold red")
                    return CHAT_RETURN_SIGNAL["quit"]

                elif user_input == "/register":
                    console.print("Logout and Register a new user!", style="bold red")
                    return CHAT_RETURN_SIGNAL["register"]

                continue

            response = conversation.chat(user_input)

            all_messages.append({"role": "user", "content": user_input})
            all_messages.append({"role": "assistant", "content": response})

        except KeyboardInterrupt:
            console.print("Goodbye!", style="bold red")
            return CHAT_RETURN_SIGNAL["quit"]

        except Exception as e:
            console.print(f"\n❌ Error: {str(e)}", style="bold red")


if __name__ == "__main__":

    global debug_mode

    parser = argparse.ArgumentParser(description="Available parameters")

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

    # Extra commands
    if args.register:
        register_flow()
        # continue to login

    if args.logout:
        logout_flow()
        exit()

    user_id = ensure_authenticated()

    while True:

        chat_return = interactive_chat(user_id)

        if chat_return == CHAT_RETURN_SIGNAL["quit"]:
            break

        elif chat_return == CHAT_RETURN_SIGNAL["logout"]:
            # switching user
            logout_flow()
            user_id = ensure_authenticated()

        elif chat_return == CHAT_RETURN_SIGNAL["register"]:
            logout_flow()
            # create new user then login
            register_flow()
            user_id = ensure_authenticated()
