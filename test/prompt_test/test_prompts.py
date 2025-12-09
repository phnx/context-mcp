# test prompt variants
import os
import json
from pathlib import Path
import sys

os.environ["IS_MCP_CONTEXT_UPDATER_TEST"] = "true"

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "context-updater"))
from llm_client import LLMClient, OpenAIAdapter

# Set LLM Client
llm_client: LLMClient = OpenAIAdapter(
    model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY")
)

from client_core import MemoryConversation


def load_system_prompt(variant_file: str, user_id: str) -> str:
    prompt_path = Path(variant_file)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {variant_file}")

    with prompt_path.open("r", encoding="utf-8") as f:
        system_prompt = f.read()

    # Replace {user_id} placeholder
    system_prompt = system_prompt.replace("{user_id}", user_id)

    return system_prompt


TEST_DB_FILE = Path("test/test_memories.db")
TEST_ANALYTIC_TOOL_DB_FILE = Path("test/test_tool_analytic.db")
USER_ID = "charlie"

conversation_scenario = [
    [
        {
            "message": "Hi, I'm planning a trip soon, can you help?",
            "expected_keywords": ["trip", "help", "travel"],
        },
        {
            "message": "I really enjoyed my last trip to Tokyo, Japan. Can you remember that?",
            "expected_keywords": ["remember", "Tokyo", "Japan", "memory"],
        },
        {
            "message": "Also, I love tropical beaches, especially in Southeast Asia.",
            "expected_keywords": [
                "beaches",
                "tropical",
                "Southeast Asia",
                "preference",
            ],
        },
        {
            "message": "I want to find flights from Bangkok to Bali for January 5th, 2026.",
            "expected_keywords": ["flights", "Bangkok", "Bali", "January", "search"],
        },
        {
            "message": "What hotels would you recommend near Seminyak Beach in Bali?",
            "expected_keywords": ["hotels", "Seminyak", "Bali", "recommend"],
        },
        {
            "message": "Actually, can you book the flight from Bangkok to Bali on January 5th, 2026 that you found yesterday?",
            "expected_keywords": ["book", "flight", "Bangkok", "Bali", "January"],
        },
        {
            "message": "And please reserve a hotel in Bali for 3 nights near the beach, checking in on January 5th, 2026 and checking out on January 8th, 2026.",
            "expected_keywords": [
                "book",
                "hotel",
                "Bali",
                "January",
                "nights",
                "check",
            ],
        },
        {
            "message": "Can you remind me what my favorite travel destinations are?",
            "expected_keywords": ["remind", "favorite", "destinations", "memory"],
        },
        {
            "message": "By the way, I prefer window seats on planes.",
            "expected_keywords": ["preference", "window", "seat"],
        },
        {
            "message": "Can you store that preference?",
            "expected_keywords": ["store", "preference", "remember"],
        },
        {
            "message": "I heard about a new trip to Iceland. Can you find flights from Bangkok to Reykjavik for February 10th, 2026?",
            "expected_keywords": [
                "flights",
                "Bangkok",
                "Reykjavik",
                "Iceland",
                "search",
                "February",
            ],
        },
        {
            "message": "Forget about my Iceland interest, I changed my mind.",
            "expected_keywords": ["forget", "Iceland", "remove", "memory"],
        },
        {
            "message": "Who else did I mention before about trips? (This is to test memory recall.)",
            "expected_keywords": ["who", "mentioned", "recall", "memory"],
        },
        {
            "message": "Can you summarize all my stored travel preferences and memories for me?",
            "expected_keywords": ["summary", "preferences", "memories", "recap"],
        },
        {
            "message": "I'm also thinking of a business trip to Singapore next month. Can you find flights from Bangkok to Singapore on March 12th, 2026 and hotels in downtown Singapore?",
            "expected_keywords": [
                "flights",
                "hotels",
                "Singapore",
                "search",
                "Bangkok",
                "March",
            ],
        },
        {
            "message": "Suggest flights and hotels for Singapore, but don't book anything yet.",
            "expected_keywords": ["suggest", "flights", "hotels", "Singapore"],
        },
        {
            "message": "I think I want to book only the hotel in Singapore. Please book a hotel from March 12th-15th, 2026 in downtown Singapore. Do not book any flights.",
            "expected_keywords": ["book", "hotel", "Singapore", "March", "reservation"],
        },
        {
            "message": "Can you update my seat preference to prefer aisle seats now?",
            "expected_keywords": ["update", "preference", "aisle", "seat"],
        },
        {
            "message": "Thank you! Can you recall all my current flight bookings and hotel reservations?",
            "expected_keywords": [
                "recall",
                "bookings",
                "reservations",
                "flight",
                "hotel",
            ],
        },
        {
            "message": "Actually, delete my memory about the Tokyo trip.",
            "expected_keywords": ["delete", "Tokyo", "memory", "remove"],
        },
        {
            "message": "Remind me of all my travel preferences one last time.",
            "expected_keywords": ["remind", "preferences", "travel"],
        },
    ],
    [
        {
            "message": "Hello! I'm planning a family vacation soon, can you help me get started?",
            "expected_keywords": ["family", "vacation", "help", "trip"],
        },
        {
            "message": "I took my kids to Osaka Disneyland last year. Can you store that memory?",
            "expected_keywords": ["Osaka", "Disneyland", "kids", "memory", "store"],
        },
        {
            "message": "We love theme parks and big aquariums.",
            "expected_keywords": ["theme park", "aquarium", "preference", "family"],
        },
        {
            "message": "Find flights from Bangkok to Seoul on April 3rd, 2026 for 4 passengers.",
            "expected_keywords": ["flights", "Bangkok", "Seoul", "April", "search"],
        },
        {
            "message": "Also, check hotels in Seoul near Myeongdong for April 3rd to April 7th, 2026.",
            "expected_keywords": ["hotels", "Seoul", "Myeongdong", "April", "search"],
        },
        {
            "message": "Please book that Seoul flight for all 4 of us on April 3rd, 2026.",
            "expected_keywords": ["book", "flight", "Seoul", "April", "passengers"],
        },
        {
            "message": "And book a hotel in Myeongdong from April 3rd to April 7th, 2026.",
            "expected_keywords": ["book", "hotel", "Myeongdong", "April"],
        },
        {
            "message": "What memories do you have stored about my past trips?",
            "expected_keywords": ["memories", "recall", "trips", "past"],
        },
        {
            "message": "By the way, I prefer hotels with breakfast included.",
            "expected_keywords": ["preference", "breakfast", "hotel"],
        },
        {
            "message": "Can you store this hotel preference?",
            "expected_keywords": ["store", "preference"],
        },
        {
            "message": "I might also be traveling to Sydney for work. Find flights from Bangkok to Sydney on May 12th, 2026.",
            "expected_keywords": ["flights", "Bangkok", "Sydney", "search", "May"],
        },
        {
            "message": "Forget my interest in Sydney for now.",
            "expected_keywords": ["forget", "Sydney", "remove"],
        },
        {
            "message": "What did I say earlier about theme parks?",
            "expected_keywords": ["theme park", "recall", "memory"],
        },
        {
            "message": "Summarize all my saved preferences so far.",
            "expected_keywords": ["summary", "preferences", "recap"],
        },
        {
            "message": "I want to compare flights to Hong Kong for June 1st, 2026 from Bangkok.",
            "expected_keywords": ["flights", "Hong Kong", "Bangkok", "June", "search"],
        },
        {
            "message": "Show me hotel suggestions in Hong Kong near Tsim Sha Tsui.",
            "expected_keywords": [
                "hotels",
                "Hong Kong",
                "Tsim Sha Tsui",
                "suggestions",
            ],
        },
        {
            "message": "Book only the hotel in Tsim Sha Tsui for June 1st-4th, 2026.",
            "expected_keywords": ["book", "hotel", "Hong Kong", "June"],
        },
        {
            "message": "Update my preference: I now prefer morning flights.",
            "expected_keywords": ["update", "preference", "morning", "flight"],
        },
        {
            "message": "What flights and hotels have I booked so far?",
            "expected_keywords": ["recall", "bookings", "reservations"],
        },
        {
            "message": "Delete my memory about the Osaka Disneyland trip.",
            "expected_keywords": ["delete", "Osaka", "memory"],
        },
    ],
    [
        {
            "message": "Hi, I travel a lot for work. Can you assist me with planning?",
            "expected_keywords": ["travel", "work", "assist", "planning"],
        },
        {
            "message": "I really enjoyed my conference trip to Berlin last year. Store that memory.",
            "expected_keywords": ["Berlin", "conference", "memory", "store"],
        },
        {
            "message": "I like cities with good public transport and walkable downtowns.",
            "expected_keywords": [
                "public transport",
                "walkable",
                "downtown",
                "preference",
            ],
        },
        {
            "message": "Find flights from Bangkok to London on September 14th, 2026.",
            "expected_keywords": ["flights", "Bangkok", "London", "September"],
        },
        {
            "message": "Check hotels in London near Waterloo Station for September 14-18, 2026.",
            "expected_keywords": ["hotels", "London", "Waterloo", "September"],
        },
        {
            "message": "Please book the London flight for September 14th, 2026.",
            "expected_keywords": ["book", "flight", "London", "September"],
        },
        {
            "message": "And book the hotel near Waterloo Station for the same dates.",
            "expected_keywords": ["book", "hotel", "London", "Waterloo"],
        },
        {
            "message": "Can you remind me what preferences you've saved about me?",
            "expected_keywords": ["preferences", "recall", "saved"],
        },
        {
            "message": "I prefer vegetarian meal options on flights.",
            "expected_keywords": ["vegetarian", "meal", "preference"],
        },
        {
            "message": "Please save that preference.",
            "expected_keywords": ["store", "save", "preference"],
        },
        {
            "message": "Find flights from Bangkok to Vancouver on October 20th, 2026.",
            "expected_keywords": ["flights", "Bangkok", "Vancouver", "October"],
        },
        {
            "message": "Actually, never mind. Forget the Vancouver plan.",
            "expected_keywords": ["forget", "Vancouver", "remove"],
        },
        {
            "message": "What do you remember about my Berlin trip?",
            "expected_keywords": ["Berlin", "recall", "memory"],
        },
        {
            "message": "Summarize all my travel preferences and memories.",
            "expected_keywords": ["summary", "preferences", "memories"],
        },
        {
            "message": "Check flights from Bangkok to Dubai for November 5th, 2026.",
            "expected_keywords": ["flights", "Bangkok", "Dubai", "November"],
        },
        {
            "message": "Show hotels in Dubai near Marina District for November 5-8, 2026, but don't book anything.",
            "expected_keywords": ["hotels", "Dubai", "Marina", "suggest"],
        },
        {
            "message": "Now book the hotel in Dubai for November 5-8, 2026.",
            "expected_keywords": ["book", "hotel", "Dubai", "November"],
        },
        {
            "message": "Update my preference: I now prefer late-night flights.",
            "expected_keywords": ["update", "preference", "late-night", "flight"],
        },
        {
            "message": "What bookings do I currently have?",
            "expected_keywords": ["bookings", "reservations", "recall"],
        },
        {
            "message": "Delete the memory about my Berlin trip.",
            "expected_keywords": ["delete", "Berlin", "memory"],
        },
    ],
]

