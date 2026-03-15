#!/usr/bin/env python3
"""Generate Paperclip dashboard HTML from API data."""
import json
import urllib.request
from datetime import datetime, timezone, timedelta

COMPANY_ID = "97a949aa-2a77-4bbe-ba47-e341d2f924bb"
BASE = "http://127.0.0.1:3100/api"
SAST = timezone(timedelta(hours=2))

def api(path):
    try:
        r = urllib.request.urlopen(f"{BASE}/companies/{COMPANY_ID}/{path}", timeout=5)
        return json.loads(r.read())
    except:
        return []

agents = api("agents")
issues = [i for i in api("issues") if i.get("status") != "cancelled"]
projects = api("projects")
goals = api("goals")
now = datetime.now(SAST).strftime("%d %b %Y, %H:%M SAST")

agent_map = {a["id"]: a for a in agents}
proj_map = {p["id"]: p for p in projects}

proj_issues = {}
for i in issues:
    pid = i.get("projectId", "none")
    proj_issues.setdefault(pid, []).append(i)

pri_colors = {"critical": "#ef4444", "high": "#f97316", "medium": "#eab308", "low": "#22c55e"}
stat_colors = {"backlog": "#6b7280", "todo": "#a3a3a3", "in_progress": "#3b82f6", "review": "#8b5cf6", "done": "#22c55e"}
icon_map = {"crown": "👑", "telescope": "🔭", "microscope": "🔬", "circuit-board": "⚡", "sparkles": "✨", "shield": "🛡️"}
proj_colors = {"Expand Onelife": "#10b981", "Polymarket Trading": "#8b5cf6", "JARVIS AI": "#f59e0b"}

model_map = {}
for a in agents:
    cfg = a.get("adapterConfig", {})
    tpl = cfg.get("payloadTemplate", {})
    model_map[a["id"]] = tpl.get("model", "—")

total = len(issues)
critical = sum(1 for i in issues if i.get("priority") == "critical")
high = sum(1 for i in issues if i.get("priority") == "high")
in_progress = sum(1 for i in issues if i.get("status") == "in_progress")
done_count = sum(1 for i in issues if i.get("status") == "done")

agent_cards = ""
for a in agents:
    icon = icon_map.get(a.get("icon",""), "🤖")
    adapter = a.get("adapterType", "none")
    wired = "🟢 wired" if adapter == "openclaw_gateway" else "⚪ offline"
    model = model_map.get(a["id"], "—").split("/")[-1] if "/" in model_map.get(a["id"], "") else model_map.get(a["id"], "—")
    task_count = sum(1 for i in issues if i.get("assigneeAgentId") == a["id"])
    agent_cards += f'''
    <div class="agent-card">
        <div class="agent-icon">{icon}</div>
        <div class="agent-name">{a["name"]}</div>
        <div class="agent-role">{a.get("title", a["role"])}</div>
        <div class="agent-model">{model}</div>
        <div class="agent-status">{wired}</div>
        <div class="agent-tasks">{task_count} tasks</div>
    </div>'''

goal_cards = ""
for g in goals:
    goal_cards += f'''
    <div class="goal-card">
        <div class="goal-title">{g["title"]}</div>
        <div class="goal-target">{g.get("description","")}</div>
    </div>'''

