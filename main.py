import asyncio
import hashlib
import hmac
import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse

import devin_client
import github_client
import poller
import session_store
from config import DEVIN_TRIGGER_LABEL, GITHUB_WEBHOOK_SECRET
from dashboard import render_dashboard
from prompt_builder import build_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(os.path.dirname(session_store.DATABASE_PATH), exist_ok=True)
    session_store.init_db()

    # Resume polling for any sessions that were blocked when the server last stopped
    blocked = session_store.get_blocked_sessions()
    for s in blocked:
        logger.info(
            json.dumps({
                "event": "resuming_blocked_session",
                "session_id": s["session_id"],
                "issue": s["issue_number"],
            })
        )
        asyncio.ensure_future(
            poller.poll_until_done(
                session_id=s["session_id"],
                issue_number=s["issue_number"],
            )
        )

    logger.info(json.dumps({"event": "server_started", "resumed_blocked": len(blocked)}))
    yield
    logger.info(json.dumps({"event": "server_stopped"}))


app = FastAPI(title="Devin Automation", lifespan=lifespan)


def _verify_signature(body: bytes, signature: str | None) -> None:
    if not signature:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256")
    expected = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


@app.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
):
    body = await request.body()
    _verify_signature(body, x_hub_signature_256)

    if x_github_event != "issues":
        return Response(status_code=204)

    payload = json.loads(body)
    action = payload.get("action")

    # We only care about label additions
    if action != "labeled":
        return Response(status_code=204)

    label_name = payload.get("label", {}).get("name", "")
    if label_name != DEVIN_TRIGGER_LABEL:
        return Response(status_code=204)

    issue = payload["issue"]
    issue_number = issue["number"]
    issue_title = issue["title"]
    issue_url = issue["html_url"]
    issue_body = issue.get("body") or ""
    labels = issue.get("labels", [])
    issue_type = github_client.extract_issue_type(labels)

    logger.info(
        json.dumps({
            "event": "webhook_received",
            "issue": issue_number,
            "title": issue_title,
            "type": issue_type,
        })
    )

    prompt = build_prompt(
        issue_number=issue_number,
        issue_title=issue_title,
        issue_url=issue_url,
        issue_body=issue_body,
        issue_type=issue_type,
    )

    try:
        session_data = await devin_client.create_session(prompt)
    except Exception as exc:
        logger.error("Failed to create Devin session for issue #%s: %s", issue_number, exc)
        raise HTTPException(status_code=502, detail=f"Devin API error: {exc}")

    session_id = session_data["session_id"]
    devin_url = session_data.get("url")

    session_store.create_session(
        session_id=session_id,
        issue_number=issue_number,
        issue_title=issue_title,
        issue_type=issue_type,
    )

    started_comment = github_client.build_devin_started_comment(session_id, devin_url)
    await github_client.post_comment(issue_number, started_comment)

    # Fire-and-forget background poller
    asyncio.create_task(
        poller.poll_until_done(session_id=session_id, issue_number=issue_number)
    )

    logger.info(
        json.dumps({
            "event": "session_dispatched",
            "session_id": session_id,
            "issue": issue_number,
        })
    )

    return {"status": "accepted", "session_id": session_id}


@app.post("/trigger/{issue_number}")
async def manual_trigger(issue_number: int):
    """Manually trigger a Devin session for a GitHub issue from the dashboard."""
    try:
        issue = await github_client.get_issue(issue_number)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {exc}")

    issue_title = issue["title"]
    issue_url = issue["html_url"]
    issue_body = issue.get("body") or ""
    labels = issue.get("labels", [])
    issue_type = github_client.extract_issue_type(labels)

    logger.info(
        json.dumps({
            "event": "manual_trigger",
            "issue": issue_number,
            "title": issue_title,
            "type": issue_type,
        })
    )

    prompt = build_prompt(
        issue_number=issue_number,
        issue_title=issue_title,
        issue_url=issue_url,
        issue_body=issue_body,
        issue_type=issue_type,
    )

    try:
        session_data = await devin_client.create_session(prompt)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Devin API error: {exc}")

    session_id = session_data["session_id"]
    devin_url = session_data.get("url")

    session_store.create_session(
        session_id=session_id,
        issue_number=issue_number,
        issue_title=issue_title,
        issue_type=issue_type,
    )

    started_comment = github_client.build_devin_started_comment(session_id, devin_url)
    await github_client.post_comment(issue_number, started_comment)

    asyncio.create_task(
        poller.poll_until_done(session_id=session_id, issue_number=issue_number)
    )

    logger.info(
        json.dumps({
            "event": "session_dispatched",
            "session_id": session_id,
            "issue": issue_number,
            "source": "manual",
        })
    )

    return {"status": "accepted", "session_id": session_id}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return render_dashboard()


@app.get("/api/sessions")
async def api_sessions():
    return session_store.get_all_sessions()


@app.get("/health")
async def health():
    return {"status": "ok"}
