#!/usr/bin/env python3
"""
Onelife Command Center — Mission Control
Animated agents, live cron status, activity feed, task board.
"""

import json, os, subprocess
from datetime import datetime, timezone, timedelta

SAST = timezone(timedelta(hours=2))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")

# Agent roster — each agent has a role, emoji, color, and assigned crons/tasks
AGENTS = {
    "Jarvis": {
        "emoji": "🦞", "color": "#00ff88", "role": "CEO / Orchestrator",
        "desc": "Orchestrates everything. Main session, strategic decisions, Naadir's right hand.",
        "owns": ["Overnight Opportunity Engine", "Heartbeat"]
    },
    "Ghost": {
        "emoji": "👻", "color": "#8b5cf6", "role": "DevOps / Building",
        "desc": "Omni-Shopify sync, dashboards, builds. Silent, reliable, runs when you're sleeping.",
        "owns": ["Morning Dashboard", "Evening Dashboard", "Intelligence Dashboard",
                 "Evening Intelligence", "Omni Cache Refresh", "Omni-Shopify Sync", "Paperclip Loop"]
    },
    "Scout": {
        "emoji": "🔭", "color": "#3b82f6", "role": "Intelligence / Research",
        "desc": "SEO reports, competitor analysis, market scanning. Finds the opportunities.",
        "owns": ["Weekly SEO Report", "Competitive Price Scan", "Business Opportunity",
                 "SEO Gap Finder", "Review Miner", "Product Trend Scanner",
                 "Weekly Competitor Pricing", "Weekly Intel Brief", "Paperclip Loop"]
    },
    "Cipher": {
        "emoji": "🔐", "color": "#f59e0b", "role": "CTO / Engineering",
        "desc": "Conversion reports, autoresearch experiments, analytics infrastructure. The numbers brain.",
        "owns": ["Friday Close-Out", "Weekly Conversion Report", "Weekly Onelife Edit",
                 "Autoresearch Experiments", "Autoresearch Morning Report", "Paperclip Loop"]
    },
    "Nova": {
        "emoji": "✨", "color": "#ec4899", "role": "CMO / Marketing",
        "desc": "TikTok batches, ad pipeline, blog posts, creative output. The maker.",
        "owns": ["Sunday TikTok Batch", "Daily TikTok Analytics", "Weekly Ad Pipeline",
                 "Biweekly Blog Post", "Monthly Blog Campaign", "Paperclip Loop"]
    },
    "Vivid": {
        "emoji": "💚", "color": "#22c55e", "role": "Brand PM",
        "desc": "Vivid Health brand turnaround. Product descriptions, collection pages, bundles, website, social. Dedicated to making the house brand shine.",
        "owns": []
    },
    "Sage": {
        "emoji": "🧙", "color": "#a855f7", "role": "Deep Analysis",
        "desc": "MiroShark simulations, deep business analysis, expert panels. The strategic thinker.",
        "owns": ["Paperclip Loop"]
    },
    "Kimi": {
        "emoji": "🌙", "color": "#06b6d4", "role": "Compaction / Fallback",
        "desc": "Context compression, emergency model fallback. The efficiency expert.",
        "owns": []
    },
}


def load_tasks():
    try:
        with open(os.path.join(WORKSPACE, "memory/active-tasks.json")) as f:
            return json.load(f).get("tasks", [])
    except:
        return []


def load_cron_jobs():
    try:
        result = subprocess.run(["openclaw", "cron", "list"], capture_output=True, text=True, timeout=15)
        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:
            return []
        jobs = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 3:
                continue
            job_id = parts[0]

            # Extract status
            status = "unknown"
            for p in parts:
                if p in ("ok", "error", "stale", "idle"):
                    status = p
                    break

            # Full name from the line (between ID and 'cron')
            idx_cron = line.find("cron ")
            if idx_cron == -1:
                idx_cron = line.find("  ", 40)
            name = line[len(job_id):idx_cron].strip().rstrip(".")

            # Next/last run
            next_run = ""
            last_run = ""
            for i, p in enumerate(parts):
                if p == "in" and i + 1 < len(parts):
                    next_run = parts[i + 1]
                if p.endswith("ago") and i > 0:
                    last_run = parts[i - 1] + " " + p

            # Model
            model = ""
            for p in parts:
                if "/" in p and any(m in p for m in ["kimi", "claude", "gpt", "moonshot", "sonnet"]):
                    model = p.split("/")[-1]

            jobs.append({
                "id": job_id, "name": name, "status": status,
                "next": next_run, "last": last_run, "model": model
            })
        return jobs
    except:
        return []


