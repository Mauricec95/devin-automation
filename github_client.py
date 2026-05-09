import logging
import re
import httpx
from config import GITHUB_TOKEN, GITHUB_REPO

logger = logging.getLogger(__name__)

BASE = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


async def get_issue(issue_number: int) -> dict:
    url = f"{BASE}/repos/{GITHUB_REPO}/issues/{issue_number}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    return resp.json()


async def post_comment(issue_number: int, body: str) -> None:
    url = f"{BASE}/repos/{GITHUB_REPO}/issues/{issue_number}/comments"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=HEADERS, json={"body": body}, timeout=15)
        resp.raise_for_status()
    logger.info("Posted comment on issue #%s", issue_number)


async def get_latest_pr_for_branch(branch: str) -> tuple[str | None, int | None]:
    url = f"{BASE}/repos/{GITHUB_REPO}/pulls"
    params = {"head": f"{GITHUB_REPO.split('/')[0]}:{branch}", "state": "open"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
    pulls = resp.json()
    if pulls:
        return pulls[0]["html_url"], pulls[0]["number"]
    return None, None


def extract_issue_type(labels: list[dict]) -> str:
    for label in labels:
        name = label.get("name", "")
        if "security" in name:
            return "security"
        if "dependency" in name or "dep" in name:
            return "dependency"
        if "quality" in name or "code" in name:
            return "code-quality"
    return "general"


def build_devin_started_comment(session_id: str, devin_url: str | None = None) -> str:
    lines = [
        "## 🤖 Devin is on it!",
        "",
        f"A Devin session has been started for this issue.",
        f"- **Session ID:** `{session_id}`",
    ]
    if devin_url:
        lines.append(f"- **Devin session:** {devin_url}")
    lines += [
        "",
        "Devin will open a Pull Request when the fix is ready. This comment will be updated with the PR link.",
    ]
    return "\n".join(lines)


def build_devin_success_comment(pr_url: str, pr_number: int, duration_seconds: int) -> str:
    minutes, seconds = divmod(duration_seconds, 60)
    return "\n".join([
        "## ✅ Devin completed the fix!",
        "",
        f"- **Pull Request:** {pr_url} (#{pr_number})",
        f"- **Time to fix:** {minutes}m {seconds}s",
        "",
        "Please review the PR and merge if it looks good.",
    ])


def build_devin_failed_comment(session_id: str, error: str | None) -> str:
    lines = [
        "## ❌ Devin session failed",
        "",
        f"- **Session ID:** `{session_id}`",
    ]
    if error:
        lines += ["", f"**Error:** {error}"]
    lines += ["", "This issue may need manual attention."]
    return "\n".join(lines)
