#!/usr/bin/env python3
"""
Onelife Command Center — clean executive operations console.

This generator intentionally avoids the old neon/gamer treatment. The page should
read like a useful owner dashboard: crisp hierarchy, strong contrast, compact
cards, and fast scanning on mobile and desktop.
"""

import html as html_lib
import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from string import Template

SAST = timezone(timedelta(hours=2))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")


AGENTS = {
    "Jarvis": {
        "emoji": "🦞",
        "color": "#0f8a52",
        "role": "CEO / Orchestrator",
        "desc": "Owns prioritisation, handoffs, and the operator layer around Naadir.",
        "owns": ["Overnight Opportunity Engine", "Heartbeat"],
    },
    "Ghost": {
        "emoji": "👻",
        "color": "#6d5dfc",
        "role": "DevOps / Building",
        "desc": "Keeps dashboards, syncs, builds, and routine plumbing alive.",
        "owns": [
            "Morning Dashboard",
            "Evening Dashboard",
            "Intelligence Dashboard",
            "Evening Intelligence",
            "Omni Cache Refresh",
            "Omni-Shopify Sync",
            "Paperclip Loop",
        ],
    },
    "Scout": {
        "emoji": "🔭",
        "color": "#2563eb",
        "role": "Intelligence / Research",
        "desc": "Finds competitors, pricing moves, SEO gaps, and market signals.",
        "owns": [
            "Weekly SEO Report",
            "Competitive Price Scan",
            "Business Opportunity",
            "SEO Gap Finder",
            "Review Miner",
            "Product Trend Scanner",
            "Weekly Competitor Pricing",
            "Weekly Intel Brief",
            "Paperclip Loop",
        ],
    },
    "Cipher": {
        "emoji": "🔐",
        "color": "#c47a00",
        "role": "CTO / Engineering",
        "desc": "Analytics, experiments, conversion checks, and technical strategy.",
        "owns": [
            "Friday Close-Out",
            "Weekly Conversion Report",
            "Weekly Onelife Edit",
            "Autoresearch Experiments",
            "Autoresearch Morning Report",
            "Paperclip Loop",
        ],
    },
    "Nova": {
        "emoji": "✨",
        "color": "#db2777",
        "role": "CMO / Marketing",
        "desc": "Creative output, TikTok batches, ads, blogs, and campaigns.",
        "owns": [
            "Sunday TikTok Batch",
            "Daily TikTok Analytics",
            "Weekly Ad Pipeline",
            "Biweekly Blog Post",
            "Monthly Blog Campaign",
            "Paperclip Loop",
        ],
    },
    "Vivid": {
        "emoji": "💚",
        "color": "#16a34a",
        "role": "Brand PM",
        "desc": "Dedicated owner for the Vivid Health turnaround and product polish.",
        "owns": [],
    },
    "Sage": {
        "emoji": "🧙",
        "color": "#9333ea",
        "role": "Deep Analysis",
        "desc": "Simulations, expert panels, and deeper business reasoning.",
        "owns": ["Paperclip Loop"],
    },
    "Kimi": {
        "emoji": "🌙",
        "color": "#0891b2",
        "role": "Compaction / Fallback",
        "desc": "Context compression, fallback runs, and long-context efficiency.",
        "owns": [],
    },
}


STATUS_META = {
    "ok": {"label": "OK", "class": "ok", "icon": "✓"},
    "active": {"label": "Active", "class": "active", "icon": "●"},
    "idle": {"label": "Standby", "class": "idle", "icon": "○"},
    "stale": {"label": "Stale", "class": "warn", "icon": "!"},
    "error": {"label": "Error", "class": "danger", "icon": "!"},
    "unknown": {"label": "Unknown", "class": "idle", "icon": "?"},
}


def esc(value):
    if value is None:
        return ""
    return html_lib.escape(str(value), quote=True)


def truncate(value, limit):
    text = str(value or "")
    return text if len(text) <= limit else text[: max(0, limit - 1)].rstrip() + "…"


def load_json(path, fallback):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return fallback


def load_paperclip_public_url():
    data = load_json(os.path.join(WORKSPACE, "memory", "paperclip_public_url.json"), {})
    url = str(data.get("url") or "").strip()
    status = str(data.get("status") or "").strip().lower()
    return url if url and status == "live" else None


