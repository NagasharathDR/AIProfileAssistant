# Profile Assistant Backend

A small FastAPI backend for the AI Profile Assistant project.

## Requirements

- Python 3.10 or newer
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

## MCP

`app/mcp_server.py` is intentionally a placeholder. MCP functionality has not been implemented.