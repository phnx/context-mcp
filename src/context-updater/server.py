import logging
import sys

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from server_database import get_database_overview, load_database
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
    database = load_database()
    users = [
        {"user_id": "NA", "memory_count": len(user_data.memories)}
        for _, user_data in database.items()
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
@mcp.custom_route("/user_overview", methods=["GET"])
async def user_overview(request: Request) -> JSONResponse:

    try:
        user_overview = get_database_overview()

        logger.debug("normal endpoint calling: user_overview")

        return JSONResponse(user_overview, 200)
    except Exception:
        return JSONResponse({"status": "error fetching user overview"}, 500)


# --------------------------------------------------------
# Server entry point
# --------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
