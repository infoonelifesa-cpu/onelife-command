#!/usr/bin/env python3
"""Generate Onelife Command Center dashboard from Omni API + local state.
No Paperclip dependency. Designed to run via cron."""

import json
import urllib.request
import urllib.parse
import os
import subprocess
from datetime import datetime, timezone, timedelta

SAST = timezone(timedelta(hours=2))
OMNI_BASE = "http://102.22.82.27:59029"
OMNI_AUTH = "UserName=analytic&Password=An%40lyt1c&CompanyName=Onelife"
BRANCHES = {"HO": "Centurion", "EDN": "Edenvale", "GVS": "Glen Village"}
TARGETS = {"HO": 1450000, "EDN": 450000, "GVS": 330000}
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")

REPORTS = {"HO": "Daily Turnover One Life", "GVS": "Daily Turnover GVS", "EDN": "Daily Turnover EDEN"}
# Trading days per month: CEN closed Sundays (26), GVS+EDN open 7 days (31)
TRADING_DAYS = {"HO": 26, "GVS": 31, "EDN": 31}

def omni_get(path, timeout=60):
    """GET from Omni API with auth."""
    sep = "&" if "?" in path else "?"
    url = f"{OMNI_BASE}{path}{sep}{OMNI_AUTH}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        r = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def get_mtd_sales():
    """Pull MTD sales from Omni Daily Turnover reports. All figures excl VAT."""
    now = datetime.now(SAST)
    month_prefix = now.strftime("%Y-%m")
    results = {}
    for branch, name in BRANCHES.items():
        report = REPORTS.get(branch, "")
        data = omni_get(f"/Report/{urllib.parse.quote(report)}", timeout=120)
        
        if isinstance(data, dict) and not data.get("error"):
            # Response is nested: {"daily_turnover_xxx": [...]}
            key = next(iter(data), None)
            records = data[key] if key and isinstance(data[key], list) else []
        elif isinstance(data, list):
            records = data
        else:
            results[branch] = {"name": name, "mtd": 0, "days": 0, "target": TARGETS.get(branch, 0), 
                             "trading_days": TRADING_DAYS.get(branch, 30), "error": data.get("error", "Unknown")}
            continue
        
        march = [r for r in records if r.get("document_date", "").startswith(month_prefix)]
        total = sum(float(r.get("value_excl_after_discount", 0)) for r in march)
        gp = sum(float(r.get("gross_profit", 0)) for r in march)
        days = len(set(r.get("document_date", "")[:10] for r in march))
        
        results[branch] = {
            "name": name, "mtd": round(total), "gp": round(gp), 
            "days": max(days, 1), "target": TARGETS.get(branch, 0),
            "trading_days": TRADING_DAYS.get(branch, 30)
        }
    return results

def load_tasks():
    """Load active tasks from workspace."""
    try:
        with open(os.path.join(WORKSPACE, "memory/active-tasks.json")) as f:
            return json.load(f).get("tasks", [])
    except:
        return []

