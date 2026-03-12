---
description: Sync blueprint roadmap tasks with Linear
argument-hint: [push|pull|status] [options]
allowed-tools: Bash(bp:*), Bash(cat:*), Read
---

## Task

Manage blueprint roadmap tasks in Linear.

Arguments: $ARGUMENTS

### Commands

**Push tasks to Linear:**
```bash
bp linear push                    # Sync all
bp linear push --dry-run          # Preview changes
bp linear push --projects         # Only projects
bp linear push --tasks -l 10      # Limit tasks
```

**Pull project IDs:**
```bash
bp linear pull
```

**Show sync status:**
```bash
bp linear status
```

**Delete issues:**
```bash
bp linear delete-issues BP-LIB --dry-run
bp linear delete-issues BP-LIB --force
```

### Prerequisites

Environment variables in `.env`:
```bash
LINEAR_API_KEY=lin_api_xxx
LINEAR_TEAM_ID=xxx
```

### Execution

Based on the argument, run the appropriate command:

1. **push** → `bp linear push $ARGUMENTS`
2. **pull** → `bp linear pull`
3. **status** → `bp linear status`

### Post-Execution Analysis

After running the command:
1. Report the number of items synced/updated
2. Highlight any errors or failures
3. Show next steps if needed (e.g., "Run `bp linear push` to sync")

### Task File Reference

Tasks are stored in `roadmap/tasks.csv`:

| Field | Description |
|-------|-------------|
| id | Task identifier (e.g., LIB-001) |
| title | Task title |
| project_id | Parent project (e.g., BP-LIB) |
| description | Task description |
| priority | urgent, high, medium, low |
| state | todo, in-progress, done |
| labels | Comma-separated labels |
| linear_id | Linear issue ID (auto-filled) |
| week | Sprint week (week-1 to week-7) |

### Adding New Tasks

To add a new task:
1. Add a row to `roadmap/tasks.csv`
2. Set the `week` field for sprint planning
3. Run `bp linear push` to sync
