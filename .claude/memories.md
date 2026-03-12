# BP-SDK Project Memories

## Project Overview

BP-SDK is a Python SDK for JSON-based CRUD operations on Lyzr blueprints and agents. It manages both the Agent API and Blueprint API in sync.

## Key Architecture Decisions

### Modernization (January 2026)
- Removed `core/` directory (~3500 lines) - was embedded lyzr-sdk, only HTTPClient was needed
- Removed `builders/instruction.py` (935 lines) - was never used
- Removed `schemas/` directory (~750 lines) - only used by instruction.py
- Created `api/http.py` - new simplified sync HTTPClient using httpx
- Code reduced from 3866 to 2219 lines (43% reduction)
- Tests: 251 passing, 75% coverage

### Design Principles
- **Stateless**: No local database; always fetches fresh data from APIs
- **Dual API**: Manages both Agent API (agents) and Blueprint API (pagos) in sync
- **Atomic Operations**: Automatic rollback on failure
- **YAML-first**: Supports YAML workflow for GitOps

## Critical API Quirks

### Fields That Must Be Arrays (Never None)
Setting these to `None` causes "NoneType is not iterable" errors during clone:
- **Agent Level**: `managed_agents`, `tool_configs`, `features`, `tools`, `files`, `artifacts`, `personas`, `messages`, `a2a_tools`
- **Blueprint Root**: `tags`, `shared_with_users`, `shared_with_organizations`, `user_ids`, `organization_ids`, `permissions`, `assets`

Use `sanitize_agent_data()` to handle this automatically.

### Field Name Mapping
| SDK Field | API Field |
|-----------|-----------|
| `role` | `agent_role` |
| `goal` | `agent_goal` |
| `context` | `agent_context` |
| `output_format` | `agent_output` |
| `usage_description` | `tool_usage_description` |

## Common Operations

### Always Sync After Agent Changes
```python
client._agent_api.update(agent_id, payload)
client.sync(blueprint_id)  # Required to update tree
```

### Add Worker
```python
worker = AgentConfig(
    name="Worker",
    description="...",
    instructions="...",
    usage_description="...",  # REQUIRED for workers
)
blueprint = client.add_worker(blueprint_id, worker)
```

### YAML Workflow
```python
blueprint = client.create_from_yaml(Path("blueprint.yaml"))
blueprint = client.update_from_yaml(Path("blueprint.yaml"))
client.export_to_yaml(blueprint_id, Path("./output"))
```

## Testing

```bash
pytest tests/ -v              # Run all tests
pytest --cov=sdk           # With coverage
ruff check sdk/            # Lint
mypy sdk/                  # Type check
```

## File Structure

```
bp-sdk/
├── sdk/
│   ├── client.py           # BlueprintClient (main interface)
│   ├── models.py           # Pydantic models
│   ├── exceptions.py       # Exception hierarchy
│   ├── api/
│   │   ├── http.py        # HTTPClient (sync)
│   │   ├── agent.py       # AgentAPI
│   │   └── blueprint.py   # BlueprintAPI
│   ├── builders/
│   │   ├── payload.py     # PayloadBuilder
│   │   └── tree.py        # TreeBuilder
│   ├── yaml/              # YAML workflow
│   ├── utils/             # Sanitization, validation
│   └── cli/               # CLI commands
├── lyzr-org/              # YAML collections
│   ├── blueprints/        # Blueprint YAML definitions
│   └── agents/            # Agent YAML definitions
├── tests/
└── docs/
```

## Environment Variables

```bash
LYZR_API_KEY=...               # Agent API key
BLUEPRINT_BEARER_TOKEN=...     # Blueprint API token
LYZR_ORG_ID=...                # Organization ID
```

## API Endpoints

| Service | URL |
|---------|-----|
| Agent API | `https://agent-prod.studio.lyzr.ai` |
| Blueprint API | `https://pagos-prod.studio.lyzr.ai` |