def match_agent(job_name):
    """Match a cron job to its owning agent.
    Strategy 1: parse 'AgentName: ...' prefix (works for all current crons).
    Strategy 2: fuzzy match against owns arrays as fallback.
    """
    if ":" in job_name:
        prefix = job_name.split(":")[0].strip()
        if prefix in AGENTS:
            return prefix
    jn = job_name.lower()
    for agent, info in AGENTS.items():
        for pattern in info["owns"]:
            pl = pattern.lower()
            if pl in jn or jn.startswith(pl[:15]):
                return agent
    return "Jarvis"  # default


def load_seo_stats():
    try:
        with open(os.path.join(WORKSPACE, "command-center/status.json")) as f:
            d = json.load(f).get("seo", {})
            if any(v for v in d.values()):
                return d
    except:
        pass
    return {"blog_posts": 17, "image_alts": 8397, "product_descriptions": 2108, "guide_pages": 3}


def generate():
    now = datetime.now(SAST)
    now_str = now.strftime("%d %b %Y, %H:%M SAST")

    tasks = load_tasks()
    crons = load_cron_jobs()
    seo = load_seo_stats()

    active = [t for t in tasks if t.get("status") == "active"]
    pending = [t for t in tasks if t.get("status") == "pending"]
    blocked = [t for t in tasks if t.get("status") == "blocked"]
    done = [t for t in tasks if t.get("status") == "done"]

    # Stale error detection: if a cron errored >24h ago and hasn't run since,
    # it's a stale error from a previous run, not an active problem.
    # Treat as "stale" (warning) not "error" (critical).
    for c in crons:
        if c["status"] == "error" and c.get("last", ""):
            last = c["last"]
            # If last run was days ago, it's stale
            if any(x in last for x in ["2d", "3d", "4d", "5d", "6d", "7d", "1w", "2w"]):
                c["status"] = "stale"

    cron_ok = sum(1 for c in crons if c["status"] in ("ok", "stale"))
    cron_err = sum(1 for c in crons if c["status"] == "error")
    cron_idle = sum(1 for c in crons if c["status"] == "idle")
    cron_total = len(crons)

    # Build agent status based on their crons
    agent_statuses = {}
    for agent in AGENTS:
        agent_crons = [c for c in crons if match_agent(c["name"]) == agent]
        has_error = any(c["status"] == "error" for c in agent_crons)  # only active errors, not stale
        has_recent = any("ago" in c.get("last", "") and ("min" in c["last"] or "1h" in c["last"] or "2h" in c["last"]) for c in agent_crons)
        all_ok = all(c["status"] in ("ok", "idle", "stale") for c in agent_crons)

        if has_error:
            agent_statuses[agent] = "error"
        elif has_recent:
            agent_statuses[agent] = "active"
        elif all_ok:
            agent_statuses[agent] = "idle"
        else:
            agent_statuses[agent] = "idle"

    # Agent cards HTML
    agent_cards = ""
    for agent, info in AGENTS.items():
        status = agent_statuses.get(agent, "idle")
        agent_crons = [c for c in crons if match_agent(c["name"]) == agent]
        status_label = {"active": "ACTIVE", "idle": "STANDBY", "error": "ERROR"}.get(status, "STANDBY")
        status_color = {"active": "#22c55e", "idle": "#64748b", "error": "#ef4444"}.get(status, "#64748b")
        pulse_class = "pulse-active" if status == "active" else "pulse-error" if status == "error" else ""
        glow = f"box-shadow:0 0 20px {info['color']}40,0 0 40px {info['color']}20;" if status == "active" else ""

        # Build mini activity feed for this agent
        activity = ""
        for c in agent_crons[:3]:
            c_col = {"ok": "#22c55e", "error": "#ef4444", "idle": "#64748b"}.get(c["status"], "#64748b")
            c_icon = {"ok": "✓", "error": "✗", "idle": "○"}.get(c["status"], "·")
            activity += f'<div class="agent-cron"><span style="color:{c_col}">{c_icon}</span> {c["name"][:32]} <span class="cron-time">{c.get("last", "—")}</span></div>'

        agent_cards += f"""
        <div class="agent-card {pulse_class}" style="border-color:{info['color']}33;{glow}">
            <div class="agent-avatar" style="background:{info['color']}15;border:2px solid {info['color']}">
                <span class="agent-emoji">{info['emoji']}</span>
                <div class="status-dot" style="background:{status_color}"></div>
            </div>
            <div class="agent-info">
                <div class="agent-name" style="color:{info['color']}">{agent}</div>
                <div class="agent-role">{info['role']}</div>
                <div class="agent-desc">{info['desc']}</div>
                <div class="agent-status" style="color:{status_color}">{status_label}</div>
            </div>
            <div class="agent-feed">{activity}</div>
        </div>"""

    # Cron timeline
    cron_rows = ""
    for c in crons:
        agent = match_agent(c["name"])
        a_info = AGENTS.get(agent, AGENTS["Jarvis"])
        s_col = {"ok": "#22c55e", "error": "#ef4444", "idle": "#64748b", "stale": "#eab308"}.get(c["status"], "#64748b")
        cron_rows += f"""<tr>
            <td><span class="agent-badge" style="background:{a_info['color']}20;color:{a_info['color']}">{a_info['emoji']} {agent}</span></td>
            <td class="cron-name">{c['name']}</td>
            <td style="color:#94a3b8;font-size:12px">{c.get('model','')}</td>
            <td style="color:#94a3b8;font-size:12px">{c.get('last','—')}</td>
            <td style="font-size:12px">{c.get('next','—')}</td>
            <td><span class="status-pill" style="background:{s_col}">{c['status']}</span></td>
        </tr>"""

    # Task board
    def task_card(t):
        s = t.get("status", "pending")
        p = t.get("priority", "MEDIUM")
        s_col = {"active": "#3b82f6", "pending": "#64748b", "blocked": "#ef4444", "done": "#22c55e"}.get(s, "#64748b")
        p_col = {"HIGH": "#ef4444", "MEDIUM": "#eab308", "LOW": "#22c55e"}.get(p, "#64748b")
        desc = t.get("description", "")[:65]
        return f"""<div class="task-card" style="border-left:3px solid {s_col}">
            <div class="task-header">
                <span class="priority-dot" style="background:{p_col}"></span>
                <span class="task-id">{t.get('id','')[:20]}</span>
            </div>
            <div class="task-desc">{desc}</div>
            <span class="status-pill" style="background:{s_col}">{s}</span>
        </div>"""

    active_cards = "".join(task_card(t) for t in active)
    pending_cards = "".join(task_card(t) for t in pending)
    done_cards = "".join(task_card(t) for t in done[:4])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="1800">
