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


def render_dashboard() -> str:
    sessions = get_all_sessions()

    total = len(sessions)
    success = sum(1 for s in sessions if s["status"] == "success")
    failed = sum(1 for s in sessions if s["status"] == "failed")
    running = sum(1 for s in sessions if s["status"] == "running")
    durations = [s["duration_seconds"] for s in sessions if s["duration_seconds"]]
    avg_duration = int(sum(durations) / len(durations)) if durations else None

    rows = ""
    for s in sessions:
        emoji = STATUS_EMOJI.get(s["status"], "❓")
        type_color = TYPE_BADGE.get(s["issue_type"], "#888")
        pr_cell = (
            f'<a href="{s["pr_url"]}" target="_blank">#{s["pr_number"]}</a>'
            if s["pr_url"]
            else "—"
        )
        error_cell = f'<span title="{s["error"]}" style="color:#d73a4a">error</span>' if s["error"] else ""
        rows += f"""
        <tr>
          <td><a href="https://github.com/Mauricec95/superset/issues/{s['issue_number']}"
                 target="_blank">#{s['issue_number']}</a></td>
          <td style="max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="{s['issue_title']}">{s['issue_title']}</td>
          <td>{_badge(s['issue_type'], type_color)}</td>
          <td>{emoji} {s['status']}</td>
          <td>{pr_cell} {error_cell}</td>
          <td>{_duration(s['duration_seconds'])}</td>
          <td style="font-size:11px;color:#888">{s['started_at'][:16].replace('T',' ')}</td>
        </tr>"""

    success_rate = f"{int(success / total * 100)}%" if total else "—"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="30">
  <title>Devin Automation Dashboard</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           margin: 0; background: #f6f8fa; color: #24292f; }}
    header {{ background: #24292f; color: #fff; padding: 16px 32px;
              display: flex; align-items: center; gap: 12px; }}
    header h1 {{ margin: 0; font-size: 20px; }}
    .subtitle {{ font-size: 13px; color: #8b949e; }}
    .metrics {{ display: flex; gap: 16px; padding: 24px 32px; flex-wrap: wrap; }}
    .card {{ background: #fff; border: 1px solid #d0d7de; border-radius: 8px;
             padding: 16px 24px; min-width: 140px; text-align: center; }}
    .card .value {{ font-size: 32px; font-weight: 700; }}
    .card .label {{ font-size: 13px; color: #57606a; margin-top: 4px; }}
    .green {{ color: #1a7f37; }}
    .red {{ color: #d1242f; }}
    .blue {{ color: #0969da; }}
    table {{ width: calc(100% - 64px); margin: 0 32px 32px;
             border-collapse: collapse; background: #fff;
             border: 1px solid #d0d7de; border-radius: 8px; overflow: hidden; }}
    th {{ background: #f6f8fa; padding: 10px 14px; text-align: left;
          font-size: 13px; border-bottom: 1px solid #d0d7de; }}
    td {{ padding: 10px 14px; font-size: 13px; border-bottom: 1px solid #f0f0f0; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #f6f8fa; }}
    a {{ color: #0969da; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .refresh-note {{ color: #8b949e; font-size: 12px; padding: 0 32px 16px; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>🤖 Devin Automation Dashboard</h1>
      <div class="subtitle">Superset · github.com/Mauricec95/superset</div>
    </div>
  </header>

  <div class="metrics">
    <div class="card"><div class="value">{total}</div><div class="label">Total Sessions</div></div>
    <div class="card"><div class="value green">{success}</div><div class="label">Succeeded</div></div>
    <div class="card"><div class="value red">{failed}</div><div class="label">Failed</div></div>
    <div class="card"><div class="value blue">{running}</div><div class="label">Running</div></div>
    <div class="card"><div class="value">{success_rate}</div><div class="label">Success Rate</div></div>
    <div class="card"><div class="value">{_duration(avg_duration)}</div><div class="label">Avg Time to PR</div></div>
  </div>

  <p class="refresh-note">Auto-refreshes every 30 seconds.</p>

  <table>
    <thead>
      <tr>
        <th>Issue</th><th>Title</th><th>Type</th><th>Status</th>
        <th>Pull Request</th><th>Duration</th><th>Started</th>
      </tr>
    </thead>
    <tbody>
      {"".join(rows) if rows else '<tr><td colspan="7" style="text-align:center;color:#8b949e;padding:32px">No sessions yet. Label an issue with <strong>devin-fix</strong> to get started.</td></tr>'}
    </tbody>
  </table>
</body>
</html>"""
