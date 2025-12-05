# web_gateway.py
import asyncio
import json
import logging
import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI


# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.sanitization import sanitize_user_id
from client_core import MemoryConversation

# Initialize OpenAI client
llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Store conversations
# NOTE this should be moved to in-memory database for performance
conversations = {}

# ============================================================================
# Models
# ============================================================================


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ClearRequest(BaseModel):
    user_id: str


# ============================================================================
# API Endpoints
# ============================================================================


def create_conversation(user_id: str) -> MemoryConversation:
    """Create conversation in thread pool to avoid event loop issues"""
    return MemoryConversation(
        llm_client=llm_client,
        user_id=user_id,
        debug_mode=False,
    )


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Send message and get response"""
    try:
        logger.info("step 1")
        user_id = sanitize_user_id(request.user_id)
        logger.info("step 2")
        # Create conversation in thread pool if needed
        if user_id not in conversations:
            conversations[user_id] = await asyncio.to_thread(
                create_conversation, user_id
            )
        logger.info("step 3")
        conversation = conversations[user_id]
        logger.info("step 4")
        response = await asyncio.to_thread(conversation.chat, request.message)

        return {"response": response, "user_id": user_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clear")
async def clear_history(request: ClearRequest):
    """Clear conversation history"""
    try:
        user_id = sanitize_user_id(request.user_id)

        if user_id in conversations:
            await asyncio.to_thread(conversations[user_id].clear_history)

        return {"status": "cleared", "user_id": user_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/api/analytics")
async def get_analytics():
    """Read and serve analytics data from JSON file"""
    try:
        json_path = "database/tool_analytic.json"

        if not os.path.exists(json_path):
            raise HTTPException(status_code=404, detail="Analytics file not found")

        with open(json_path, "r") as f:
            data = json.load(f)

        return data

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Serve Frontend
# ============================================================================


@app.get("/")
async def serve_frontend():
    return FileResponse("src/context-updater/web-client/index.html")


app.mount(
    "/static", StaticFiles(directory="src/context-updater/web-client"), name="static"
)

# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "__main__:app", host="0.0.0.0", port=8001, reload=True, log_level="debug"
    )
