FROM python:3.13-slim AS base

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code & initial data
COPY src/ ./src/
COPY database/ ./database/

# Target 1: FastMCP Server
FROM base as mcp-server
EXPOSE 8000
CMD ["python", "src/context-updater/server.py"]

# Target 2: FastAPI Web Client
FROM base as web-client
EXPOSE 8001
CMD ["python", "src/context-updater/web-client/web_gateway.py"]