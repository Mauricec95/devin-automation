from datetime import datetime, timezone
from session_store import get_all_sessions

COGNITION_LOGO = "https://cognition.ai/favicon.ico"
OWNER_NAME = "Maurice Lubetzki"
GITHUB_REPO = "Mauricec95/superset"

ALL_ISSUES = [
    (1, "[Security] Add startup validation to reject default SECRET_KEY", "security"),
    (2, "[Dependency] Upgrade @reduxjs/toolkit from 1.9.x to 2.x", "dependency"),
    (3, "[Code Quality] Add missing Python type hints to date_parser.py", "code-quality"),
    (4, "[Code Quality] Replace `any` types in core TypeScript utility files", "code-quality"),
    (5, "[Security] Restrict CSP unsafe-eval to development mode only", "security"),
    (6, "[Dependency] Pin paramiko upper version bound", "dependency"),
]

STATUS_EMOJI = {
    "running": "🔄",
    "success": "✅",
    "failed": "❌",
    "blocked": "🟠",
    "pending": "⏳",
}

DEVIN_SESSION_BASE = "https://app.devin.ai/sessions"

TYPE_BADGE = {
    "security": "#d73a4a",
    "dependency": "#e4a800",
    "code-quality": "#0e8a16",
    "general": "#6f42c1",
}

TYPE_LABEL = {
    "security": "🔒 Security",
    "dependency": "📦 Dependency",
    "code-quality": "🧹 Code Quality",
    "general": "⚙️ General",
}


def _badge(text: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:#fff;'
        f'padding:2px 8px;border-radius:12px;font-size:12px">{text}</span>'
    )