def load_cron_summary():
    """Get cron status counts."""
    try:
        result = subprocess.run(["openclaw", "cron", "list"], capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().split("\n")[1:]  # skip header
        total = len(lines)
        errors = sum(1 for l in lines if "error" in l.lower())
        ok = sum(1 for l in lines if "ok" in l.lower())
        return {"total": total, "ok": ok, "errors": errors}
    except:
        return {"total": 0, "ok": 0, "errors": 0}

def load_seo_stats():
    """Load SEO stats from status.json or MEMORY."""
    try:
        with open(os.path.join(WORKSPACE, "command-center/status.json")) as f:
            return json.load(f).get("seo", {})
    except:
        return {"blog_posts": 17, "image_alts": 8397, "product_descriptions": 2108, "guide_pages": 12}

def fmt_money(val):
    """Format as R1,234k"""
    if val >= 1000000:
        return f"R{val/1000000:.1f}M"
    elif val >= 1000:
        return f"R{val/1000:.0f}k"
    return f"R{val:.0f}"

def generate():
    now = datetime.now(SAST)
    now_str = now.strftime("%d %b %Y, %H:%M SAST")
    
    # Pull data
    sales = get_mtd_sales()
    tasks = load_tasks()
    crons = load_cron_summary()
    seo = load_seo_stats()
    
    total_mtd = sum(s.get("mtd", 0) for s in sales.values())
    total_target = sum(s.get("target", 0) for s in sales.values())
    omni_ok = not any(s.get("error") for s in sales.values())
    
    # Count tasks by status
    active_tasks = [t for t in tasks if t.get("status") == "active"]
    pending_tasks = [t for t in tasks if t.get("status") == "pending"]
    done_tasks = [t for t in tasks if t.get("status") == "done"]
    
    # Store cards with GP and projection
    store_cards = ""
    for branch in ["HO", "EDN", "GVS"]:
        s = sales.get(branch, {})
        mtd = s.get("mtd", 0)
        gp = s.get("gp", 0)
        target = s.get("target", 0)
        days = s.get("days", 1)
        trading_days = s.get("trading_days", 30)
        pct = round(mtd / target * 100) if target else 0
        daily_avg = mtd / days if days else 0
        remaining_days = max(trading_days - days, 0)
        projected = mtd + (daily_avg * remaining_days)
        gp_pct = round(gp / mtd * 100, 1) if mtd else 0
        on_track = projected >= target
        pace_color = "#22c55e" if on_track else "#ef4444"
        pace_label = "On track" if on_track else f"Need {fmt_money((target - mtd) / max(remaining_days, 1))}/day"
        err = s.get("error", "")
        status_dot = "🔴" if err else "🟢"
        store_cards += f'''
        <div class="store-card">
            <div class="store-name">{status_dot} {s.get("name", branch)}</div>
            <div class="store-mtd">{fmt_money(mtd)}</div>
            <div class="store-target">of {fmt_money(target)} target · {days} days</div>
            <div class="store-bar"><div class="store-fill" style="width:{min(pct,100)}%;background:{pace_color}"></div></div>
            <div class="store-pct" style="color:{pace_color}">{pct}% · {pace_label}</div>
            <div style="font-size:0.65em;color:#737373;margin-top:4px">GP: {fmt_money(gp)} ({gp_pct}%) · Proj: {fmt_money(round(projected))}</div>
        </div>'''
    
    # Task rows
    task_html = ""
    for t in active_tasks + pending_tasks:
        status = t.get("status", "pending")
        priority = t.get("priority", "MEDIUM")
        pri_color = {"HIGH": "#ef4444", "MEDIUM": "#eab308", "LOW": "#22c55e"}.get(priority, "#6b7280")
        stat_color = {"active": "#3b82f6", "pending": "#737373", "blocked": "#ef4444"}.get(status, "#737373")
        task_html += f'''
        <tr>
            <td><span class="badge" style="background:{pri_color}">{priority}</span></td>
            <td class="task-desc">{t.get("description","")[:80]}</td>
            <td><span class="badge" style="background:{stat_color}">{status}</span></td>
        </tr>'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Onelife Command Center</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0a0a;color:#e5e5e5;font-family:-apple-system,BlinkMacSystemFont,sans-serif;padding:12px;max-width:900px;margin:0 auto}}
.hdr{{text-align:center;padding:20px 0 12px;border-bottom:1px solid #262626;margin-bottom:16px}}
.hdr h1{{color:#00ff88;font-size:1.5em}}
.hdr .sub{{color:#737373;font-size:0.75em;margin-top:4px}}
.hdr .ts{{color:#525252;font-size:0.65em;margin-top:6px;font-family:monospace}}
.omni-status{{text-align:center;font-size:0.7em;margin:8px 0;padding:4px 12px;border-radius:6px;display:inline-block}}
.kpi{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0}}
.k{{background:#171717;border:1px solid #262626;border-radius:10px;padding:14px 8px;text-align:center}}
.kv{{font-size:1.5em;font-weight:700;color:#00ff88}}
.kl{{font-size:0.6em;color:#737373;text-transform:uppercase;letter-spacing:1px;margin-top:4px}}
.sec{{background:#171717;border:1px solid #262626;border-radius:10px;padding:14px;margin:12px 0}}
.sh{{font-weight:600;font-size:0.95em;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #262626}}
.stores{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.store-card{{background:#0d1117;border-radius:8px;padding:12px;text-align:center}}
.store-name{{font-weight:600;font-size:0.85em;margin-bottom:6px}}
.store-mtd{{font-size:1.4em;font-weight:700;color:#e5e5e5}}
.store-target{{font-size:0.65em;color:#737373;margin:2px 0 8px}}
.store-bar{{background:#262626;border-radius:4px;height:6px;overflow:hidden}}
.store-fill{{height:100%;border-radius:4px;transition:width 0.5s}}
.store-pct{{font-size:0.8em;font-weight:700;margin-top:4px}}
.seo-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}}
.seo-item{{background:#0d1117;border-radius:8px;padding:10px;text-align:center}}
.seo-num{{font-size:1.2em;font-weight:700;color:#6366f1}}
.seo-label{{font-size:0.6em;color:#737373;margin-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:0.8em}}
th{{text-align:left;font-size:0.65em;color:#737373;text-transform:uppercase;padding:8px 6px;border-bottom:1px solid #262626}}
td{{padding:8px 6px;border-bottom:1px solid #1a1a1a}}
.task-desc{{max-width:400px}}
.badge{{display:inline-block;padding:2px 8px;border-radius:6px;font-size:0.65em;font-weight:600;color:#fff}}
.cron-row{{display:flex;justify-content:space-between;align-items:center;padding:4px 0}}
.cron-label{{font-size:0.8em;color:#aaa}}
.cron-val{{font-size:0.8em;font-weight:600}}
.ft{{text-align:center;color:#404040;font-size:0.6em;padding:16px 0}}
@media(max-width:600px){{
  .kpi{{grid-template-columns:repeat(2,1fr)}}
  .stores{{grid-template-columns:1fr}}
  .seo-grid{{grid-template-columns:repeat(2,1fr)}}
  table{{font-size:0.7em}}
  td,th{{padding:6px 4px}}
  .task-desc{{max-width:200px}}
}}
</style>
</head>
<body>
<div class="hdr">
  <h1>🦞 Onelife Command Center</h1>
  <div class="sub">Omni · Shopify · Klaviyo · GA4</div>
  <div class="ts">Updated: {now_str}</div>
  <div class="omni-status" style="background:{'#0f3d0f' if omni_ok else '#3d0f0f'}; color:{'#22c55e' if omni_ok else '#ef4444'}">
    Omni: {'● Connected' if omni_ok else '● Unreachable'}
  </div>
</div>

<div class="kpi">
  <div class="k"><div class="kv">{fmt_money(total_mtd)}</div><div class="kl">MTD Revenue</div></div>
  <div class="k"><div class="kv">{fmt_money(total_target)}</div><div class="kl">Monthly Target</div></div>
  <div class="k"><div class="kv">{len(active_tasks)}</div><div class="kl">Active Tasks</div></div>
  <div class="k"><div class="kv" style="color:{'#22c55e' if crons.get('errors',0)==0 else '#ef4444'}">{crons.get('ok',0)}/{crons.get('total',0)}</div><div class="kl">Crons OK</div></div>
</div>

<div class="sec">
  <div class="sh">📊 Store Performance (MTD excl VAT)</div>
  <div class="stores">{store_cards}</div>
</div>

<div class="sec">
  <div class="sh">🔍 SEO Progress</div>
  <div class="seo-grid">
    <div class="seo-item"><div class="seo-num">{seo.get('blog_posts',0)}</div><div class="seo-label">Blog Posts</div></div>
    <div class="seo-item"><div class="seo-num">{fmt_money(seo.get('image_alts',0)).replace('R','')}</div><div class="seo-label">Image Alts</div></div>
    <div class="seo-item"><div class="seo-num">{fmt_money(seo.get('product_descriptions',0)).replace('R','')}</div><div class="seo-label">Descriptions</div></div>
    <div class="seo-item"><div class="seo-num">{seo.get('guide_pages',0)}</div><div class="seo-label">Guide Pages</div></div>
  </div>
</div>

<div class="sec">
  <div class="sh">📋 Active Tasks ({len(active_tasks) + len(pending_tasks)})</div>
  <table>
    <thead><tr><th>Priority</th><th>Task</th><th>Status</th></tr></thead>
    <tbody>{task_html}</tbody>
  </table>
</div>

<div class="sec">
  <div class="sh">⏰ Automation</div>
  <div class="cron-row"><span class="cron-label">Cron Jobs</span><span class="cron-val">{crons.get('total',0)} total</span></div>
  <div class="cron-row"><span class="cron-label">Healthy</span><span class="cron-val" style="color:#22c55e">{crons.get('ok',0)}</span></div>
  <div class="cron-row"><span class="cron-label">Errors</span><span class="cron-val" style="color:{'#ef4444' if crons.get('errors',0) else '#22c55e'}">{crons.get('errors',0)}</span></div>
</div>

<div class="ft">Onelife Intelligence × OpenClaw × Jarvis 🦞 · {now_str}</div>
</body>
</html>'''
    
    out_path = os.path.join(SCRIPT_DIR, "index.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Dashboard generated: {len(html)} bytes → {out_path}")
    return out_path

if __name__ == "__main__":
    generate()
