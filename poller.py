import asyncio
import json
import logging
from typing import Optional

import devin_client
import github_client
import session_store
from config import POLL_INTERVAL_SECONDS

logger = logging.getLogger(__name__)

# Track active polling tasks so we don't double-poll the same session
_active_polls: set[str] = set()


async def poll_until_done(
    session_id: str,
    issue_number: int,
    started_duration_offset: int = 0,
) -> None:
    if session_id in _active_polls:
        logger.warning("Already polling session %s, skipping", session_id)
        return

    _active_polls.add(session_id)
    logger.info(json.dumps({"event": "poll_started", "session_id": session_id}))

    try:
        while True:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

            try:
                data = await devin_client.get_session_status(session_id)
            except Exception as exc:
                logger.error("Error polling Devin session %s: %s", session_id, exc)
                continue

            status_raw = data.get("status_enum", "unknown")
            logger.info(
                json.dumps({
                    "event": "poll_tick",
                    "session_id": session_id,
                    "devin_status": status_raw,
                })
            )

            if not devin_client.is_terminal(status_raw):
                continue

            # Session has finished — determine outcome
            if devin_client.is_success(status_raw):
                pr_url, pr_number = devin_client.extract_pr_url(data)

                # Fallback: search GitHub PRs if Devin didn't surface the URL
                if not pr_url:
                    branch = f"devin/fix-issue-{issue_number}"
                    pr_url, pr_number = await github_client.get_latest_pr_for_branch(branch)

                session_store.update_session_status(
                    session_id=session_id,
                    status="success",
                    pr_url=pr_url,
                    pr_number=pr_number,
                )

                session = session_store.get_session(session_id)
                duration = session["duration_seconds"] or 0

                if pr_url and pr_number:
                    comment = github_client.build_devin_success_comment(
                        pr_url, pr_number, duration
                    )
                else:
                    comment = (
                        f"## ✅ Devin finished\n\n"
                        f"Session `{session_id}` completed but no PR URL was found. "
                        f"Please check the repository for a new pull request."
                    )

                await github_client.post_comment(issue_number, comment)
                logger.info(
                    json.dumps({
                        "event": "session_success",
                        "session_id": session_id,
                        "issue": issue_number,
                        "pr": pr_url,
                        "duration_s": duration,
                    })
                )
            else:
                error_msg = data.get("error") or f"Devin status: {status_raw}"
                session_store.update_session_status(
                    session_id=session_id,
                    status="failed",
                    error=error_msg,
                )
                comment = github_client.build_devin_failed_comment(session_id, error_msg)
                await github_client.post_comment(issue_number, comment)
                logger.error(
                    json.dumps({
                        "event": "session_failed",
                        "session_id": session_id,
                        "issue": issue_number,
                        "error": error_msg,
                    })
                )

            break  # Exit loop once terminal state is handled

    finally:
        _active_polls.discard(session_id)
