import logging
import sys
from fastmcp import FastMCP

from server_database import load_database
from tools import register_all_tools

# Initialize FastMCP server
mcp = FastMCP("user-travel-memory-server")

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)

# logger.info(f"Tool called: {name}")
# ============================================================================
# MCP Tools
# ============================================================================

register_all_tools(mcp)


@mcp.tool()
def list_users() -> dict:
    """
    List user's stored memory counts.

    Returns:
        List of user's memory count
    """
    database = load_database()

    # redact user_id
    users = [
        {"user_id": "NA", "memory_count": len(user_data.memories)}
        for _, user_data in database.items()
    ]

    logger.debug("tool calling: list_users")

    return {"status": "success", "total_users": len(users), "users": users}


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run in HTTP mode on port 8000
    mcp.run(transport="http", host="0.0.0.0", port=8000)
