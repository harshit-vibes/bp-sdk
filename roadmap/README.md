# Task Manager

> CSV-based task management synced with Linear

## Overview

This project manages Lyzr's Blueprint initiative tasks using CSV files as the source of truth, synchronized with Linear for team visibility and collaboration.

## Directory Structure

```
task-manager/
├── README.md           # This file
├── .env                # Linear API credentials
├── projects.csv        # Project definitions
├── tasks.csv           # Task definitions
└── sync_linear.py      # Sync script
```

## CSV Schema

### projects.csv

| Column | Description |
|--------|-------------|
| id | Unique project identifier (e.g., BP-LIB) |
| name | Project display name |
| initiative | Parent initiative name |
| team | Linear team name |
| description | Project description |
| state | Project state (planned/started/completed/canceled) |
| linear_id | Linear project ID (populated after sync) |

### tasks.csv

| Column | Description |
|--------|-------------|
| id | Unique task identifier (e.g., BP-038, PLAT-001) |
| title | Task title |
| project_id | Parent project ID (references projects.csv) |
| description | Task description |
| priority | Priority level (urgent/high/medium/low) |
| state | Task state (backlog/todo/in_progress/done/canceled) |
| labels | Comma-separated labels |
| linear_id | Linear issue ID (populated after sync) |

## Projects

### BP Initiative

| Project | Description |
|---------|-------------|
| **BP Library** | Blueprint instances - 12 planned blueprints to develop |
| **BP Ops** | Marketing, distribution, non-dev activities |
| **BP Platform** | Developer tasks for blueprint UI/UX (23 tasks) |
| **Lyzr SDK** | SDK functionality and integrations |

## Usage

### Sync to Linear

```bash
# Full sync (creates/updates all projects and tasks)
python sync_linear.py sync

# Sync only projects
python sync_linear.py sync --projects-only

# Sync only tasks
python sync_linear.py sync --tasks-only

# Dry run (preview changes without applying)
python sync_linear.py sync --dry-run
```

### Pull from Linear

```bash
# Update CSVs with Linear IDs and status
python sync_linear.py pull
```

### Update Initiative Description

Linear limits initiative descriptions to 255 characters. For full content, manually copy from `/Users/harshitchoudhary/Documents/lyzr/kb/README.md` to Linear UI.

### Status Check

```bash
# Show sync status
python sync_linear.py status
```

## Workflow

1. **Edit CSVs** - Add/modify projects and tasks in CSV files
2. **Sync to Linear** - Run `python sync_linear.py sync`
3. **Work in Linear** - Team updates task status in Linear
4. **Pull updates** - Run `python sync_linear.py pull` to update CSVs

## Environment Setup

```bash
# Copy .env.example to .env and add your Linear API key
cp .env.example .env

# Install dependencies
pip install python-dotenv requests
```

## Linear Structure

```
Lyzr Studio (Team)
└── Blueprints (Initiative)
    ├── BP Library (Project) - 12 tasks
    │   └── Tasks: BP-038 to BP-049 (planned blueprints)
    ├── BP Ops (Project) - 0 tasks
    │   └── Tasks: TBD (marketing, distribution)
    ├── BP Platform (Project) - 23 tasks
    │   └── Tasks: PLAT-001 to PLAT-023 (UI/UX components)
    └── Lyzr SDK (Project) - 38 tasks
        └── Tasks: SDK-001 to SDK-038 (5 phases)
```

## Task Statistics

| Project | Tasks | High Priority | Medium Priority | Low Priority |
|---------|-------|---------------|-----------------|--------------|
| BP Library | 12 | 7 | 4 | 1 |
| BP Ops | 0 | - | - | - |
| BP Platform | 23 | 0 | 23 | 0 |
| Lyzr SDK | 38 | 10 | 27 | 1 |
| **Total** | **73** | **17** | **54** | **2** |

## Lyzr SDK Phases

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1: Foundation | SDK-001 to SDK-009 | CLI setup, auth, storage, platform client |
| Phase 2: Chat | SDK-010 to SDK-013 | Interactive chat, SSE streaming, WebSocket |
| Phase 3: Sub-agents | SDK-014 to SDK-018 | Multi-agent hierarchies, dependency mgmt |
| Phase 4: Tools | SDK-019 to SDK-024 | Tool sources (composio, mcp, openapi, aci) |
| Phase 5: Features | SDK-025 to SDK-034 | Memory, RAG, Voice, RAI, etc. |
| Supporting | SDK-035 to SDK-038 | Collection, docs, tests, release |
