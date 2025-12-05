import asyncio
import json
import os
from typing import Optional

from fastmcp import Client, FastMCP
from openai import OpenAI

from utils.sanitization import sanitize_tool_input, sanitize_user_message
from utils.tool_analytic import ToolCounter
from utils.token_counter import count_tokens

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
MODEL = os.getenv("OPENAI_MODEL")

# ============================================================================
# Tool Definitions for OpenAI
# ============================================================================

# example of tool definition format
# TOOLS = [
#     {
#         "type": "function",
#         "function": {
#             "name": "store_memory",
#             "description": "Store or update a memory for a user. Use this when the user wants to save information about themselves.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "user_id": {
#                         "type": "string",
#                         "description": "Unique identifier for the user",
#                     },
#                     "key": {
#                         "type": "string",
#                         "description": "Memory key (e.g., 'favourite_color', 'name', 'occupation')",
#                     },
#                     "value": {"type": "string", "description": "Memory value to store"},
#                 },
#                 "required": ["user_id", "key", "value"],
#             },
#         },
#     },
# ]


async def get_tools_from_mcp(mcp_client: FastMCP) -> list:
    """Fetch tool definitions from MCP server"""
    try:
        async with mcp_client:
            tools_response = await mcp_client.list_tools()

            # Convert MCP tools to OpenAI format
            tools = []
            for tool in tools_response:
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,
                        },
                    }
                )
            return tools
    except Exception as e:
        print(f"Error fetching tools: {str(e)}")
        return []


# ============================================================================
# MCP Tool Execution
# ============================================================================


async def call_mcp_tool(mcp_client: Client, tool_name: str, **kwargs) -> dict:
    """Call a tool on the MCP server using FastMCP Client"""
    try:
        async with mcp_client:
            result = await mcp_client.call_tool(tool_name, kwargs)
            # Extract content from CallToolResult
            if hasattr(result, "content"):
                content = result.content[0].text if result.content else "{}"
                return json.loads(content) if isinstance(content, str) else content

            return {"status": "success", "result": str(result)}

    except Exception as e:
        return {"status": "error", "message": f"MCP Server error: {str(e)}"}


def process_tool_call(mcp_client: Client, tool_name: str, tool_input: dict) -> str:
    """Process a tool call from OpenAI and return result as string"""

    tool_input = sanitize_tool_input(tool_input)

    result = asyncio.run(call_mcp_tool(mcp_client, tool_name, **tool_input))
    return json.dumps(result)


# ============================================================================
# Conversation with Memory
# ============================================================================


class MemoryConversation:
    """Manage conversation with memory context"""

    def __init__(
        self,
        llm_client: OpenAI,
        user_id: str,
        system_prompt: Optional[str] = None,
        debug_mode: bool = False,
        max_history_size: int = 200,
    ):

        self.user_id = user_id
        self.conversation_history = []  # always trimmed under max_history_size
        self.llm_client = llm_client
        self.mcp_client = Client(MCP_SERVER_URL)
        self.debug_mode = debug_mode
        self.max_history_size = max_history_size  # Size cap

        self.tools = asyncio.run(get_tools_from_mcp(self.mcp_client))
        self.tool_counter = ToolCounter()

        # Default system prompt
        if system_prompt is None:
            system_prompt = f"""You are a helpful assistant with memory capabilities. 
You can store and retrieve information about the user (ID: {user_id}).

Start by looking up existing user information with retrieve_memory and retrieve_travel_preferences tools.

When a user tells you something about travel preference, e.g., dream destination or favorite trips, use store_travel_preference tool to save it.
When you need to recall user's travel preferences, use the retrieve_travel_preference tool.

When a user tells you something else about themselves, use the store_memory tool to save it.
When you need to recall general information about the user, use the retrieve_memory tool.

Delete data using delete_travel_preference and delete_memory ONLY upon user's request.

Make sure the data of each user is CONFIDENTIAL to the owner.
Always be friendly and personable, referencing stored preferences and memories when relevant."""

        self.system_prompt = system_prompt

    def _trim_history(self) -> None:
        """Trim conversation history to max_history_size, preserving system context"""
        if len(self.conversation_history) > self.max_history_size:
            # Keep only the last max_history_size messages
            self.conversation_history = self.conversation_history[
                -self.max_history_size :
            ]

    def chat(self, user_message: str) -> str:
        """
        Send a message and get a response with memory context.

        Args:
            user_message: User's input message

        Returns:
            Assistant's response
        """

        user_message = sanitize_user_message(user_message)

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Call OpenAI with tools
        response = self.llm_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history,
            ],
            tools=self.tools,
            tool_choice="auto",
        )

        # Process response
        assistant_message = response.choices[0].message

        # Handle tool calls
        while assistant_message.tool_calls:
            # Add assistant's response to history
            self.conversation_history.append(
                {"role": "assistant", "content": assistant_message.content or ""}
            )

            # Process each tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)

                if self.debug_mode:
                    print(f"\n🔧 Calling tool: {tool_name}")
                    print(f"   Input: {json.dumps(tool_input, indent=2)}")

                result = process_tool_call(self.mcp_client, tool_name, tool_input)

                if self.debug_mode:
                    print(f"   Result: {result}")

                # Add tool result as user message
                self.conversation_history.append(
                    {
                        "role": "user",
                        "content": f"Tool '{tool_name}' returned: {result}",
                    }
                )

                # keep tool statistics
                tool_input_raw = tool_call.function.arguments
                tool_input_tokens = count_tokens(tool_input_raw)

                tool_output_raw = json.dumps(result)
                tool_output_tokens = count_tokens(tool_output_raw)
                self.tool_counter.increment_tool(
                    tool_name,
                    calls=1,
                    tokens_in=tool_input_tokens,
                    tokens_out=tool_output_tokens,
                )

            # Get next response from OpenAI
            response = self.llm_client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history,
                ],
                tools=self.tools,
                tool_choice="auto",
            )

            assistant_message = response.choices[0].message

        # Extract final text response
        final_response = assistant_message.content or "No response generated"

        # Add to history
        self.conversation_history.append(
            {"role": "assistant", "content": final_response}
        )

        # Trim history after each chat
        self._trim_history()

        return final_response

    def get_history(self) -> list:
        """Get conversation history"""
        return self.conversation_history

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []
