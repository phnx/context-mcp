# MCP Application - Context Memory Updater

[![CI/CD for MCP Context Server](https://github.com/phnx/context-mcp/actions/workflows/deploy.yml/badge.svg)](https://github.com/phnx/context-mcp/actions/workflows/deploy.yml)

This application showcases context memory using Model Context Protocol (MCP) tools in an LLM-based system.
It allows different users to store, retrieve, and update their travel preferences and other general memories with intelligence assistant through a chatinterface.

On the analytic side, the application summarizes tool usage statistics to support continuous improvement and cost control, answering questions such as  which tool-call sequences happens the more frequently? or which tool incurs most tokens?

## System Design
[diagram]

### MCP Server
- Standardized, specific tools made available for LLM to utilize upon natural language query: CRUD operations for user's general memory and travel preferences
- Unified datamodel and data storage for context memory
- Containerized: more persistent, suitable for LLM integration than serverless deployment

### MCP Client
- Chat-based user interface, self-identification, individual context information
- Lightweight server analytics - how has MCP server been utilized by the client? - macro statistics of tool usage
- Two versions of client, sharing the same core functionality

![mcp-statistics](./assets/mcp-tool-statistics.png)

#### Command-Line Client
- Native Python cli application with interactive chat loop
- No deployment, only connect to local MCP server and LLM API

![cli-client](./assets/cli-client.png)

#### Web Client
- Lightweight frontend that interacts with the single gateway, holding no secret keys and user information
- Single page application using vanilla JS
- Python API gateway for MCP & LLM API
- Containerized and deployable
- *Alternative*: heavier frontend JS frameworks as a one-stop solution to connect with LLM and MCP, which also requires its own deployment process & secret management, hence falling back to simple client-gateway solution

![web-client](./assets/web-client.png)


## Setup, Development, and Usage

Update local environment secret key. Never hard-code one.
```bash
cp .env.example .env
vi .env # update OPENAI_API_KEY
```

Local dependencies. Tested on Python 3.13. Using [PyEnv](https://github.com/pyenv/pyenv) to manage local Python version is recommended.
```bash
# option 1: installing in virtual environment (Pipenv--https://pipenv.pypa.io)
pipenv install
pipenv shell

# option 2: installing from frozen requirements.txt
pip install -r requirements.txt
```

### MCP Server & Clients
MCP server and available clients can operate in multiple options.

**Option 1)** Starting server without container.
```bash
# start server
python src/context-updater/server.py
```

**Option 2)** Starting servers with individual containers (mcp-server & web client) & host data sync.
```bash
# build images
docker build --target mcp-server -t context-mcp-server:latest .
docker build --target web-client -t context-web-client:latest .

# start mcp-server container
docker run -d --rm -p 0.0.0.0:8000:8000 \
    -v $(pwd)/database:/app/database \
    context-mcp-server:latest

# start web-client container
docker run -d --rm -p 0.0.0.0:8001:8001 \
    --env-file .env \
    -e MCP_SERVER_URL=http://host.docker.internal:8000/mcp \
    -e PYTHONUNBUFFERED=1 \
    context-web-client:latest
```

**Option 3)** Building and starting all containers (mcp-server & web client) with docker-compose.
```bash
docker-compose build
docker-compose up -d
```

### Non-Containerized Clients
Starting CLI client.
```bash
# start cli client only available as local option
python src/context-updater/cli_client.py
# or
python src/context-updater/cli_client.py --debug # show tool calls

# start web gateway & client
python src/context-updater/web-client/web_gateway.py
# web client runs on http://127.0.0.1:8001
```


Either option should yield following endpoint URLs:
- MCP - http://127.0.0.1:8000
- Web-Client - http://127.0.0.1:8001

## Tests
Unit testing whether MCP tools work correctly without LLM.
```bash
# Install dev dependencies
pipenv install --dev

# MCP functional test
pytest test/test_server.py -v -s
```

Integration testing whether LLM understands the data from, and can correctly interact with, MCP tools.

```bash
# make sure to start server with test flag - do not contaminate real database
IS_MCP_CONTEXT_UPDATER_TEST=true  python src/context-updater/server.py

# LLM hallunication test ~$0.20 per run
RUN_LLM_TESTS=true pytest tests/test_llm.py -v -s

# Single test case
RUN_LLM_TESTS=true pytest test/test_llm.py::TestLLMRealHallucination::test_llm_stores_and_retrieves_memory -v -s
```

## Limitations and Future Work

There are several pending tasks on [TODOs](TASKLIST.md).
- **scalable database**: currently, we're using single json file to store data. Even with file locking process to prevent access conflict, it's definitely not ideal. We can create an pydantic-based adapter that connects tools to more robust database instance via the unified datamodels, making data more persistent--only modify `server_database.py`.
- **proper user authentication & authorization**: there's no authentication mechanism per se, only unique user identification. To achieve this, we can 1) implement simple token-based authentication with a set of pre-defined users / roles or 2) implement dynamic registration using well-established protocol such as OAuth.
- **model performance test**: we use `gpt-4o-mini` for its cost effectiveness. It should be tested whether switching to more advanced models worth the costs for this type of tasks. We can create semantically difficult dataset and questions to test this out.

## Final Thoughts


I chose the MCP option out of curiosity because I've recently implemented an [LLM document assitant](https://github.com/phnx/diary-rag) for my old blog as a toy project, which has covered most required functionalities for the RAG option, and partially for the data-driven assistant option.
I felt it's a good opportunity to try building an MCP server from scratch because I've only worked with MCP tools implemented by other people.
However, it was quite an open-ended requirement, leaving room for interpretation. I hope I haven't misunderstood it by far :)

The most challenging problem I encountered was the rapidly changing API specifications of all the essential libraries and tools.
This makes AI coding assistant **very** unreliable.
Documentation does not provide a good support either.
Trial-and-error, with very specific questions prompts on small and concise issues, is the best workaround in this case.
Holistic prompting never works.