project_sections = ""
for p in projects:
    pid = p["id"]
    p_issues = proj_issues.get(pid, [])
    color = proj_colors.get(p["name"], "#6b7280")
    
    rows = ""
    for i in sorted(p_issues, key=lambda x: ["critical","high","medium","low"].index(x.get("priority","medium"))):
        pri = i.get("priority", "medium")
        status = i.get("status", "backlog")
        aid = i.get("assigneeAgentId", "")
        agent = agent_map.get(aid, {})
        agent_name = agent.get("name", "—")
        agent_icon = icon_map.get(agent.get("icon",""), "")
        pri_color = pri_colors.get(pri, "#6b7280")
        stat_color = stat_colors.get(status, "#6b7280")
        rows += f'''
        <tr>
            <td><span class="badge" style="background:{pri_color}">{pri}</span></td>
            <td class="issue-title">{i.get("identifier","")}: {i["title"]}</td>
            <td><span class="badge" style="background:{stat_color}">{status.replace("_"," ")}</span></td>
            <td>{agent_icon} {agent_name}</td>
        </tr>'''
    
    project_sections += f'''
    <div class="proj-header">
      <div class="proj-dot" style="background:{color}"></div>
      <div class="proj-name">{p["name"]}</div>
      <div class="proj-count">{len(p_issues)} tasks</div>
    </div>
    <table>
      <thead><tr><th>Priority</th><th>Task</th><th>Status</th><th>Agent</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>'''

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Onelife Intelligence — Command Center</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#0a0a0a; color:#e5e5e5; min-height:100vh; }}
  .container {{ max-width:1200px; margin:0 auto; padding:16px; }}
  .header {{ text-align:center; padding:24px 0 16px; border-bottom:1px solid #262626; margin-bottom:24px; }}
  .header h1 {{ font-size:24px; font-weight:700; background:linear-gradient(135deg,#6366f1,#8b5cf6,#f59e0b); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
  .header .sub {{ color:#737373; font-size:13px; margin-top:4px; }}
  .header .updated {{ color:#525252; font-size:11px; margin-top:8px; }}
  .stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:24px; }}
  .stat {{ background:#171717; border:1px solid #262626; border-radius:12px; padding:16px; text-align:center; }}
  .stat .num {{ font-size:28px; font-weight:700; }}
  .stat .label {{ font-size:11px; color:#737373; text-transform:uppercase; letter-spacing:1px; margin-top:4px; }}
  .section {{ margin-bottom:24px; }}
  .section h2 {{ font-size:16px; font-weight:600; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #262626; }}
  .agents {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:12px; }}
  .agent-card {{ background:#171717; border:1px solid #262626; border-radius:12px; padding:14px 10px; text-align:center; }}
  .agent-icon {{ font-size:28px; margin-bottom:6px; }}
  .agent-name {{ font-weight:600; font-size:14px; }}
  .agent-role {{ color:#737373; font-size:10px; margin-top:2px; }}
  .agent-model {{ color:#6366f1; font-size:10px; margin-top:4px; font-family:monospace; }}
  .agent-status {{ font-size:11px; margin-top:6px; }}
  .agent-tasks {{ color:#525252; font-size:10px; margin-top:2px; }}
  .goals {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; }}
  .goal-card {{ background:#171717; border:1px solid #262626; border-radius:12px; padding:16px; }}
  .goal-title {{ font-weight:600; font-size:14px; }}
  .goal-target {{ color:#737373; font-size:12px; margin-top:6px; line-height:1.4; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{ text-align:left; font-size:10px; color:#737373; text-transform:uppercase; letter-spacing:1px; padding:8px 10px; border-bottom:1px solid #262626; }}
  td {{ padding:10px; border-bottom:1px solid #1a1a1a; font-size:13px; }}
  .issue-title {{ font-weight:500; max-width:400px; }}
  .badge {{ display:inline-block; padding:2px 8px; border-radius:6px; font-size:10px; font-weight:600; color:#fff; }}
  .proj-header {{ display:flex; align-items:center; gap:8px; margin:20px 0 8px; }}
  .proj-dot {{ width:10px; height:10px; border-radius:50%; }}
  .proj-name {{ font-weight:600; font-size:14px; }}
  .proj-count {{ color:#525252; font-size:12px; }}
  .footer {{ text-align:center; padding:24px; color:#404040; font-size:11px; }}
  @media (max-width:600px) {{
    .stats {{ grid-template-columns:repeat(2,1fr); }}
    .agents {{ grid-template-columns:repeat(3,1fr); }}
    .agent-card {{ padding:10px 6px; }}
    .agent-icon {{ font-size:22px; }}
    .agent-name {{ font-size:12px; }}
    .agent-role {{ font-size:9px; }}
    table {{ font-size:11px; }}
    td, th {{ padding:6px 4px; }}
    .issue-title {{ max-width:200px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🦞 Onelife Intelligence</h1>
    <div class="sub">Agent Command Center</div>
    <div class="updated">Last updated: {now}</div>
  </div>
  <div class="stats">
    <div class="stat"><div class="num">{len(agents)}</div><div class="label">Agents</div></div>
    <div class="stat"><div class="num" style="color:#ef4444">{critical}</div><div class="label">Critical</div></div>
    <div class="stat"><div class="num" style="color:#3b82f6">{in_progress}</div><div class="label">In Progress</div></div>
    <div class="stat"><div class="num" style="color:#22c55e">{done_count}</div><div class="label">Done</div></div>
  </div>
  <div class="section">
    <h2>Agent Team</h2>
    <div class="agents">{agent_cards}</div>
  </div>
  <div class="section">
    <h2>Goals</h2>
    <div class="goals">{goal_cards}</div>
  </div>
  <div class="section">
    <h2>Task Board ({total} tasks)</h2>
    {project_sections}
  </div>
  <div class="footer">Onelife Intelligence × Paperclip × OpenClaw</div>
</div>
</body>
</html>'''

with open("/tmp/paperclip-dash/index.html", "w") as f:
    f.write(html)
print(f"Generated: {len(html)} bytes")
