# web_gateway.py
import asyncio
import json
import logging
import os
import sys
import time

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.sanitization import sanitize_user_id
from client_core import MemoryConversation
from llm_client import LLMClient, OpenAIAdapter
from utils.tool_analytic import ToolCounter
from utils.auth import AuthDB  # <-- ensure this is imported

# Initialize LLM client
llm_client: LLMClient = OpenAIAdapter(
    model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY")
)

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)

app = FastAPI()
auth_db = AuthDB()

rate_limit = {}
MAX_CALLS = 20
WINDOW = 60  # seconds


@app.middleware("http")
async def simple_rate_limit(request: Request, call_next):
    ip = request.client.host
    now = time.time()

    if ip not in rate_limit:
        rate_limit[ip] = []

    # Remove old timestamps
    rate_limit[ip] = [t for t in rate_limit[ip] if now - t < WINDOW]

    if len(rate_limit[ip]) >= MAX_CALLS:
        return JSONResponse(
            status_code=429,
            content={
                "status": "error",
                "message": "Too Many Requests. Please slow down.",
            },
        )

    rate_limit[ip].append(now)

    return await call_next(request)


# Store conversations
# NOTE this should be moved to in-memory database for performance
conversations = {}

# ============================================================================
# Models
# ============================================================================


class ChatRequest(BaseModel):
    message: str


class ClearRequest(BaseModel):
    user_id: str


class AuthRequest(BaseModel):
    user_id: str
    password: str


class TokenRequest(BaseModel):
    token: str


# ============================================================================
# Helper Functions
# ============================================================================


def require_auth(token: str | None):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    user_id = auth_db.authenticate(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


def create_conversation(user_id: str) -> MemoryConversation:
    """Create conversation in thread pool to avoid event loop issues"""
    return MemoryConversation(
        llm_client=llm_client,
        user_id=user_id,
        debug_mode=False,
    )


# ============================================================================
# Auth Endpoints
# ============================================================================


@app.post("/api/register")
async def register(req: AuthRequest):
    user_id = req.user_id.strip().lower()
    password = req.password.strip()

    # Register user (returns only True/False)
    ok = auth_db.register(user_id, password)
    if not ok:
        return {
            "status": "error",
            "message": "Failed to create account: user already exists",
        }

    # Auto-login (returns token or None)
    token = auth_db.login(user_id, password)
    if not token:
        return {"status": "error", "message": "Failed to authenticate new account"}

    return {"status": "ok", "user_id": user_id, "token": token}


@app.post("/api/login")
async def login(req: AuthRequest):
    user_id = req.user_id.strip().lower()
    password = req.password.strip()

    token = auth_db.login(user_id, password)

    if not token:
        return {"status": "error", "message": "Invalid username or password"}

    return {"status": "ok", "user_id": user_id, "token": token}


@app.post("/api/auth-check")
def auth_check(authorization: str = Header(None)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ", 1)[1]
    user_id = auth_db.authenticate(token)

    if not user_id:
        return {"status": "error", "message": "invalid token"}

    return {"status": "ok"}


# ============================================================================
# API Endpoints
# ============================================================================


@app.post("/api/chat")
async def chat(request: ChatRequest, authorization: str = Header(None)):
    """Send message and get response"""

    try:
        # Validate token
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid auth header")

        token = authorization.split(" ", 1)[1]
        user_id = require_auth(token)  # returns username

        # Create conversation in thread pool if needed
        if user_id not in conversations:
            conversations[user_id] = await asyncio.to_thread(
                create_conversation, user_id
            )
        conversation = conversations[user_id]
        response = await asyncio.to_thread(conversation.chat, request.message)

        return {"response": response, "user_id": user_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clear")
async def clear_history(authorization: str = Header(None)):
    """Clear conversation history"""
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid auth header")

        token = authorization.split(" ", 1)[1]
        user_id = require_auth(token)

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
    """Read and serve analytics data from tool counter database"""
    try:
        counter = ToolCounter()
        data = counter.get_all_stats()
        return data

    except Exception as e:
        logger.exception("Failed to get analytics")
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