def load_tasks():
    data = load_json(os.path.join(WORKSPACE, "memory", "active-tasks.json"), {"tasks": []})
    return data.get("tasks", []) if isinstance(data, dict) else []


def load_cron_jobs():
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception:
        return []

    lines = [line.rstrip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return []

    jobs = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 2:
            continue

        job_id = parts[0]
        status = "unknown"
        for token in parts:
            if token in ("ok", "error", "stale", "idle"):
                status = token
                break

        # Name is the text between the id and the schedule/status columns.
        idx_cron = line.find(" cron ")
        idx_every = line.find(" every ")
        cut_points = [idx for idx in (idx_cron, idx_every) if idx != -1]
        cut = min(cut_points) if cut_points else max(line.find("  ", len(job_id)), len(job_id))
        name = line[len(job_id):cut].strip().rstrip(".") or job_id

        next_run = ""
        last_run = ""
        for i, token in enumerate(parts):
            if token == "in" and i + 1 < len(parts):
                next_run = parts[i + 1]
            if token.endswith("ago") and i > 0:
                last_run = f"{parts[i - 1]} {token}"

        model = ""
        for token in parts:
            if "/" in token and any(m in token for m in ("kimi", "claude", "gpt", "moonshot", "sonnet")):
                model = token.split("/")[-1]

        jobs.append(
            {
                "id": job_id,
                "name": name,
                "status": status,
                "next": next_run or "—",
                "last": last_run or "—",
                "model": model,
            }
        )
    return jobs


def match_agent(job_name):
    if ":" in job_name:
        prefix = job_name.split(":", 1)[0].strip()
        if prefix in AGENTS:
            return prefix

    lowered = job_name.lower()
    for agent, info in AGENTS.items():
        for pattern in info["owns"]:
            p = pattern.lower()
            if p in lowered or lowered.startswith(p[:15]):
                return agent
    return "Jarvis"


def load_seo_stats():
    data = load_json(os.path.join(WORKSPACE, "command-center", "status.json"), {})
    seo = data.get("seo", {}) if isinstance(data, dict) else {}
    if isinstance(seo, dict) and any(seo.values()):
        return seo
    return {"blog_posts": 17, "image_alts": 8397, "product_descriptions": 2108, "guide_pages": 3}


def normalise_stale_cron_errors(crons):
    for cron in crons:
        last = cron.get("last", "")
        if cron.get("status") == "error" and any(x in last for x in ("2d", "3d", "4d", "5d", "6d", "7d", "1w", "2w")):
            cron["status"] = "stale"


def agent_status(agent, crons):
    owned = [c for c in crons if match_agent(c["name"]) == agent]
    if any(c["status"] == "error" for c in owned):
        return "error"
    if any("ago" in c.get("last", "") and ("min" in c["last"] or "1h" in c["last"] or "2h" in c["last"]) for c in owned):
        return "active"
    return "idle"


def status_pill(status):
    meta = STATUS_META.get(status, STATUS_META["unknown"])
    return f'<span class="pill {meta["class"]}">{esc(meta["label"])}</span>'


def render_link_bar(paperclip_url):
    paperclip = (
        f'<a class="primary-link" href="{esc(paperclip_url)}" target="_blank" rel="noopener noreferrer">📎 Paperclip</a>'
        if paperclip_url
        else '<span class="primary-link muted">📎 Paperclip offline</span>'
    )
    links = [
        paperclip,
        '<a href="https://infoonelifesa-cpu.github.io/onelife-intelligence/daily.html">📋 Daily Summary</a>',
        '<a href="https://infoonelifesa-cpu.github.io/onelife-intelligence/cash-integrity.html">🔒 Cash Integrity</a>',
        '<a href="https://infoonelifesa-cpu.github.io/onelife-intelligence/">📊 Intelligence</a>',
        '<a href="https://infoonelifesa-cpu.github.io/onelife-missions/">🎯 Missions</a>',
    ]
    return "\n".join(links)


def render_kpi_cards(active, pending, blocked, done, cron_ok, cron_total, cron_err):
    cards = [
        ("Active tasks", len(active), "blue", "Currently moving"),
        ("Pending", len(pending), "slate", "Waiting their turn"),
        ("Blocked", len(blocked), "red", "Needs attention"),
        ("Completed", len(done), "green", "Closed items"),
        ("Cron health", f"{cron_ok}/{cron_total}", "green" if cron_err == 0 else "red", "Healthy automations" if cron_err == 0 else "Automation alerts"),
        ("Errors", cron_err, "red" if cron_err else "green", "Active failures" if cron_err else "No active failures"),
    ]
    return "\n".join(
        f'''
        <article class="kpi-card accent-{tone}">
            <div class="kpi-label">{esc(label)}</div>
            <div class="kpi-value">{esc(value)}</div>
            <div class="kpi-note">{esc(note)}</div>
        </article>'''
        for label, value, tone, note in cards
    )


def render_agent_cards(crons):
    cards = []
    for agent, info in AGENTS.items():
        owned = [c for c in crons if match_agent(c["name"]) == agent]
        status = agent_status(agent, crons)
        meta = STATUS_META["active" if status == "active" else status]
        recent = owned[:3]
        if recent:
            activity = "\n".join(
                f'''
                <li>
                    <span class="activity-dot {STATUS_META.get(c['status'], STATUS_META['unknown'])['class']}">{esc(STATUS_META.get(c['status'], STATUS_META['unknown'])['icon'])}</span>
                    <span title="{esc(c['name'])}">{esc(truncate(c['name'], 44))}</span>
                    <time>{esc(c.get('last', '—'))}</time>
                </li>'''
                for c in recent
            )
        else:
            activity = '<li class="quiet-line">No cron ownership yet</li>'

        cards.append(
            f'''
            <article class="agent-card" style="--agent:{esc(info['color'])}">
                <div class="agent-topline">
                    <div class="agent-avatar">{esc(info['emoji'])}</div>
                    <div>
                        <h3>{esc(agent)}</h3>
                        <p>{esc(info['role'])}</p>
                    </div>
                    <span class="agent-status {meta['class']}">{esc(meta['label'])}</span>
                </div>
                <p class="agent-desc">{esc(info['desc'])}</p>
                <ul class="activity-list">{activity}</ul>
            </article>'''
        )
    return "\n".join(cards)


def render_cron_rows(crons):
    if not crons:
        return '<tr><td colspan="6" class="empty-table">Cron list unavailable</td></tr>'

    rows = []
    for cron in crons:
        agent = match_agent(cron["name"])
        info = AGENTS.get(agent, AGENTS["Jarvis"])
        meta = STATUS_META.get(cron["status"], STATUS_META["unknown"])
        rows.append(
            f'''
            <tr>
                <td><span class="agent-chip" style="--agent:{esc(info['color'])}">{esc(info['emoji'])} {esc(agent)}</span></td>
                <td class="job-name">{esc(cron['name'])}</td>
                <td>{esc(cron.get('model') or '—')}</td>
                <td>{esc(cron.get('last') or '—')}</td>
                <td>{esc(cron.get('next') or '—')}</td>
                <td><span class="pill {meta['class']}">{esc(meta['label'])}</span></td>
            </tr>'''
        )
    return "\n".join(rows)


def render_task_card(task):
    status = task.get("status", "pending")
    priority = task.get("priority", "MEDIUM")
    desc = task.get("description", "")[:110]
    tone = {"active": "blue", "pending": "slate", "blocked": "red", "done": "green"}.get(status, "slate")
    return f'''
    <article class="task-card accent-{tone}">
        <div class="task-meta">
            <span>{esc(priority)}</span>
            <span>{esc(task.get('id', '')[:22])}</span>
        </div>
        <p>{esc(desc)}</p>
        {status_pill(status)}
    </article>'''


def render_task_column(title, tasks, empty_text):
    body = "\n".join(render_task_card(t) for t in tasks) if tasks else f'<div class="empty-state">{esc(empty_text)}</div>'
    return f'''
    <section class="task-column">
        <h3>{esc(title)} <span>{len(tasks)}</span></h3>
        {body}
    </section>'''


def render_seo_items(seo):
    items = [
        ("Blog posts", seo.get("blog_posts", 0)),
        ("Image alts", f"{int(seo.get('image_alts', 0)):,}" if str(seo.get("image_alts", 0)).isdigit() else seo.get("image_alts", 0)),
        ("Descriptions", f"{int(seo.get('product_descriptions', 0)):,}" if str(seo.get("product_descriptions", 0)).isdigit() else seo.get("product_descriptions", 0)),
        ("Guide pages", seo.get("guide_pages", 0)),
    ]
    return "\n".join(
        f'''
        <article class="mini-stat">
            <strong>{esc(value)}</strong>
            <span>{esc(label)}</span>
        </article>'''
        for label, value in items
    )


def generate():
    now = datetime.now(SAST)
    now_str = now.strftime("%d %b %Y, %H:%M SAST")

    tasks = load_tasks()
    crons = load_cron_jobs()
    normalise_stale_cron_errors(crons)
    seo = load_seo_stats()

    active = [t for t in tasks if t.get("status") == "active"]
    pending = [t for t in tasks if t.get("status") == "pending"]
    blocked = [t for t in tasks if t.get("status") == "blocked"]
    done = [t for t in tasks if t.get("status") == "done"]

    cron_ok = sum(1 for c in crons if c.get("status") in ("ok", "stale"))
    cron_err = sum(1 for c in crons if c.get("status") == "error")
    cron_total = len(crons)

    system_state = "Action needed" if cron_err else "Healthy"
    system_class = "danger" if cron_err else "ok"

    html = Template(
        """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="1800">
<title>Onelife Command Center | $title_date</title>
<style>
:root {
    --bg:#f3f6f4;
    --surface:#ffffff;
    --surface-soft:#f8faf9;
    --ink:#12211b;
    --muted:#66756f;
    --line:#dfe7e2;
    --green:#0f8a52;
    --green-dark:#0b3d2a;
    --blue:#2563eb;
    --red:#dc2626;
    --amber:#b7791f;
    --slate:#64748b;
    --shadow:0 18px 50px rgba(18,33,27,.09);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:linear-gradient(180deg,#eef4f0 0%,#f7f9f8 46%,#eef2f0 100%);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,Arial,sans-serif;line-height:1.45}
a{color:inherit;text-decoration:none}
.page{width:min(1240px,calc(100% - 32px));margin:0 auto;padding:24px 0 34px}
.hero{background:radial-gradient(circle at top left,rgba(41,184,119,.38),transparent 34%),linear-gradient(135deg,#092417 0%,#0e3d2a 54%,#14221c 100%);border:1px solid rgba(255,255,255,.16);border-radius:28px;padding:24px;box-shadow:var(--shadow);color:#fff;position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;inset:auto -80px -120px auto;width:320px;height:320px;border-radius:50%;background:rgba(255,255,255,.08);filter:blur(4px)}
.hero-top{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;position:relative;z-index:1}
.eyebrow{margin:0 0 8px;color:#b8e5cf;font-size:12px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
h1{margin:0;font-size:clamp(32px,5vw,58px);line-height:.95;letter-spacing:-.06em;font-weight:900}
.hero-copy{max-width:620px;margin:14px 0 0;color:#dcefe6;font-size:15px}
.status-block{text-align:right;min-width:190px;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.16);border-radius:18px;padding:14px 16px;backdrop-filter:blur(12px)}
.status-label{font-size:11px;text-transform:uppercase;letter-spacing:.14em;color:#b8e5cf;font-weight:800}
.status-value{margin-top:5px;font-size:22px;font-weight:900}.status-value.ok{color:#86efac}.status-value.danger{color:#fecaca}
.updated{margin-top:5px;color:#dcefe6;font-size:12px}
.link-bar{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px;position:relative;z-index:1}
.link-bar a,.link-bar span{display:inline-flex;align-items:center;gap:6px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.10);color:#eefbf4;border-radius:999px;padding:10px 13px;font-size:13px;font-weight:750;backdrop-filter:blur(10px)}
.link-bar a:hover{background:rgba(255,255,255,.18);transform:translateY(-1px)}
.link-bar .primary-link{background:#fff;color:#0b3d2a;border-color:#fff;box-shadow:0 8px 24px rgba(0,0,0,.14)}
.link-bar .primary-link.muted{background:rgba(183,121,31,.18);border-color:rgba(251,191,36,.36);color:#fde68a;box-shadow:none}
.kpi-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin:18px 0}
.kpi-card{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:16px;box-shadow:0 10px 30px rgba(18,33,27,.055);position:relative;overflow:hidden}
.kpi-card:before{content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--accent,var(--green))}.accent-blue{--accent:var(--blue)}.accent-slate{--accent:var(--slate)}.accent-red{--accent:var(--red)}.accent-green{--accent:var(--green)}
.kpi-label{font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);font-weight:900}.kpi-value{margin-top:8px;font-size:30px;line-height:1;font-weight:950;letter-spacing:-.05em}.kpi-note{margin-top:8px;color:var(--muted);font-size:12px}
.panel{background:rgba(255,255,255,.86);border:1px solid var(--line);border-radius:24px;padding:20px;box-shadow:var(--shadow);margin-top:16px;backdrop-filter:blur(18px)}
.panel-header{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:16px}.panel-header h2{margin:0;font-size:20px;letter-spacing:-.03em}.panel-header p{margin:4px 0 0;color:var(--muted);font-size:13px}.panel-count{color:var(--muted);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.12em}
.agent-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.agent-card{background:var(--surface);border:1px solid var(--line);border-top:4px solid var(--agent);border-radius:18px;padding:15px;min-height:228px;display:flex;flex-direction:column;gap:12px}.agent-topline{display:grid;grid-template-columns:44px 1fr auto;gap:10px;align-items:center}.agent-avatar{width:44px;height:44px;border-radius:14px;background:color-mix(in srgb,var(--agent) 13%,#fff);display:flex;align-items:center;justify-content:center;font-size:23px}.agent-card h3{margin:0;font-size:17px}.agent-card .agent-topline p{margin:2px 0 0;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}.agent-desc{margin:0;color:#4d5d57;font-size:13px;min-height:38px}.agent-status{border-radius:999px;padding:5px 8px;font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.08em}.agent-status.active{background:#dcfce7;color:#166534}.agent-status.idle{background:#f1f5f9;color:#475569}.agent-status.danger{background:#fee2e2;color:#991b1b}.activity-list{list-style:none;padding:0;margin:auto 0 0;display:grid;gap:7px}.activity-list li{display:grid;grid-template-columns:18px 1fr auto;gap:7px;align-items:center;color:#475569;font-size:12px;border-top:1px solid #edf2ef;padding-top:7px}.activity-list time{font-size:11px;color:#8b9893}.activity-dot{width:18px;height:18px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:10px;font-weight:900}.activity-dot.ok,.activity-dot.active{background:#dcfce7;color:#166534}.activity-dot.idle{background:#f1f5f9;color:#64748b}.activity-dot.warn{background:#fef3c7;color:#92400e}.activity-dot.danger{background:#fee2e2;color:#991b1b}.quiet-line{display:block!important;color:#8b9893!important}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:18px;background:var(--surface)}table{width:100%;border-collapse:collapse;min-width:840px}th,td{text-align:left;padding:12px 14px;border-bottom:1px solid #edf2ef;font-size:13px;vertical-align:middle}th{position:sticky;top:0;background:#f8faf9;color:#66756f;font-size:11px;text-transform:uppercase;letter-spacing:.12em;font-weight:900;z-index:1}tr:last-child td{border-bottom:0}.job-name{font-weight:750;color:#23362f}.agent-chip{display:inline-flex;align-items:center;gap:5px;background:color-mix(in srgb,var(--agent) 12%,#fff);color:var(--agent);border-radius:999px;padding:6px 10px;font-size:12px;font-weight:850;white-space:nowrap}.pill{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:5px 9px;font-size:10px;font-weight:950;text-transform:uppercase;letter-spacing:.08em}.pill.ok,.pill.active{background:#dcfce7;color:#166534}.pill.idle{background:#f1f5f9;color:#475569}.pill.warn{background:#fef3c7;color:#92400e}.pill.danger{background:#fee2e2;color:#991b1b}.empty-table{text-align:center;color:var(--muted)}
.task-board{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.task-column{background:#f8faf9;border:1px solid var(--line);border-radius:18px;padding:14px}.task-column h3{margin:0 0 12px;font-size:13px;text-transform:uppercase;letter-spacing:.12em;color:#53615c}.task-column h3 span{float:right;color:#99a5a0}.task-card{background:#fff;border:1px solid #e7eee9;border-left:4px solid var(--accent);border-radius:14px;padding:12px;margin-bottom:10px}.task-meta{display:flex;justify-content:space-between;gap:8px;color:#7a8983;font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.08em}.task-card p{margin:8px 0 10px;color:#273b33;font-size:13px}.empty-state{border:1px dashed #cfdad4;border-radius:14px;padding:18px;color:#8b9893;text-align:center;font-size:13px;background:#fff}
.mini-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.mini-stat{background:#f8faf9;border:1px solid var(--line);border-radius:16px;padding:16px;text-align:center}.mini-stat strong{display:block;font-size:26px;letter-spacing:-.04em}.mini-stat span{display:block;margin-top:4px;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.12em;font-weight:900}.footer{text-align:center;color:#8b9893;font-size:12px;padding:24px 0 4px}
@media(max-width:1100px){.kpi-grid{grid-template-columns:repeat(3,1fr)}.agent-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:760px){.page{width:min(100% - 20px,720px);padding-top:10px}.hero{border-radius:22px;padding:18px}.hero-top{display:block}.status-block{text-align:left;margin-top:16px}.link-bar{display:grid;grid-template-columns:1fr 1fr}.link-bar .primary-link{grid-column:1/-1}.kpi-grid{grid-template-columns:repeat(2,1fr)}.agent-grid,.task-board,.mini-grid{grid-template-columns:1fr}.panel{border-radius:20px;padding:16px}.panel-header{display:block}.agent-card{min-height:0}.activity-list li{grid-template-columns:18px 1fr}.activity-list time{grid-column:2}}
</style>
</head>
<body>
<main class="page">
    <section class="hero">
        <div class="hero-top">
            <div>
                <p class="eyebrow">Onelife Health operations</p>
                <h1>Command Center</h1>
                <p class="hero-copy">A cleaner operator view for tasks, automations, agent ownership, and the core reporting links. Built for fast scanning, not sci-fi cosplay.</p>
            </div>
            <aside class="status-block">
                <div class="status-label">System status</div>
                <div class="status-value $system_class">$system_state</div>
                <div class="updated">Updated $now_str</div>
            </aside>
        </div>
        <nav class="link-bar">$link_bar</nav>
    </section>

    <section class="kpi-grid">$kpi_cards</section>

    <section class="panel">
        <div class="panel-header">
            <div>
                <h2>Agent roster</h2>
                <p>Who owns what, with recent automation activity.</p>
            </div>
            <div class="panel-count">$agent_count agents</div>
        </div>
        <div class="agent-grid">$agent_cards</div>
    </section>

    <section class="panel">
        <div class="panel-header">
            <div>
                <h2>Automation grid</h2>
                <p>Live cron ownership, last run, next run, model, and health.</p>
            </div>
            <div class="panel-count">$cron_total jobs</div>
        </div>
        <div class="table-wrap">
            <table>
                <thead><tr><th>Owner</th><th>Job</th><th>Model</th><th>Last run</th><th>Next</th><th>Status</th></tr></thead>
                <tbody>$cron_rows</tbody>
            </table>
        </div>
    </section>

    <section class="panel">
        <div class="panel-header">
            <div>
                <h2>Task board</h2>
                <p>Active, pending, and recently completed work.</p>
            </div>
            <div class="panel-count">$task_total total</div>
        </div>
        <div class="task-board">$task_columns</div>
    </section>

    <section class="panel">
        <div class="panel-header">
            <div>
                <h2>SEO & content metrics</h2>
                <p>Current output counters used by the content engine.</p>
            </div>
        </div>
        <div class="mini-grid">$seo_items</div>
    </section>

    <footer class="footer">Jarvis 🦞 × OpenClaw × Onelife Health · $footer_date</footer>
</main>
</body>
</html>"""
    ).safe_substitute(
        title_date=now.strftime("%d %b"),
        system_class=system_class,
        system_state=system_state,
        now_str=now_str,
        link_bar=render_link_bar(load_paperclip_public_url()),
        kpi_cards=render_kpi_cards(active, pending, blocked, done, cron_ok, cron_total, cron_err),
        agent_count=len(AGENTS),
        agent_cards=render_agent_cards(crons),
        cron_total=cron_total,
        cron_rows=render_cron_rows(crons),
        task_total=len(tasks),
        task_columns="\n".join(
            [
                render_task_column("Active", active, "No active tasks"),
                render_task_column("Pending", pending, "No pending tasks"),
                render_task_column("Done", done[:6], "No completed tasks"),
            ]
        ),
        seo_items=render_seo_items(seo),
        footer_date=now.strftime("%d %B %Y"),
    )

    out = os.path.join(SCRIPT_DIR, "index.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"Command Center generated: {len(html):,} bytes → {out}")
    return out


if __name__ == "__main__":
    generate()
