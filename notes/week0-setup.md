# Week 0 — Environment Setup & First API Call

## Completed
- GitHub repo `claude-architect-foundations` created and cloned
- Python 3.12.13 via virtual environment (`python3.12 -m venv venv`)
- Installed `anthropic` SDK with pip
- API key stored as environment variable `ANTHROPIC_API_KEY` in `~/.zshrc` (never hardcoded in source)
- First successful API call: `client.messages.create()` returned a text response

## Key Concepts
- **Virtual environment (venv):** project-specific toolbox; isolates Python version and packages per project
- **Environment variable:** secure way to store secrets outside code; the SDK reads `ANTHROPIC_API_KEY` automatically
- **API request anatomy:** `model` (which model), `max_tokens` (response length cap), `messages` (conversation history as a list of role/content dicts)
- **Response structure:** `response.content` is a LIST of blocks; `content[0].text` is the first block's text. Later, tool_use blocks will appear in this same list.

## Analogy
Client = waiter, model = kitchen, request = order slip, environment variable = key kept in your pocket instead of taped to the door.