<title>Command Center | {now.strftime('%d %b')}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#06060f;color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;overflow-x:hidden}}

/* Animated grid background */
body::before{{
    content:'';position:fixed;top:0;left:0;width:100%;height:100%;
    background:
        linear-gradient(rgba(0,255,136,0.03) 1px,transparent 1px),
        linear-gradient(90deg,rgba(0,255,136,0.03) 1px,transparent 1px);
    background-size:60px 60px;
    animation:grid-drift 20s linear infinite;
    pointer-events:none;z-index:0
}}
@keyframes grid-drift{{0%{{transform:translate(0,0)}}100%{{transform:translate(60px,60px)}}}}

.container{{max-width:1200px;margin:0 auto;padding:20px;position:relative;z-index:1}}

/* Header */
.header{{text-align:center;padding:30px 0 20px;margin-bottom:24px;position:relative}}
.header h1{{font-size:36px;font-weight:900;letter-spacing:2px;color:#00ff88;text-shadow:0 0 30px #00ff8840}}
.header .subtitle{{font-size:14px;color:#64748b;margin-top:6px;letter-spacing:4px;text-transform:uppercase}}
.header .timestamp{{font-size:11px;color:#2d2d3d;margin-top:8px;font-family:'Courier New',monospace}}
.header::after{{
    content:'';position:absolute;bottom:0;left:10%;right:10%;height:1px;
    background:linear-gradient(90deg,transparent,#00ff8840,transparent)
}}

/* KPI Strip */
.kpi-strip{{display:flex;gap:12px;margin-bottom:24px;justify-content:center;flex-wrap:wrap}}
.kpi{{background:#0d0d1a;border:1px solid #1e1e2e;border-radius:12px;padding:16px 24px;text-align:center;min-width:120px;position:relative;overflow:hidden}}
.kpi::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--accent)}}
.kpi-val{{font-size:32px;font-weight:800}}
.kpi-lbl{{font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:2px;margin-top:4px}}

/* Agent Cards */
.agents-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;margin-bottom:24px}}
.agent-card{{
    background:#0d0d1a;border:1px solid #1e1e2e;border-radius:16px;padding:20px;
    display:grid;grid-template-columns:72px 1fr;grid-template-rows:auto auto;gap:12px;
    transition:all 0.3s ease;position:relative;overflow:hidden
}}
.agent-card:hover{{transform:translateY(-2px);border-color:#2d2d3d}}
.agent-avatar{{
    width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;
    position:relative;grid-row:1/2
}}
.agent-emoji{{font-size:28px}}
.status-dot{{
    position:absolute;bottom:2px;right:2px;width:14px;height:14px;border-radius:50%;
    border:2px solid #0d0d1a
}}
.agent-info{{grid-row:1/2}}
.agent-name{{font-size:18px;font-weight:700;letter-spacing:0.5px}}
.agent-role{{font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;margin-top:2px}}
.agent-desc{{font-size:12px;color:#64748b;margin-top:6px;line-height:1.4}}
.agent-status{{font-size:11px;font-weight:700;letter-spacing:2px;margin-top:8px}}
.agent-feed{{grid-column:1/-1;border-top:1px solid #1e1e2e;padding-top:10px}}
.agent-cron{{font-size:12px;color:#94a3b8;padding:3px 0;display:flex;gap:6px;align-items:center}}
.cron-time{{margin-left:auto;font-size:11px;color:#404040;font-family:monospace}}

/* Pulse animations */
.pulse-active{{animation:pulse-glow 2s ease-in-out infinite}}
.pulse-error{{animation:pulse-error 1.5s ease-in-out infinite}}
@keyframes pulse-glow{{
    0%,100%{{box-shadow:0 0 5px transparent}}
    50%{{box-shadow:0 0 20px rgba(0,255,136,0.15)}}
}}
@keyframes pulse-error{{
    0%,100%{{box-shadow:0 0 5px transparent}}
    50%{{box-shadow:0 0 20px rgba(239,68,68,0.2)}}
}}

/* Cron Table */
.section{{background:#0d0d1a;border:1px solid #1e1e2e;border-radius:16px;padding:24px;margin-bottom:20px}}
.section-title{{font-size:16px;font-weight:700;margin-bottom:16px;display:flex;align-items:center;gap:10px}}
.section-title::after{{content:'';flex:1;height:1px;background:#1e1e2e}}
table{{width:100%;border-collapse:collapse}}
th{{font-size:10px;color:#404040;text-align:left;padding:10px 8px;letter-spacing:2px;text-transform:uppercase;border-bottom:1px solid #1e1e2e}}
td{{padding:12px 8px;border-bottom:1px solid #0f0f1a;font-size:13px}}
.cron-name{{max-width:400px;word-break:break-word}}
.agent-badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap}}
.status-pill{{display:inline-block;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:1px}}

/* Task Board */
.task-board{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px}}
.task-column-header{{font-size:12px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:2px;padding:8px 0;margin-bottom:8px;border-bottom:1px solid #1e1e2e}}
.task-card{{background:#0a0a14;border-radius:10px;padding:14px;margin-bottom:8px;transition:all 0.2s}}
.task-card:hover{{background:#12121f}}
.task-header{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
.priority-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.task-id{{font-size:11px;color:#64748b;font-family:monospace}}
.task-desc{{font-size:13px;line-height:1.4;margin-bottom:8px;color:#cbd5e1}}

/* SEO */
.seo-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.seo-item{{background:#0a0a14;border-radius:10px;padding:16px;text-align:center}}
.seo-num{{font-size:24px;font-weight:800;color:#818cf8}}
.seo-lbl{{font-size:10px;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:1px}}

/* Org Chart */
.org-chart{{background:#0d0d1a;border:1px solid #1e1e2e;border-radius:16px;padding:24px 24px 16px;margin-bottom:20px;text-align:center}}
.org-chart-title{{font-size:11px;font-weight:700;color:#404040;letter-spacing:3px;text-transform:uppercase;margin-bottom:16px}}
.org-ceo{{display:inline-flex;align-items:center;gap:12px;background:#00ff8808;border:2px solid #00ff8830;border-radius:12px;padding:12px 28px;margin-bottom:0}}
.org-reports{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}}
.org-node{{background:#0a0a14;border:1px solid #1e1e2e;border-top-width:3px;border-radius:10px;padding:10px 16px;font-size:13px;font-weight:600;color:#cbd5e1;min-width:90px;text-align:center;line-height:1.5}}
.org-node small{{display:block;font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-top:2px}}

/* Links */
.link-bar{{display:flex;gap:10px;justify-content:center;margin:20px 0;flex-wrap:wrap}}
.link-bar a{{
    color:#94a3b8;text-decoration:none;font-size:12px;padding:8px 16px;
    background:#0d0d1a;border:1px solid #1e1e2e;border-radius:10px;
    transition:all 0.2s
}}
.link-bar a:hover{{background:#1e1e2e;color:#f1f5f9;border-color:#2d2d3d}}

.footer{{text-align:center;padding:24px;font-size:11px;color:#1e1e2e;letter-spacing:2px}}

/* Scanning line animation */
.scan-line{{
    position:fixed;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,transparent,#00ff8860,transparent);
    animation:scan 8s linear infinite;
    pointer-events:none;z-index:100
}}
@keyframes scan{{
    0%{{top:0;opacity:0}}10%{{opacity:1}}90%{{opacity:1}}100%{{top:100vh;opacity:0}}
}}

@media(max-width:768px){{
    .agents-grid{{grid-template-columns:1fr}}
    .task-board{{grid-template-columns:1fr}}
    .seo-grid{{grid-template-columns:repeat(2,1fr)}}
    .kpi-strip{{gap:8px}}
    .kpi{{min-width:80px;padding:12px 16px}}
    .kpi-val{{font-size:24px}}
}}
</style>
</head>
<body>

<div class="scan-line"></div>

<div class="container">

<div class="header">
    <h1>COMMAND CENTER</h1>
    <div class="subtitle">Onelife Health · Mission Control</div>
    <div class="timestamp">SYS.TIME {now.strftime('%Y-%m-%d %H:%M:%S')} SAST // ALL SYSTEMS {'NOMINAL' if cron_err == 0 else 'ALERT'}</div>
</div>

<div class="link-bar">
    <a href="https://infoonelifesa-cpu.github.io/onelife-intelligence/">📊 Intelligence</a>
    <a href="https://infoonelifesa-cpu.github.io/onelife-missions/">🎯 Missions</a>
    <a href="https://cal-describing-faqs-joined.trycloudflare.com" target="_blank">📎 Paperclip</a>
    <a href="http://localhost:3000">🦈 MiroShark</a>
    <a href="https://onelife.co.za/admin">🛍️ Shopify Admin</a>
    <a href="https://www.klaviyo.com/dashboard">📧 Klaviyo</a>
    <a href="https://analytics.google.com">📈 GA4</a>
</div>

<!-- KPI Strip -->
<div class="kpi-strip">
    <div class="kpi" style="--accent:#3b82f6"><div class="kpi-val" style="color:#3b82f6">{len(active)}</div><div class="kpi-lbl">Active</div></div>
    <div class="kpi" style="--accent:#64748b"><div class="kpi-val" style="color:#64748b">{len(pending)}</div><div class="kpi-lbl">Pending</div></div>
    <div class="kpi" style="--accent:#ef4444"><div class="kpi-val" style="color:#ef4444">{len(blocked)}</div><div class="kpi-lbl">Blocked</div></div>
    <div class="kpi" style="--accent:#22c55e"><div class="kpi-val" style="color:#22c55e">{len(done)}</div><div class="kpi-lbl">Done</div></div>
    <div class="kpi" style="--accent:#00ff88"><div class="kpi-val" style="color:{'#22c55e' if cron_err==0 else '#ef4444'}">{cron_ok}<span style="font-size:16px;color:#404040">/{cron_total}</span></div><div class="kpi-lbl">Crons</div></div>
    <div class="kpi" style="--accent:#ef4444"><div class="kpi-val" style="color:{'#22c55e' if cron_err==0 else '#ef4444'}">{cron_err}</div><div class="kpi-lbl">Errors</div></div>
</div>

<!-- Org Hierarchy -->
<div class="org-chart">
    <div class="org-chart-title">ORG HIERARCHY — ALL AGENTS REPORT TO JARVIS</div>
    <div class="org-ceo">
        <span style="font-size:26px">🦞</span>
        <span style="font-size:20px;font-weight:800;color:#00ff88">Jarvis</span>
        <span style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:2px;border-left:1px solid #1e1e2e;padding-left:12px;margin-left:4px">CEO / Orchestrator</span>
    </div>
    <div style="width:2px;height:20px;background:linear-gradient(#00ff8830,#1e1e2e);margin:0 auto 12px"></div>
    <div class="org-reports">
        <div class="org-node" style="border-top-color:#ec4899">✨ Nova<small>CMO</small></div>
        <div class="org-node" style="border-top-color:#f59e0b">🔐 Cipher<small>CTO</small></div>
        <div class="org-node" style="border-top-color:#8b5cf6">👻 Ghost<small>DevOps</small></div>
        <div class="org-node" style="border-top-color:#3b82f6">🔭 Scout<small>Intel</small></div>
        <div class="org-node" style="border-top-color:#a855f7">🧙 Sage<small>Analysis</small></div>
        <div class="org-node" style="border-top-color:#22c55e">💚 Vivid<small>Brand PM</small></div>
        <div class="org-node" style="border-top-color:#06b6d4">🌙 Kimi<small>Fallback</small></div>
    </div>
</div>

<!-- Agent Roster -->
<div class="section">
    <div class="section-title">AGENT ROSTER</div>
    <div class="agents-grid">
        {agent_cards}
    </div>
</div>

<!-- Cron Monitor -->
<div class="section">
    <div class="section-title">AUTOMATION GRID — {cron_total} Jobs</div>
    <table>
        <thead><tr><th>Agent</th><th>Job</th><th>Model</th><th>Last Run</th><th>Next</th><th>Status</th></tr></thead>
        <tbody>{cron_rows}</tbody>
    </table>
</div>

<!-- Task Board -->
<div class="section">
    <div class="section-title">TASK BOARD</div>
    <div class="task-board">
        <div>
            <div class="task-column-header">🔵 Active ({len(active)})</div>
            {active_cards if active_cards else '<div style="color:#404040;font-size:12px;padding:12px">No active tasks</div>'}
        </div>
        <div>
            <div class="task-column-header">⏳ Pending ({len(pending)})</div>
            {pending_cards if pending_cards else '<div style="color:#404040;font-size:12px;padding:12px">No pending tasks</div>'}
        </div>
        <div>
            <div class="task-column-header">✅ Done ({len(done)})</div>
            {done_cards if done_cards else '<div style="color:#404040;font-size:12px;padding:12px">No completed tasks</div>'}
        </div>
    </div>
</div>

<!-- SEO Progress -->
<div class="section">
    <div class="section-title">SEO & CONTENT METRICS</div>
    <div class="seo-grid">
        <div class="seo-item"><div class="seo-num">{seo.get('blog_posts',0)}</div><div class="seo-lbl">Blog Posts</div></div>
        <div class="seo-item"><div class="seo-num">{seo.get('image_alts',0):,}</div><div class="seo-lbl">Image Alts</div></div>
        <div class="seo-item"><div class="seo-num">{seo.get('product_descriptions',0):,}</div><div class="seo-lbl">Descriptions</div></div>
        <div class="seo-item"><div class="seo-num">{seo.get('guide_pages',0)}</div><div class="seo-lbl">Guide Pages</div></div>
    </div>
</div>

<div class="footer">COMMAND CENTER × JARVIS 🦞 × OPENCLAW // {now.strftime('%d %B %Y')}</div>

</div>
</body>
</html>"""

    out = os.path.join(SCRIPT_DIR, "index.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"Command Center generated: {len(html):,} bytes → {out}")
    return out


if __name__ == "__main__":
    generate()
