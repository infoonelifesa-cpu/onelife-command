#!/usr/bin/env python3
"""Generate Onelife Command Center dashboard — mission control for agents, crons, and backlog.
No store data here (that's Intelligence). Designed to run via cron."""

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta

SAST = timezone(timedelta(hours=2))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")


def load_tasks():
    try:
        with open(os.path.join(WORKSPACE, "memory/active-tasks.json")) as f:
            return json.load(f).get("tasks", [])
    except:
        return []


def load_cron_jobs():
    """Get full cron list with details."""
    try:
        result = subprocess.run(["openclaw", "cron", "list"], capture_output=True, text=True, timeout=15)
        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:
            return []
        # Parse the columnar output
        jobs = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 5:
                job_id = parts[0]
                # Find the status field — usually "ok", "error", or "stale"
                status = "unknown"
                for p in parts:
                    if p in ("ok", "error", "stale", "pending"):
                        status = p
                        break
                # Name is between ID and the cron expression
                name_parts = []
                for p in parts[1:]:
                    if p.startswith("cron") or p.startswith("0") or p.startswith("*"):
                        break
                    name_parts.append(p)
                name = " ".join(name_parts) if name_parts else job_id[:12]
                
                # Next run info
                next_run = ""
                for i, p in enumerate(parts):
                    if p.startswith("in"):
                        next_run = " ".join(parts[i:i+2]) if i+1 < len(parts) else p
                        break
                
                # Last run info
                last_run = ""
                for i, p in enumerate(parts):
                    if p.endswith("ago"):
                        last_run = " ".join(parts[max(0,i-1):i+1])
                        break
                
                # Model
                model = ""
                for p in parts:
                    if "/" in p and ("kimi" in p or "claude" in p or "gpt" in p or "moonshot" in p):
                        model = p.split("/")[-1]
                        break
                
                jobs.append({
                    "id": job_id, "name": name, "status": status,
                    "next": next_run, "last": last_run, "model": model
                })
        return jobs
    except:
        return []


def load_seo_stats():
    try:
        with open(os.path.join(WORKSPACE, "command-center/status.json")) as f:
            return json.load(f).get("seo", {})
    except:
        return {"blog_posts": 17, "image_alts": 8397, "product_descriptions": 2108, "guide_pages": 12}


def load_memory_files():
    """Check recent memory files."""
    mem_dir = os.path.join(WORKSPACE, "memory")
    try:
        files = sorted([f for f in os.listdir(mem_dir) if f.startswith("2026-") and f.endswith(".md")], reverse=True)
        return files[:7]  # last week
    except:
        return []


