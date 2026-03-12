---
description: Sync blueprints from Lyzr Studio to local directory
argument-hint: [--dir path] [--visibility type] [--clean] [--dry-run]
allowed-tools: Bash(bp:*), Bash(ls:*)
---

## Task

Sync blueprints from Lyzr Studio API to local directory.

Arguments: $ARGUMENTS

### Default Behavior

```bash
bp sync
```

Syncs all accessible blueprints to `./blueprints/studio/` organized by visibility:
- `private/` - Your private blueprints
- `org-wide/` - Organization shared blueprints
- `public-owned/` - Public blueprints you own
- `public-unowned/` - Public blueprints from others

### Options

**Custom directory:**
```bash
bp sync -d ./my-blueprints
```

**Filter by visibility:**
```bash
bp sync -v private        # Only private
bp sync -v organization   # Only org-wide
bp sync -v public         # Only public
```

**Clean stale files:**
```bash
bp sync --clean           # Remove local files not in remote
```

**Preview changes:**
```bash
bp sync --dry-run         # Show what would be synced
```

### Execution

Run the sync command:
```bash
bp sync $ARGUMENTS
```

### Post-Sync Analysis

After syncing, report:
1. Number of blueprints synced by visibility
2. Any new blueprints added
3. Any blueprints updated
4. Any stale files removed (if --clean)
5. Total disk usage

### Directory Structure After Sync

```
blueprints/studio/
├── private/
│   ├── blueprint-name-uuid.json
│   └── ...
├── org-wide/
│   └── ...
├── public-owned/
│   └── ...
└── public-unowned/
    └── ...
```

Each JSON file contains the full blueprint data from the API.
