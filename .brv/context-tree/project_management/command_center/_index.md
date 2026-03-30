---
children_hash: 58362f857e46124b2c6d6f45589474281b06e7cbc212e0eae2f038c1ceb24cbe
compression_ratio: 0.7009063444108762
condensation_order: 1
covers: [command_center_dashboard.md]
covers_token_total: 331
summary_level: d1
token_count: 232
type: summary
---
# Command Center Overview

The Command Center serves as the central operational hub for the project, providing real-time visibility into system status, task tracking, and agent roles.

## Dashboard Architecture
- **Components**: The system utilizes `generate_dashboard.py` to process cron status data and generate the `index.html` dashboard file.
- **UI/UX**: Features a grid-drift animation and a KPI strip for monitoring active tasks.
- **Workspace**: Operations are anchored at `~/.openclaw/workspace`.

## Agent Roster and Roles
The following roles are defined for organizational orchestration:
- **CEO / Orchestrator**: Jarvis
- **CTO / Engineering**: Cipher
- **DevOps / Building**: Ghost
- **Intelligence / Research**: Scout
- **CMO / Marketing**: Nova
- **Brand PM**: Vivid
- **Deep Analysis**: Sage
- **Compaction / Fallback**: Kimi

For detailed implementation specifications, refer to `command_center_dashboard.md`.