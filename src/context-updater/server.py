import logging
import sys

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from server_database import get_database_overview, get_all_users
from tools import register_all_tools


mcp = FastMCP("user-travel-memory-server")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

register_all_tools(mcp)


@mcp.tool()
def list_users() -> dict:
    """
    List anonymous users with their memory and travel preference counts.
    """
    users_data = (
        get_all_users()
    )  # returns dict[user_id] = {"memory_count": int, "travel_pref_count": int}

    users = [
        {
            "user_id": "NA",
            "memory_count": data.get("memory_count", 0),
            "travel_pref_count": data.get("travel_pref_count", 0),
        }
        for _, data in users_data.items()
    ]

    logger.debug("tool calling: list_users")

    return {
        "status": "success",
        "total_users": len(users),
        "users": users,
    }


# --------------------------------------------------------
# Normal HTTP endpoints
# --------------------------------------------------------


# observing user base, not exposing user data
@mcp.custom_route("/memory_overview", methods=["GET"])
async def memory_overview(request: Request) -> JSONResponse:

    try:
        memory_overview = get_database_overview()

        logger.debug("normal endpoint calling: memory_overview")

        return JSONResponse(memory_overview, 200)
    except Exception:
        return JSONResponse({"status": "error fetching user overview"}, 500)


# --------------------------------------------------------
# Server entry point
# --------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
