---
children_hash: 02befa47e408cc4722e66f5167f6a2bea5a855739464a3cb393da8d122614759
compression_ratio: 0.8281786941580757
condensation_order: 1
covers: [agent_roster.md]
covers_token_total: 291
summary_level: d1
token_count: 241
type: summary
---
# Agent Roster and Project Infrastructure Summary

This document provides a structural overview of the current agent roster and project configuration. For detailed role descriptions and specific agent capabilities, see [agent_roster.md].

## Agent Roster
The team is composed of eight specialized agents, each defined by a specific role and responsibility:
* **Jarvis**: CEO / Orchestrator
* **Cipher**: CTO / Engineering
* **Ghost**: DevOps / Building
* **Scout**: Intelligence / Research
* **Nova**: CMO / Marketing
* **Vivid**: Brand PM
* **Sage**: Deep Analysis
* **Kimi**: Compaction / Fallback

## Project Infrastructure and Workspace
The project operates within the local environment at `~/.openclaw/workspace`. The system utilizes two primary scripts and a central file for dashboard management:
* **Dashboard Logic**: Handled via `generate_dashboard.py` and `generate.py`.
* **Dashboard Output**: The command center dashboard is maintained in `index.html`.