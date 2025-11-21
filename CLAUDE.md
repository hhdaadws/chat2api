# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chat2API is a ChatGPT-to-OpenAI-API proxy written in Python with FastAPI. It converts ChatGPT's web interface into OpenAI-compatible API endpoints, supporting models from GPT-3.5 to O3-mini, including GPTs and multimodal capabilities.

## Development Commands

### Running the Application

```bash
# Direct Python execution (default port 5005)
python app.py

# Using uvicorn with auto-reload for development
uvicorn app:app --host 0.0.0.0 --port 5005 --reload

# With SSL (uncomment in app.py)
uvicorn app:app --host 0.0.0.0 --port 5005 --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### Dependency Management

```bash
# Install dependencies
pip install -r requirements.txt

# Core dependencies: FastAPI, curl_cffi, uvicorn, tiktoken, websockets, APScheduler
```

### Docker Operations

```bash
# Build and run with Docker
docker build -t chat2api .
docker run -d --name chat2api -p 5005:5005 chat2api

# Using Docker Compose
docker-compose up -d

# Using Docker Compose with WARP
docker-compose -f docker-compose-warp.yml up -d
```

### Testing Endpoints

```bash
# Test chat completions endpoint
curl -X POST http://127.0.0.1:5005/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}], "stream": true}'

# Access token management UI
# Navigate to: http://127.0.0.1:5005/tokens (or /{API_PREFIX}/tokens if API_PREFIX is set)
```

## Architecture

### Dual Operation Modes

The application operates in two distinct modes controlled by the `ENABLE_GATEWAY` environment variable:

1. **API-only mode** (default): Exposes OpenAI-compatible endpoints at `/v1/chat/completions`
2. **Gateway mode**: Adds official ChatGPT web interface mirroring functionality

### Directory Structure

- **`api/`**: Reverse API endpoints
  - `chat2api.py`: Main chat completions endpoint, token management routes
  - `tokens.py`: Token upload/management logic
  - `models.py`: Model name mapping/proxy
  - `files.py`: File upload utilities (images, documents)

- **`chatgpt/`**: Core ChatGPT interaction layer
  - `ChatService.py`: Main service class handling requests to ChatGPT backend
  - `authorization.py`: Token validation, refresh logic
  - `proofofWork.py`: PoW challenge solver
  - `turnstile.py`: Cloudflare Turnstile solver
  - `chatFormat.py`: Convert OpenAI API format to ChatGPT format
  - `chatLimit.py`: Rate limiting and quota management
  - `fp.py`: Browser fingerprinting
  - `wssClient.py`: WebSocket client for streaming

- **`gateway/`**: Gateway mode implementation (only loaded when `ENABLE_GATEWAY=true`)
  - `backend.py`: ChatGPT backend API proxy
  - `share.py`: Shared conversation handling
  - `chatgpt.py`, `gpts.py`, `v1.py`: Various gateway endpoints
  - `reverseProxy.py`: Reverse proxy utilities
  - `login.py`: Login page handling

- **`utils/`**: Shared utilities
  - `configs.py`: Environment variable loading and validation
  - `globals.py`: Global state (token lists, conversation maps)
  - `Client.py`: HTTP client wrapper using curl_cffi
  - `Logger.py`: Logging configuration
  - `retry.py`: Retry logic with token rotation
  - `kv_utils.py`: Key-value storage utilities

- **`templates/`**: Jinja2 HTML templates for token management UI and gateway

### Request Flow (API Mode)

1. Request arrives at `/v1/chat/completions` → `api/chat2api.py:send_conversation()`
2. Token extraction and validation → `chatgpt/authorization.py:verify_token()`
3. ChatService initialization → `chatgpt/ChatService.py:ChatService()`
4. Get chat requirements (PoW, Arkose) → `ChatService.get_chat_requirements()`
5. Format messages → `chatgpt/chatFormat.py:api_messages_to_chat()`
6. Send to ChatGPT backend → `ChatService.send_conversation()`
7. Stream or return response → `chatgpt/chatFormat.py:stream_response()`
8. Retry on failure with next token → `utils/retry.py:async_retry()`

### Token Management System

- Tokens stored in `data/token.txt` (managed via `utils/globals.py`)
- Supports both `AccessToken` and `RefreshToken`
- Automatic rotation on failure (controlled by `RETRY_TIMES`)
- Optional scheduled refresh (when `SCHEDULED_REFRESH=true`)
- Random vs sequential selection (controlled by `RANDOM_TOKEN`)
- Error tokens tracked separately to avoid reuse

### Model Mapping

Model names in requests are mapped to ChatGPT's internal model slugs in `ChatService.set_model()`:
- `gpt-3.5-turbo*` → `text-davinci-002-render-sha`
- `gpt-4o*` → `gpt-4o`
- `o1-*` → `o1-preview`, `o1-mini`, `o1-pro`
- `o3-mini*` → `o3-mini`, `o3-mini-high`, etc.
- Custom GPTs: `gpt-4-gizmo-g-*` → extracts gizmo ID

### Challenge Handling

The system handles multiple ChatGPT security challenges:
- **Proof of Work (PoW)**: Solved in `chatgpt/proofofWork.py` using difficulty-based computation
- **Arkose**: Requires external solver service (configured via `ARK0SE_TOKEN_URL`)
- **Turnstile**: Cloudflare challenge solver (configured via `TURNSTILE_SOLVER_URL`)
- **Sentinel**: Chat requirements endpoint provides challenge metadata

## Configuration

Environment variables are defined in `.env` (see `.env.example`). Key variables:

- **Security**: `API_PREFIX`, `AUTHORIZATION`, `AUTH_KEY`
- **Request**: `CHATGPT_BASE_URL`, `PROXY_URL`, `EXPORT_PROXY_URL`
- **Functionality**: `HISTORY_DISABLED`, `POW_DIFFICULTY`, `RETRY_TIMES`, `ENABLE_LIMIT`, `SCHEDULED_REFRESH`, `RANDOM_TOKEN`
- **Gateway**: `ENABLE_GATEWAY`, `AUTO_SEED`, `FORCE_NO_HISTORY`

All configs are loaded and validated in `utils/configs.py` on startup.

## Important Development Notes

### Adding New Endpoints

When adding API endpoints, respect the `api_prefix` decorator pattern:
```python
@app.post(f"/{api_prefix}/your/route" if api_prefix else "/your/route")
```

### HTTP Client Usage

Always use `utils/Client.py` (curl_cffi wrapper) instead of standard requests/httpx:
- Supports browser impersonation to avoid detection
- Handles proxy rotation with `{}` placeholder for session IDs
- Example: `self.s = Client(proxy=proxy_url, impersonate="safari15_3")`

### Error Handling

- Always close ChatService clients: use `BackgroundTask(chat_service.close_client)` with responses
- HTTPException with appropriate status codes (401, 403, 429, 500, 502)
- Token rotation on errors via `utils/retry.py:async_retry()`

### Logging

Use the logger from `utils/Logger.py`:
```python
from utils.Logger import logger
logger.info("message")
logger.error("error")
```

### File Operations

Image/file uploads are handled in `api/files.py`:
- Base64 and URL formats supported
- Automatic MIME type detection
- Upload flow: get upload URL → PUT to Azure → verify → return file_id

### Gateway Mode

Only enable gateway features when `enable_gateway=True` (from `utils/configs.py`). Gateway imports are conditional in `app.py` to avoid loading unnecessary modules.

### Version Management

Version is stored in `version.txt` and logged on startup. Update this file when releasing new versions.
