# Tasklist
Keeping track of active tasks & statuses

## DONE
- test fastmcp connectivity
- test openai & env keys
- datamodel & primitive database
- implement memory CRUD tools 
- dockerize mcp server
- unittest tools
- unittest llm
- sanitize user inputs
- tool call logging
- simple web client interface
- dockerize web-client
- mcp usage analytics: tool calls, consumed tokens


## TODO

- deployment plan
    - mcp server as container -> for persistent connection with llm api
    - website frontend deployment
    - cli client - no deployment


- demo scenario - auto replay question set - playwright
- refactor & optimize
- document design decision


- guardrail - sensitive content
- replace OpenAI client with more unified interface & adapter





## DISCONTINUED
- database adapter -> technically feasible & straightforward -> use json now for ease of manipulation & testing
- authentication -> token-based authentication or more robust protocol e.g., OAuth
- admin privileges -> restricted functions e.g., list user -> should be implemented after authentication & authorization