# Example usage
if __name__ == "__main__":

    prompt_list = [
        "test/prompt_test/prompt/variant_1.md",
        "test/prompt_test/prompt/variant_2.md",
        "test/prompt_test/prompt/variant_3.md",
        "test/prompt_test/prompt/variant_4.md",
        "test/prompt_test/prompt/variant_5.md",
    ]

    for prompt_file in prompt_list:
        # delete DB files
        if TEST_DB_FILE.exists():
            TEST_DB_FILE.unlink()

        if TEST_ANALYTIC_TOOL_DB_FILE.exists():
            TEST_ANALYTIC_TOOL_DB_FILE.unlink()

        print("loading ", prompt_file)

        system_prompt = load_system_prompt(prompt_file, USER_ID)
        # inject system prompt
        conversation = MemoryConversation(
            llm_client=llm_client, user_id=USER_ID, system_prompt=system_prompt
        )

        # conversation loop
        result = {
            "hit": 0,
            "miss": 0,
        }
        for scenario in conversation_scenario:
            print("new scenario")
            for convo in scenario:

                print("msg:", convo["message"])
                resp = conversation.chat(convo["message"])
                print("resp:", resp)

                resp_lower = resp.lower()

                if any(kw.lower() in resp_lower for kw in convo["expected_keywords"]):
                    result["hit"] += 1
                else:
                    result["miss"] += 1

        # get tool analytics
        variant_name = prompt_file.split("/")[-1].split(".")[0]
        tool_stats = conversation.tool_counter.get_all_stats()
        print("tool_stats", tool_stats)

        tool_output_path = Path(
            f"test/prompt_test/test_result/{variant_name}_tool.json"
        )
        result_output_path = Path(
            f"test/prompt_test/test_result/{variant_name}_result.json"
        )
        with tool_output_path.open("w", encoding="utf-8") as f:
            json.dump(tool_stats, f, indent=2, ensure_ascii=False)

        with result_output_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # delete DB files
        if TEST_DB_FILE.exists():
            TEST_DB_FILE.unlink()

        if TEST_ANALYTIC_TOOL_DB_FILE.exists():
            TEST_ANALYTIC_TOOL_DB_FILE.unlink()

    # unset test vars
    os.environ.pop("IS_MCP_CONTEXT_UPDATER_TEST", None)
