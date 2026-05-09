# Devin Automation — Superset Issue Remediator

An event-driven automation that watches a GitHub repository for issues labeled `devin-fix` and autonomously remediates them using the [Devin API](https://docs.devin.ai/api-reference/overview).

## Architecture

```
GitHub Issue (labeled "devin-fix")
        │
        ▼
GitHub Webhook → FastAPI Server (this app)
                        │
                        ▼
               Devin API (creates session)
                        │
                   [Devin works]
                        │
                        ▼
               Poller checks status every 30s
                        │
                        ▼
               GitHub PR created by Devin
                        │
                        ▼
               Comment posted on issue with PR link
                        │
                        ▼
               SQLite + Dashboard (/dashboard)
```

## Prerequisites

- Docker + Docker Compose
- A GitHub account with a forked repo ([Mauricec95/superset](https://github.com/Mauricec95/superset))
- A [Devin API key](https://app.devin.ai/settings/api)
- A GitHub personal access token (scopes: `repo`, `write:discussion`)
- [ngrok](https://ngrok.com) (for local webhook delivery during development)

## Setup

### 1. Clone this repo

```bash
git clone https://github.com/Mauricec95/devin-automation.git
cd devin-automation
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in your tokens and secrets in .env
```

### 3. Run the server

```bash
docker compose up --build
```

The server starts at `http://localhost:8000`.

### 4. Expose the webhook (local development)

```bash
ngrok http 8000
# Copy the https URL, e.g. https://abc123.ngrok.io
```

### 5. Register the GitHub webhook

In your fork → **Settings → Webhooks → Add webhook**:

| Field | Value |
|-------|-------|
| Payload URL | `https://abc123.ngrok.io/webhook` |
| Content type | `application/json` |
| Secret | Same value as `GITHUB_WEBHOOK_SECRET` in your `.env` |
| Events | Select **Issues** only |

### 6. Trigger a run

Go to any issue in your fork and add the label **`devin-fix`**.

Watch the server logs and visit `http://localhost:8000/dashboard` to see it in action.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /webhook` | GitHub webhook receiver |
| `GET /dashboard` | Observability dashboard (auto-refreshes every 30s) |
| `GET /api/sessions` | Raw JSON list of all sessions |
| `GET /health` | Health check |

## Dashboard

The dashboard at `/dashboard` shows:

- Total sessions / Success / Failed / Running counts
- Success rate %
- Average time from trigger to PR
- Per-issue status, PR link, and duration

## Issues Tracked

| # | Title | Type |
|---|-------|------|
| [#1](https://github.com/Mauricec95/superset/issues/1) | Add startup validation to reject default SECRET_KEY | security |
| [#2](https://github.com/Mauricec95/superset/issues/2) | Upgrade @reduxjs/toolkit from 1.9.x to 2.x | dependency |
| [#3](https://github.com/Mauricec95/superset/issues/3) | Add missing Python type hints to date_parser.py | code-quality |
| [#4](https://github.com/Mauricec95/superset/issues/4) | Replace `any` types in core TypeScript utility files | code-quality |
| [#5](https://github.com/Mauricec95/superset/issues/5) | Restrict CSP unsafe-eval to development mode only | security |
| [#6](https://github.com/Mauricec95/superset/issues/6) | Pin paramiko upper version bound | dependency |

## Project Structure

```
devin-automation/
├── main.py            # FastAPI app — webhook listener + API routes
├── devin_client.py    # Devin API wrapper (create + poll sessions)
├── github_client.py   # GitHub API wrapper (read issues, post comments)
├── session_store.py   # SQLite session state
├── prompt_builder.py  # Builds structured prompts for Devin
├── poller.py          # Background async task — polls until Devin finishes
├── dashboard.py       # Renders the observability HTML page
├── config.py          # Environment variable loading
├── requirements.txt   # Python dependencies
├── Dockerfile
├── docker-compose.yml
└── .env.example       # Template for required environment variables
```
