import argparse
import os

from openai import OpenAI

from utils.sanitization import sanitize_user_id
from client_core import MemoryConversation


# Initialize OpenAI client
llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
        user_id=user_id,
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
    args = parser.parse_args()
    debug_mode = args.debug

    user_id = sanitize_user_id(input("Enter user ID: ").strip())

    interactive_chat(user_id)
