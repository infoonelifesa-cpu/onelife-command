---
title: Command Center Dashboard
tags: []
keywords: []
importance: 50
recency: 1
maturity: draft
createdAt: '2026-03-29T17:57:08.316Z'
updatedAt: '2026-03-29T17:57:08.316Z'
---
## Raw Concept
**Task:**
Maintain Command Center Dashboard

**Files:**
- index.html
- generate_dashboard.py

**Flow:**
data gathered -> generate_dashboard.py -> index.html

**Timestamp:** 2026-03-29

## Narrative
### Structure
Dashboard built with grid-drift animation and KPI strip. Tracks active tasks and agent roles.

### Dependencies
Uses openclaw cron list for system status.

### Highlights
Real-time dashboard generation from cron status and agent task tracking.

## Facts
- **dashboard_generation**: Dashboard is generated via generate_dashboard.py [project]
- **dashboard_file**: The command center dashboard is stored in index.html [project]
- **workspace_path**: Workspace is located at ~/.openclaw/workspace [project]
- **jarvis_role**: Jarvis is the CEO / Orchestrator [team]
- **ghost_role**: Ghost is DevOps / Building [team]
- **scout_role**: Scout is Intelligence / Research [team]
- **cipher_role**: Cipher is CTO / Engineering [team]
- **nova_role**: Nova is CMO / Marketing [team]
- **vivid_role**: Vivid is Brand PM [team]
- **sage_role**: Sage is Deep Analysis [team]
- **kimi_role**: Kimi is Compaction / Fallback [team]
