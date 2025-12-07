from fastmcp import FastMCP
from .memory_tools import (
    store_memory,
    retrieve_memory,
    update_memory,
    delete_memory,
)
from .travel_preference_tools import (
    store_travel_preference,
    retrieve_travel_preference,
    update_travel_preference,
    delete_travel_preference,
)
from .external_tools import book_a_flight, book_a_hotel, lookup_flights, lookup_hotels


def register_all_tools(mcp: FastMCP):
    """Register all tools with FastMCP server"""

    # Memory tools
    mcp.tool()(store_memory)
    mcp.tool()(retrieve_memory)
    mcp.tool()(update_memory)
    mcp.tool()(delete_memory)

    # Travel tools
    mcp.tool()(store_travel_preference)
    mcp.tool()(retrieve_travel_preference)
    mcp.tool()(update_travel_preference)
    mcp.tool()(delete_travel_preference)

    # External tools
    mcp.tool()(lookup_flights)
    mcp.tool()(lookup_hotels)
    mcp.tool()(book_a_hotel)
    mcp.tool()(book_a_flight)
