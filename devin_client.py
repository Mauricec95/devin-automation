import logging
import httpx
from config import DEVIN_API_KEY, DEVIN_API_BASE

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {DEVIN_API_KEY}",
    "Content-Type": "application/json",
}


async def create_session(prompt: str) -> dict:
    """Start a new Devin session and return the session object."""
    url = f"{DEVIN_API_BASE}/sessions"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers=HEADERS,
            json={"prompt": prompt},
            timeout=30,
        )
        resp.raise_for_status()
    data = resp.json()
    logger.info(
        "Devin session created: session_id=%s", data.get("session_id")
    )
    return data


async def get_session_status(session_id: str) -> dict:
    """Poll a Devin session and return its current state."""
    url = f"{DEVIN_API_BASE}/session/{session_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    return resp.json()


def is_terminal(status: str) -> bool:
    """Return True if the session has reached a final state."""
    return status in ("finished", "stopped", "failed", "error", "blocked")


def is_success(status: str) -> bool:
    return status == "finished"


def extract_pr_url(session_data: dict) -> tuple[str | None, int | None]:
    """
    Try to pull a PR URL out of the Devin session response.
    Devin may surface it in structured_output or in the status_enum field.
    """
    structured = session_data.get("structured_output") or {}

    pr_url = structured.get("pr_url") or structured.get("pull_request_url")
    pr_number = structured.get("pr_number")

    if pr_url and pr_number is None:
        # parse number from URL: .../pull/123
        parts = pr_url.rstrip("/").split("/")
        if parts and parts[-1].isdigit():
            pr_number = int(parts[-1])

    return pr_url, pr_number
