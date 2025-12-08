#!/bin/bash

set -e  # stop on error

USER_SCENARIO=${1:-tony}

# -----------------------------------------------------------------------------
# PRE-CLEAN
# -----------------------------------------------------------------------------
echo "🧹 Cleaning old test databases..."
rm -f test/test_memories.db
rm -f test/auth_secure.db

# -----------------------------------------------------------------------------
# START BOTH PYTHON SERVERS
# -----------------------------------------------------------------------------
echo "🚀 Starting MCP Server + Web Gateway..."

export IS_MCP_CONTEXT_UPDATER_TEST=true

python src/context-updater/server.py &
PID_SERVER=$!

python src/context-updater/web-client/web_gateway.py &
PID_GATEWAY=$!

# -----------------------------------------------------------------------------
# CLEANUP HANDLER
# -----------------------------------------------------------------------------
cleanup() {
    echo ""
    echo "🛑 Caught signal — stopping everything..."

    # Kill ALL child processes in the same process group
    echo "🔪 Killing process group..."
    kill -- -$$ 2>/dev/null || true

    echo "🧹 Cleaning temporary DB files..."
    rm -f test/test_memories.db
    rm -f test/auth_secure.db

    echo "✅ Done."
}

# Run cleanup on:
#   EXIT   → script ends normally
#   INT    → ctrl+c
#   TERM   → external termination
trap cleanup EXIT INT TERM

# -----------------------------------------------------------------------------
# RUN TEST
# -----------------------------------------------------------------------------
echo "🧪 Running Puppeteer scenario: $USER_SCENARIO"
node puppeteer-runner.js "$USER_SCENARIO"

# -----------------------------------------------------------------------------
# NORMAL EXIT CLEANUP
