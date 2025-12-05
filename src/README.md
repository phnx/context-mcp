# Source Directory

## context-updater
Main MCP application source code

## fastmcp-test
For FastMCP smoke test:
```bash
# use http connection for better connectivity
fastmcp run src/simple_server.py:mcp --transport http --port 8000
python src/fastmcp-test/simple_client.py
```

## openai-api-test
For OpenAI API test:
```bash
python src/openai-api-test/openai_api_test.py
```