def generate():
    now = datetime.now(SAST)
    now_str = now.strftime("%d %b %Y, %H:%M SAST")
    
    tasks = load_tasks()
    crons = load_cron_jobs()
    seo = load_seo_stats()
    memory_files = load_memory_files()
    
    active = [t for t in tasks if t.get("status") == "active"]
    pending = [t for t in tasks if t.get("status") == "pending"]
    blocked = [t for t in tasks if t.get("status") == "blocked"]
    done = [t for t in tasks if t.get("status") == "done"]
    
    cron_ok = sum(1 for c in crons if c["status"] == "ok")
    cron_err = sum(1 for c in crons if c["status"] == "error")
    cron_total = len(crons)
    
    # Priority colors
    def pri_col(p):
        return {"HIGH": "#ef4444", "MEDIUM": "#eab308", "LOW": "#22c55e"}.get(p, "#6b7280")
    def stat_col(s):
        return {"active": "#3b82f6", "pending": "#737373", "blocked": "#ef4444", "done": "#22c55e"}.get(s, "#737373")
    def cron_col(s):
        return {"ok": "#22c55e", "error": "#ef4444", "stale": "#eab308"}.get(s, "#737373")
    
    # Task rows
    task_rows = ""
    for t in sorted(active + pending + blocked, key=lambda x: {"HIGH":0,"MEDIUM":1,"LOW":2}.get(x.get("priority","MEDIUM"),1)):
        p = t.get("priority", "MEDIUM")
        s = t.get("status", "pending")
        desc = t.get("description", "")[:70]
        owner = t.get("agent", "Jarvis")
        task_rows += f"""<tr>
            <td><span class="badge" style="background:{pri_col(p)}">{p}</span></td>
            <td class="task-desc">{desc}</td>
            <td style="font-size:12px;color:#94a3b8">{owner}</td>
            <td><span class="badge" style="background:{stat_col(s)}">{s}</span></td>
        </tr>"""
    
    # Cron rows
    cron_rows = ""
    for c in crons:
        s = c["status"]
        cron_rows += f"""<tr>
            <td><span class="dot" style="background:{cron_col(s)}"></span></td>
            <td style="font-size:13px;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{c["name"]}</td>
            <td style="font-size:12px;color:#94a3b8">{c["model"]}</td>
            <td style="font-size:12px;color:#94a3b8">{c["last"]}</td>
            <td style="font-size:12px;color:#64748b">{c["next"]}</td>
            <td><span class="badge" style="background:{cron_col(s)}">{s}</span></td>
        </tr>"""
    
    # Memory timeline
    mem_html = ""
    for f in memory_files:
        day = f.replace(".md", "")
        mem_html += f'<span class="mem-chip">{day}</span>'
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="1800">
<title>Command Center | {now.strftime('%d %b')}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0a0a14;color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:20px;max-width:1000px;margin:0 auto}}
.header{{text-align:center;padding:24px 0 16px;border-bottom:1px solid #2d2d3d;margin-bottom:20px}}
.header h1{{font-size:28px;font-weight:800;color:#00ff88;letter-spacing:-0.5px}}
.header .sub{{font-size:13px;color:#64748b;margin-top:4px}}
.header .ts{{font-size:11px;color:#404040;margin-top:8px;font-family:monospace}}
.kpi-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:20px}}
.kpi{{background:#1a1a2e;border:1px solid #2d2d3d;border-radius:10px;padding:16px;text-align:center}}
.kpi-val{{font-size:28px;font-weight:800}}
.kpi-lbl{{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-top:4px}}
.section{{background:#1a1a2e;border:1px solid #2d2d3d;border-radius:12px;padding:20px;margin-bottom:16px}}
.section-title{{font-size:16px;font-weight:700;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid #2d2d3d}}
table{{width:100%;border-collapse:collapse}}
th{{font-size:11px;color:#64748b;text-align:left;padding:8px;letter-spacing:1px;text-transform:uppercase}}
td{{padding:10px 8px;border-bottom:1px solid #1e1e2e;font-size:13px}}
.badge{{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;color:#fff}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}}
.task-desc{{max-width:350px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.seo-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.seo-item{{background:#0f0f1a;border-radius:8px;padding:14px;text-align:center}}
.seo-num{{font-size:22px;font-weight:700;color:#818cf8}}
.seo-lbl{{font-size:11px;color:#64748b;margin-top:4px}}
.mem-chip{{display:inline-block;background:#0f0f1a;border:1px solid #2d2d3d;border-radius:6px;padding:4px 10px;margin:4px;font-size:12px;color:#94a3b8;font-family:monospace}}
.link-bar{{display:flex;gap:12px;justify-content:center;margin:16px 0;flex-wrap:wrap}}
.link-bar a{{color:#818cf8;text-decoration:none;font-size:12px;padding:6px 14px;background:#0f0f1a;border:1px solid #2d2d3d;border-radius:8px}}
.link-bar a:hover{{background:#1a1a2e}}
.footer{{text-align:center;padding:20px;font-size:12px;color:#404040}}
@media(max-width:768px){{
  .kpi-grid{{grid-template-columns:repeat(2,1fr)}}
  .seo-grid{{grid-template-columns:repeat(2,1fr)}}
}}
</style>
</head>
<body>

<div class="header">
    <h1>🦞 Command Center</h1>
    <div class="sub">Agent Operations · Cron Monitor · Task Backlog</div>
    <div class="ts">Updated: {now_str}</div>
</div>

<div class="link-bar">
    <a href="https://infoonelifesa-cpu.github.io/onelife-intelligence/">📊 Intelligence Dashboard</a>
    <a href="https://onelife.co.za">🛍️ Shopify</a>
    <a href="https://www.klaviyo.com/dashboard">📧 Klaviyo</a>
</div>

<div class="kpi-grid">
    <div class="kpi"><div class="kpi-val" style="color:#3b82f6">{len(active)}</div><div class="kpi-lbl">Active Tasks</div></div>
    <div class="kpi"><div class="kpi-val" style="color:#737373">{len(pending)}</div><div class="kpi-lbl">Pending</div></div>
    <div class="kpi"><div class="kpi-val" style="color:#ef4444">{len(blocked)}</div><div class="kpi-lbl">Blocked</div></div>
    <div class="kpi"><div class="kpi-val" style="color:#22c55e">{len(done)}</div><div class="kpi-lbl">Done</div></div>
    <div class="kpi"><div class="kpi-val" style="color:{'#22c55e' if cron_err == 0 else '#ef4444'}">{cron_ok}/{cron_total}</div><div class="kpi-lbl">Crons OK</div></div>
</div>

<!-- Task Backlog -->
<div class="section">
    <div class="section-title">📋 Task Backlog ({len(active) + len(pending) + len(blocked)} open)</div>
    <table>
        <thead><tr><th>Priority</th><th>Task</th><th>Agent</th><th>Status</th></tr></thead>
        <tbody>{task_rows if task_rows else '<tr><td colspan="4" style="text-align:center;color:#64748b">No open tasks</td></tr>'}</tbody>
    </table>
</div>

<!-- Cron Monitor -->
<div class="section">
    <div class="section-title">⏰ Cron Jobs ({cron_total} total · <span style="color:#22c55e">{cron_ok} ok</span>{f' · <span style="color:#ef4444">{cron_err} errors</span>' if cron_err else ''})</div>
    <table>
        <thead><tr><th></th><th>Job</th><th>Model</th><th>Last Run</th><th>Next Run</th><th>Status</th></tr></thead>
        <tbody>{cron_rows if cron_rows else '<tr><td colspan="6" style="text-align:center;color:#64748b">No cron jobs found</td></tr>'}</tbody>
    </table>
</div>

<!-- SEO Progress -->
<div class="section">
    <div class="section-title">🔍 SEO & Content Progress</div>
    <div class="seo-grid">
        <div class="seo-item"><div class="seo-num">{seo.get('blog_posts', 0)}</div><div class="seo-lbl">Blog Posts</div></div>
        <div class="seo-item"><div class="seo-num">{seo.get('image_alts', 0):,}</div><div class="seo-lbl">Image Alts</div></div>
        <div class="seo-item"><div class="seo-num">{seo.get('product_descriptions', 0):,}</div><div class="seo-lbl">Descriptions</div></div>
        <div class="seo-item"><div class="seo-num">{seo.get('guide_pages', 0)}</div><div class="seo-lbl">Guide Pages</div></div>
    </div>
</div>

<!-- Memory Timeline -->
<div class="section">
    <div class="section-title">🧠 Memory Log (recent)</div>
    <div>{mem_html if mem_html else '<span style="color:#64748b">No memory files found</span>'}</div>
</div>

<div class="footer">Command Center × Jarvis 🦞 × OpenClaw · {now.strftime('%d %B %Y')}</div>

</body>
</html>"""
    
    out = os.path.join(SCRIPT_DIR, "index.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"Command Center generated: {len(html):,} bytes → {out}")
    return out


if __name__ == "__main__":
    generate()
