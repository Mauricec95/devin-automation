from config import GITHUB_REPO

REPO_URL = f"https://github.com/{GITHUB_REPO}"

BASE_PROMPT = """You are an autonomous software engineer remediating a GitHub issue in the Apache Superset repository.

REPOSITORY: {repo_url}
ISSUE #{issue_number}: {issue_title}
ISSUE URL: {issue_url}
ISSUE TYPE: {issue_type}

--- ISSUE DESCRIPTION ---
{issue_body}
--- END DESCRIPTION ---

STRICT INSTRUCTIONS:
1. Clone the repository at {repo_url} (branch: master)
2. Make the minimal change that resolves the issue — do not refactor unrelated code
3. Ensure all existing tests pass relevant to the files you changed
4. Run pre-commit checks: `pre-commit run --all-files`
5. Create a Pull Request with:
   - Title: "fix: {issue_title}"
   - Body: explain what was changed and why, reference issue #{issue_number}
6. Do NOT modify anything unrelated to this issue
7. Do NOT skip pre-commit or test steps

CODEBASE CONTEXT:
- Backend: Python/Flask — all new code needs type hints, MyPy must pass
- Frontend: TypeScript only — no `any` types allowed
- Tests: `npm run test` for frontend, `pytest` for backend
- Pre-commit: `pre-commit run --all-files` must pass before opening PR
- Apache license headers required on any new files

When done, output the Pull Request URL clearly.
"""

TYPE_ADDENDUM = {
    "security": """
SECURITY FIX NOTES:
- Be conservative — security fixes should be minimal and targeted
- Add a unit test that proves the vulnerability is blocked
- Do not introduce new dependencies to fix the issue
""",
    "dependency": """
DEPENDENCY UPGRADE NOTES:
- Only change the version constraint, not unrelated code
- Run the test suite after upgrading to verify nothing broke
- If there are breaking changes, fix them in the same PR
- Update lock files if present (package-lock.json, etc.)
""",
    "code-quality": """
CODE QUALITY NOTES:
- Do not change any logic — only improve types, hints, or structure
- TypeScript: replace `any` with the most specific correct type
- Python: add type hints, ensure MyPy passes
- Run the full test suite to confirm no regressions
""",
}


def build_prompt(
    issue_number: int,
    issue_title: str,
    issue_url: str,
    issue_body: str,
    issue_type: str,
) -> str:
    prompt = BASE_PROMPT.format(
        repo_url=REPO_URL,
        issue_number=issue_number,
        issue_title=issue_title,
        issue_url=issue_url,
        issue_body=issue_body or "(no description provided)",
        issue_type=issue_type,
    )
    addendum = TYPE_ADDENDUM.get(issue_type, "")
    return prompt + addendum
