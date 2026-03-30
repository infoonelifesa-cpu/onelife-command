---
children_hash: ac93f69caedd678dd935d50a8dac3f8fb47acff9dee1f0f4bce4d755cfb8f8c6
compression_ratio: 0.7804054054054054
condensation_order: 2
covers: [command_center/_index.md]
covers_token_total: 296
summary_level: d2
token_count: 231
type: summary
---
# Command Center Structural Summary

The Command Center functions as the primary operational hub for project orchestration, centralizing system status, task tracking, and agent role management within the `~/.openclaw/workspace`.

## Dashboard Architecture
The infrastructure relies on `generate_dashboard.py` to aggregate cron status data and render the `index.html` dashboard. Key interface features include a KPI monitoring strip and grid-drift visual animations. Refer to `command_center_dashboard.md` for technical implementation details.

## Agent Orchestration Roster
Operational governance is distributed across specialized roles:
*   **Executive/Orchestration**: Jarvis (CEO)
*   **Engineering/DevOps**: Cipher (CTO), Ghost (DevOps)
*   **Research/Intelligence**: Scout (Intelligence), Sage (Deep Analysis)
*   **Brand/Marketing**: Nova (CMO), Vivid (Brand PM)
*   **System Maintenance**: Kimi (Compaction/Fallback)