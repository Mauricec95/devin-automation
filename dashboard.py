from datetime import datetime, timezone
from session_store import get_all_sessions


STATUS_EMOJI = {
    "running": "🔄",
    "success": "✅",
    "failed": "❌",
    "pending": "⏳",
}

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

    system_status = (
        '<span style="color:#1a7f37">● Live</span>' if True
        else '<span style="color:#d1242f">● Offline</span>'
    )

    type_cards = _type_breakdown_cards(sessions)

    rows = ""
    for s in sessions:
        emoji = STATUS_EMOJI.get(s["status"], "❓")
        type_color = TYPE_BADGE.get(s["issue_type"], "#888")
        pr_cell = (
            f'<a href="{s["pr_url"]}" target="_blank">#{s["pr_number"]}</a>'
            if s["pr_url"]
            else "—"
        )
        error_cell = (
            f'<span title="{s["error"]}" style="color:#d73a4a">⚠ error</span>'
            if s["error"] else ""
        )
        rows += f"""
        <tr>
          <td><a href="https://github.com/Mauricec95/superset/issues/{s['issue_number']}"
                 target="_blank">#{s['issue_number']}</a></td>
          <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="{s['issue_title']}">{s['issue_title']}</td>
          <td>{_badge(s['issue_type'], type_color)}</td>
          <td>{emoji} {s['status']}</td>
          <td>{pr_cell} {error_cell}</td>
          <td>{_duration(s['duration_seconds'])}</td>
          <td style="font-size:11px;color:#888">{s['started_at'][:16].replace('T', ' ')}</td>
        </tr>"""

    empty_row = (
        '<tr><td colspan="7" style="text-align:center;color:#8b949e;padding:32px">'
        'No sessions yet. Label an issue with <strong>devin-fix</strong> to get started.'
        '</td></tr>'
    )

    type_section = ""
    if type_cards:
        type_section = (
            '<div class="divider"></div>'
            '<div class="metrics">'
            '<div class="section-label" style="width:100%;padding:0">By Issue Type</div>'
            + type_cards +
            '</div>'
        )

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
    header h1 {{ margin: 0; font-size: 20px; }}
    .header-meta {{ text-align: right; font-size: 12px; color: #8b949e; line-height: 1.8; }}
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
    td {{ padding: 10px 14px; font-size: 13px; border-bottom: 1px solid #f0f0f0; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #f6f8fa; }}
    a {{ color: #0969da; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .footer {{ color: #8b949e; font-size: 12px; padding: 0 32px 24px; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>🤖 Devin Automation Dashboard</h1>
      <div style="font-size:13px;color:#8b949e;margin-top:4px">
        apache/superset · github.com/Mauricec95/superset
      </div>
    </div>
    <div class="header-meta">
      <div>{system_status} &nbsp;System running</div>
      <div>Last updated: {now}</div>
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
  <div class="section-label">Session Log</div>

  <table>
    <thead>
      <tr>
        <th>Issue</th><th>Title</th><th>Type</th><th>Status</th>
        <th>Pull Request</th><th>Duration</th><th>Started (UTC)</th>
      </tr>
    </thead>
    <tbody>
      {rows if rows else empty_row}
    </tbody>
  </table>

  <div class="footer">Auto-refreshes every 30 seconds &nbsp;·&nbsp;
    <a href="/api/sessions">JSON API</a> &nbsp;·&nbsp;
    <a href="https://github.com/Mauricec95/devin-automation" target="_blank">Source</a>
  </div>
</body>
</html>"""
