# Profile Assistant Backend

A small FastAPI backend for the AI Profile Assistant project.

## Requirements

- Python 3.11 or newer
- `pip`

## Setup

From this directory, create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate it with:

```sh
source .venv/bin/activate
```

Install dependencies:

```sh
pip install -r requirements.txt
```

Copy `.env.example` to `.env` to keep local configuration values together. The application currently reads configuration from process environment variables; it does not automatically load `.env` files.

## Run

Start the development server from this directory:

```sh
python -m uvicorn app.main:app --reload
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Endpoints

- `GET /health` returns `{"status": "healthy"}`.
- `GET /api/profile` returns illustrative sample profile data, explicitly labelled as sample data and not representing a real person.

## Tests

Run the test suite from this directory:

```sh
pytest
```

## Profile MCP Server

The FastAPI app also exposes a Streamable HTTP MCP server at `/mcp`. Its `search_profile` tool searches the configured LinkedIn and resume PDFs and returns matching excerpts with source names and page numbers. The index is built lazily on the first tool call and kept in memory; the first call may download the configured embedding model.

Connect an MCP client to `http://127.0.0.1:8000/mcp` for local development. The MCP endpoint is public unless protected by deployment-level access controls; profile excerpts returned by the tool are therefore visible to callers. MCP host validation allows localhost by default and includes Hugging Face's `SPACE_HOST` environment value when available. Set `PROFILE_MCP_ALLOWED_HOSTS` to a comma-separated explicit host allowlist when deploying elsewhere.

This MCP server exposes PDF search only. It does not call an LLM or the GitHub MCP server. The GitHub MCP integration and LLM orchestration are separate future phases.