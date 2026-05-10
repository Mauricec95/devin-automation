# Devin Automation — Superset Issue Remediator

An event-driven automation that watches a GitHub repository for issues labeled `devin-fix` and autonomously remediates them using the [Devin API](https://docs.devin.ai/api-reference/overview).

**Related repo:** [Mauricec95/superset](https://github.com/Mauricec95/superset) — the Apache Superset fork containing the issues being remediated.

---

## How It Works

```
1. GITHUB          An issue gets labeled "devin-fix"
                          │
                          ▼
2. FASTAPI SERVER  Receives the webhook, reads the issue,
   (this app)      builds a structured prompt, calls Devin API
                          │
                          ▼
3. DEVIN API       Autonomous engineer: clones the repo,
                   understands the code, makes the fix,
                   runs tests, opens a Pull Request
                          │
                          ▼
4. GITHUB PR       Devin's proposed fix — reviewable and mergeable
                   by a human engineer
                          │
                          ▼
5. DASHBOARD       Every session recorded in SQLite, visible
   /dashboard      at localhost:8000/dashboard with live metrics
```

---

## Prerequisites

- Docker + Docker Compose
- A [Devin API key](https://app.devin.ai/settings/api)
- A GitHub personal access token (scopes: `repo`, `write:discussion`)
- [ngrok](https://ngrok.com) for local webhook delivery

---

## Setup

### 1. Clone this repo

```bash
git clone https://github.com/Mauricec95/devin-automation.git
cd devin-automation
```

### 2. Configure environment

```bash
cp .env.example .env
# Open .env and fill in GITHUB_TOKEN, DEVIN_API_KEY, GITHUB_WEBHOOK_SECRET
```

### 3. Run the server

```bash
docker compose up --build
```

Server starts at `http://localhost:8000`.

### 4. Expose the webhook (local development)

```bash
ngrok http 8000
# Copy the https URL shown, e.g. https://abc123.ngrok-free.app
```

### 5. Register the GitHub webhook

In your fork → **Settings → Webhooks → Add webhook**:

| Field | Value |
|-------|-------|
| Payload URL | `https://abc123.ngrok-free.app/webhook` |
| Content type | `application/json` |
| Secret | Same value as `GITHUB_WEBHOOK_SECRET` in `.env` |
| Events | **Issues** only |

### 6. Trigger a run

Add the label **`devin-fix`** to any issue in your fork.

---

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /webhook` | GitHub webhook receiver |
| `GET /dashboard` | Live observability dashboard (auto-refreshes every 30s) |
| `GET /api/sessions` | Raw JSON — all session records |
| `GET /health` | Health check |

---

## Observability Dashboard

The dashboard at `/dashboard` answers the question **"Is this working?"** for an engineering leader:

- Total sessions / Succeeded / Failed / Running
- Success rate %
- Average time from trigger to PR
- Breakdown by issue type (security · dependency · code-quality)
- Per-session status, PR link, and duration
- JSON API link for programmatic access

---

## Issues Remediated

| # | Issue | Type | Status |
|---|-------|------|--------|
| [#1](https://github.com/Mauricec95/superset/issues/1) | Add startup validation to reject default SECRET_KEY | security | ✅ Merged ([PR #7](https://github.com/Mauricec95/superset/pull/7)) |
| [#2](https://github.com/Mauricec95/superset/issues/2) | Upgrade @reduxjs/toolkit from 1.9.x to 2.x | dependency | ⏳ Pending |
| [#3](https://github.com/Mauricec95/superset/issues/3) | Add missing Python type hints to date_parser.py | code-quality | ⏳ Pending |
| [#4](https://github.com/Mauricec95/superset/issues/4) | Replace `any` types in core TypeScript utility files | code-quality | ⏳ Pending |
| [#5](https://github.com/Mauricec95/superset/issues/5) | Restrict CSP unsafe-eval to development mode only | security | ⏳ Pending |
| [#6](https://github.com/Mauricec95/superset/issues/6) | Pin paramiko upper version bound | dependency | ⏳ Pending |

---

## Project Structure

```
devin-automation/
├── main.py            # FastAPI app — webhook listener + API routes
├── devin_client.py    # Devin API wrapper (create + poll sessions)
├── github_client.py   # GitHub API wrapper (read issues, post comments)
├── session_store.py   # SQLite session state
├── prompt_builder.py  # Builds structured prompts per issue type
├── poller.py          # Background task — polls Devin every 30s
├── dashboard.py       # Renders the observability HTML page
├── config.py          # Environment variable loading
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Why Devin?

Traditional automation (Dependabot, shell scripts) handles narrow, pre-defined patterns — bump a version, apply a patch. Devin handles the **long tail**: security hardening, type safety fixes, config changes — anything that requires reading and understanding code.

The same system handles all three issue types with a single interface: a prompt. The human retains full control — every fix goes through a Pull Request review before anything is merged.

### The Real Problem This Solves

Every engineering team has a backlog of issues that never get prioritized — not because they don't matter, but because they're not glamorous enough to justify pulling an engineer off feature work. Security hardening tickets. Outdated dependencies. Type safety debt. They sit there for months.

Apache Superset is a perfect example. Our audit identified a default `SECRET_KEY` that makes session tokens forgeable, a CSP policy that allows `unsafe-eval` in production, an EOL dependency with no security patches, and dozens of missing type annotations. None of these are hard to fix. All of them would take a real engineer 30–60 minutes each. None of them ever make it to the top of the sprint.

### Why Existing Tools Don't Solve It

Dependabot can bump a version number. A shell script can run a linter. But fixing a security configuration, adding type annotations to a specific file, or restricting a CSP policy to development mode — these require *understanding the codebase*. You need to know which file to change, what the correct logic is, and whether the tests still pass. That's not a script, that's engineering judgment.

### Why Devin Changes the Equation

Devin is the first tool that can receive a natural-language description of an engineering problem, read the relevant code, reason about the correct fix, run the tests, and open a Pull Request — without a human writing a single line. That's not a copilot you pair program with. That's a delegation model: you describe the problem, Devin solves it, you review the result.

In this system, triggering a fix costs an engineer **30 seconds** — the time it takes to add a label to a GitHub issue. The rest is autonomous. Devin clones the repo, understands the context, makes the change, validates it, and ships the PR. The engineer reviews and merges.

### The Compounding Advantage

Build this workflow once, and every future issue labeled `devin-fix` gets picked up automatically. The backlog shrinks on its own. Security findings from a scan become PRs without a meeting. Dependency alerts become fixes without a sprint ticket. The system gets more valuable the more issues you feed it — and it runs while your engineers are focused on things that actually require human creativity.