def _duration(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    m, s = divmod(seconds, 60)
    return f"{m}m {s}s"


def _type_breakdown_cards(sessions: list[dict]) -> str:
    counts: dict[str, dict] = {}
    for s in sessions:
        t = s["issue_type"]
        if t not in counts:
            counts[t] = {"total": 0, "success": 0}
        counts[t]["total"] += 1
        if s["status"] == "success":
            counts[t]["success"] += 1

    if not counts:
        return ""

    cards = ""
    for issue_type, data in counts.items():
        color = TYPE_BADGE.get(issue_type, "#888")
        label = TYPE_LABEL.get(issue_type, issue_type)
        rate = f"{int(data['success'] / data['total'] * 100)}%" if data["total"] else "—"
        cards += f"""
        <div class="card" style="border-top: 3px solid {color}">
          <div class="value" style="color:{color}">{data['total']}</div>
          <div class="label">{label}</div>
          <div style="font-size:11px;color:#8b949e;margin-top:6px">{data['success']} succeeded · {rate}</div>
        </div>"""
    return cards


def _trigger_button(issue_number: int, session: dict | None) -> str:
    if session is None:
        label, bg = "▶ Run Devin", "#0969da"
        return (
            f'<button onclick="triggerDevin({issue_number})" '
            f'style="background:{bg};color:#fff;border:none;border-radius:6px;'
            f'padding:4px 12px;font-size:12px;cursor:pointer;white-space:nowrap">'
            f'{label}</button>'
        )

    status = session.get("status")
    is_blocked = "blocked" in (session.get("error") or "")

    if status == "running" or is_blocked:
        return '<span style="color:#8b949e;font-size:12px">⏳ running…</span>'

    if status == "success":
        return '<span style="color:#1a7f37;font-size:12px">✅ Done</span>'

    # failed (non-blocked) — allow re-run
    return (
        f'<button onclick="triggerDevin({issue_number})" '
        f'style="background:#6f42c1;color:#fff;border:none;border-radius:6px;'
        f'padding:4px 12px;font-size:12px;cursor:pointer;white-space:nowrap">'
        f'↺ Re-run Devin</button>'
    )


def render_dashboard() -> str:
    sessions = get_all_sessions()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    total = len(sessions)
    success = sum(1 for s in sessions if s["status"] == "success")
    failed = sum(1 for s in sessions if s["status"] == "failed")
    running = sum(1 for s in sessions if s["status"] == "running")
    durations = [s["duration_seconds"] for s in sessions if s["duration_seconds"]]
    avg_duration = int(sum(durations) / len(durations)) if durations else None
    success_rate = f"{int(success / total * 100)}%" if total else "—"

    # Index sessions by issue number for quick lookup
    session_by_issue: dict[int, dict] = {}
    for s in sessions:
        n = s["issue_number"]
        if n not in session_by_issue or s["started_at"] > session_by_issue[n]["started_at"]:
            session_by_issue[n] = s

    type_cards = _type_breakdown_cards(sessions)
    type_section = ""
    if type_cards:
        type_section = (
            '<div class="divider"></div>'
            '<div class="metrics">'
            '<div class="section-label" style="width:100%;padding:0">By Issue Type</div>'
            + type_cards +
            '</div>'
        )

    # Build rows for all known issues (not just ones with sessions)
    rows = ""
    for issue_number, issue_title, issue_type in ALL_ISSUES:
        s = session_by_issue.get(issue_number)
        type_color = TYPE_BADGE.get(issue_type, "#888")
        is_running = s is not None and s["status"] == "running"
        is_blocked = s is not None and "blocked" in (s.get("error") or "")

        if s:
            is_blocked = "blocked" in (s.get("error") or "")
            emoji = STATUS_EMOJI.get("blocked" if is_blocked else s["status"], "❓")

            if is_blocked:
                session_url = f"{DEVIN_SESSION_BASE}/{s['session_id']}"
                status_cell = (
                    f'{emoji} <span style="color:#b45309;font-weight:600">Needs your input</span>'
                    f'<div style="font-size:11px;color:#8b949e;margin-top:2px">'
                    f'Devin is waiting — '
                    f'<a href="{session_url}" target="_blank" style="color:#0969da">open Devin session</a>'
                    f' to unblock it</div>'
                )
            else:
                status_cell = f"{emoji} {s['status']}"

            pr_cell = (
                f'<a href="{s["pr_url"]}" target="_blank">#{s["pr_number"]}</a>'
                if s["pr_url"] else "—"
            )
            error_cell = (
                f'<span title="{s["error"]}" style="color:#d73a4a">⚠ error</span>'
                if s["error"] and not is_blocked else ""
            )
            duration_cell = _duration(s["duration_seconds"])
            started_cell = s["started_at"][:16].replace("T", " ")
        else:
            status_cell = "⏳ pending"
            pr_cell = "—"
            error_cell = ""
            duration_cell = "—"
            started_cell = "—"

        rows += f"""
        <tr>
          <td><a href="https://github.com/{GITHUB_REPO}/issues/{issue_number}"
                 target="_blank">#{issue_number}</a></td>
          <td style="max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="{issue_title}">{issue_title}</td>
          <td>{_badge(issue_type, type_color)}</td>
          <td>{status_cell}</td>
          <td>{pr_cell} {error_cell}</td>
          <td>{duration_cell}</td>
          <td style="font-size:11px;color:#888">{started_cell}</td>
          <td>{_trigger_button(issue_number, s)}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="30">
  <title>Devin Automation Dashboard</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           margin: 0; background: #f6f8fa; color: #24292f; }}
    header {{ background: #24292f; color: #fff; padding: 16px 32px;
              display: flex; align-items: center; justify-content: space-between; }}
    .header-left {{ display: flex; align-items: center; gap: 14px; }}
    .cognition-badge {{ display: flex; align-items: center; gap: 6px;
                        background: #fff1; border: 1px solid #ffffff30;
                        border-radius: 20px; padding: 4px 12px 4px 8px;
                        font-size: 12px; color: #fff; }}
    .cognition-badge img {{ width: 16px; height: 16px; border-radius: 3px; }}
    header h1 {{ margin: 0; font-size: 20px; }}
    .header-meta {{ text-align: right; font-size: 12px; color: #8b949e; line-height: 1.8; }}
    .owner {{ font-size: 13px; color: #8b949e; margin-top: 2px; }}
    .section-label {{ padding: 0 32px 8px; font-size: 11px; font-weight: 600;
                      text-transform: uppercase; letter-spacing: 0.08em; color: #57606a; }}
    .metrics {{ display: flex; gap: 16px; padding: 24px 32px 8px; flex-wrap: wrap; }}
    .divider {{ height: 1px; background: #d0d7de; margin: 16px 32px; }}
    .card {{ background: #fff; border: 1px solid #d0d7de; border-radius: 8px;
             padding: 16px 24px; min-width: 130px; text-align: center; }}
    .card .value {{ font-size: 32px; font-weight: 700; }}
    .card .label {{ font-size: 12px; color: #57606a; margin-top: 4px; }}
    .green {{ color: #1a7f37; }}
    .red {{ color: #d1242f; }}
    .blue {{ color: #0969da; }}
    table {{ width: calc(100% - 64px); margin: 16px 32px 32px;
             border-collapse: collapse; background: #fff;
             border: 1px solid #d0d7de; border-radius: 8px; overflow: hidden; }}
    th {{ background: #f6f8fa; padding: 10px 14px; text-align: left;
          font-size: 12px; font-weight: 600; border-bottom: 1px solid #d0d7de; }}
    td {{ padding: 10px 14px; font-size: 13px; border-bottom: 1px solid #f0f0f0;
          vertical-align: middle; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #f6f8fa; }}
    a {{ color: #0969da; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .footer {{ color: #8b949e; font-size: 12px; padding: 0 32px 24px; }}
    .toast {{ position: fixed; bottom: 24px; right: 24px; background: #24292f;
              color: #fff; padding: 12px 20px; border-radius: 8px; font-size: 13px;
              display: none; z-index: 999; }}
  </style>
</head>
<body>
  <header>
    <div class="header-left">
      <div>
        <h1>🤖 Devin Automation Dashboard</h1>
        <div class="owner">Built by {OWNER_NAME} &nbsp;·&nbsp; apache/superset</div>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px">
      <div class="cognition-badge">
        <img src="{COGNITION_LOGO}" alt="Cognition">
        Powered by Devin · Cognition AI
      </div>
      <div class="header-meta">
        <span style="color:#1a7f37">● Live</span> &nbsp; Last updated: {now}
      </div>
    </div>
  </header>

  <div class="metrics" style="padding-top:24px">
    <div class="section-label" style="width:100%;padding:0">Overall</div>
    <div class="card"><div class="value">{total}</div><div class="label">Total Sessions</div></div>
    <div class="card"><div class="value green">{success}</div><div class="label">Succeeded</div></div>
    <div class="card"><div class="value red">{failed}</div><div class="label">Failed</div></div>
    <div class="card"><div class="value blue">{running}</div><div class="label">Running</div></div>
    <div class="card"><div class="value">{success_rate}</div><div class="label">Success Rate</div></div>
    <div class="card"><div class="value">{_duration(avg_duration)}</div><div class="label">Avg Time to PR</div></div>
  </div>

  {type_section}

  <div class="divider"></div>
  <div class="section-label">Issue Tracker</div>

  <table>
    <thead>
      <tr>
        <th>Issue</th><th>Title</th><th>Type</th><th>Status</th>
        <th>Pull Request</th><th>Duration</th><th>Started (UTC)</th><th>Action</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

  <div class="footer">
    Auto-refreshes every 30s &nbsp;·&nbsp;
    <a href="/api/sessions">JSON API</a> &nbsp;·&nbsp;
    <a href="https://github.com/Mauricec95/devin-automation" target="_blank">Source</a>
  </div>

  <div class="toast" id="toast"></div>

  <script>
    async function triggerDevin(issueNumber) {{
      const btn = event.target;
      btn.disabled = true;
      btn.textContent = '⏳ Starting…';
      try {{
        const res = await fetch(`/trigger/${{issueNumber}}`, {{ method: 'POST' }});
        const data = await res.json();
        if (res.ok) {{
          showToast(`✅ Devin started on issue #${{issueNumber}}`);
          setTimeout(() => location.reload(), 2000);
        }} else {{
          showToast(`❌ Error: ${{data.detail}}`);
          btn.disabled = false;
          btn.textContent = '▶ Run Devin';
        }}
      }} catch (e) {{
        showToast('❌ Could not reach server');
        btn.disabled = false;
        btn.textContent = '▶ Run Devin';
      }}
    }}

    function showToast(msg) {{
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.style.display = 'block';
      setTimeout(() => t.style.display = 'none', 4000);
    }}
  </script>
</body>
</html>"""
