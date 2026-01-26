# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## MANDATORY RULES (Read First)

### Rule 1: ONLY Use BlueprintClient

**STOP. Before writing ANY code that touches blueprints or agents, ask yourself:**
> "Am I using `BlueprintClient` methods?"

If the answer is NO, you are doing it wrong.

```python
# CORRECT - Always start with this
from sdk import BlueprintClient

client = BlueprintClient(
    agent_api_key="...",
    blueprint_bearer_token="...",
    organization_id="..."
)
```

### Rule 2: NEVER Write Raw API Calls

**These are FORBIDDEN:**

```python
# WRONG - Raw requests
import requests
response = requests.get(f'{BASE_URL}/v3/agents/{agent_id}')
response = requests.put(f'{BASE_URL}/v3/agents/{agent_id}', json=payload)

# WRONG - Using internal APIs directly
client._agent_api.get(agent_id)
client._agent_api.update(agent_id, payload)
client._blueprint_api.update(blueprint_id, payload)

# WRONG - Building payloads manually
tree = TreeBuilder().build(...)
payload = PayloadBuilder().build_agent_payload(...)
```

### Rule 3: Use the Right Method for Each Task

| Task | Correct Method | WRONG Approach |
|------|----------------|----------------|
| Update agent model/config | `client.sync()` after Agent API update | Manual tree rebuild |
| Add worker to blueprint | `client.add_worker()` | Create agent + manual sync |
| Remove worker | `client.remove_worker()` | Delete agent + manual sync |
| Update blueprint metadata | `client.update_metadata()` | Raw API call |
| Get fresh agent data | `client.get_manager()` / `client.get_workers()` | `blueprint_data.agents` |
| Rebuild tree after changes | `client.sync()` | Manual TreeBuilder |

---

## Quick Reference: Common Operations

### 1. Sync Blueprint After External Agent Changes

```python
# When agents were updated outside the SDK (e.g., via Agent API directly)
blueprint = client.sync(blueprint_id)
```

### 2. Update Agent Model

```python
# Step 1: Get current agent, modify, update via Agent API
from sdk.utils.sanitize import sanitize_agent_data

agent_data = client._agent_api.get(agent_id)
payload = sanitize_agent_data(agent_data)
payload['model'] = 'gpt-4o-mini'
payload['provider_id'] = 'OpenAI'
payload['llm_credential_id'] = 'lyzr_openai'
for field in ['_id', 'created_at', 'updated_at', 'api_key']:
    payload.pop(field, None)
client._agent_api.update(agent_id, payload)

# Step 2: Sync blueprint to update tree
blueprint = client.sync(blueprint_id)
```

### 3. Add a Worker

```python
from sdk import AgentConfig

worker = AgentConfig(
    name="New Worker",
    description="Does something useful",
    instructions="You are a helpful assistant...",
    usage_description="Use this worker for X tasks",  # REQUIRED for workers
    model="gpt-4o-mini",
)

blueprint = client.add_worker(blueprint_id, worker)
```

### 4. Get Blueprint Info

```python
blueprint = client.get(blueprint_id)
print(blueprint.name)
print(blueprint.manager_id)
print(blueprint.worker_ids)
print(blueprint.studio_url)
```

### 5. Update Metadata Only (Fast Path)

```python
blueprint = client.update_metadata(
    blueprint_id,
    name="New Name",
    description="New description",
    tags=["tag1", "tag2"],
    category="people",
)
```

---

## Decision Tree: What Method Should I Use?

```
START
  │
  ├─► Need to CREATE a new blueprint?
  │     └─► client.create(BlueprintConfig(...))
  │
  ├─► Need to UPDATE agent configs (model, instructions, etc.)?
  │     └─► 1. Update agent via _agent_api.update()
  │         2. Then call client.sync(blueprint_id)
  │
  ├─► Need to ADD a new worker?
  │     └─► client.add_worker(blueprint_id, AgentConfig(...))
  │
  ├─► Need to REMOVE a worker?
  │     └─► client.remove_worker(blueprint_id, worker_id)
  │
  ├─► Need to UPDATE only name/description/tags?
  │     └─► client.update_metadata(blueprint_id, ...)
  │
  ├─► Need to GET fresh agent data?
  │     └─► client.get_manager(blueprint_id)
  │         client.get_workers(blueprint_id)
  │
  ├─► Blueprint tree is out of sync?
  │     └─► client.sync(blueprint_id)
  │
  └─► Need to DELETE a blueprint?
        └─► client.delete(blueprint_id)
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Manual Tree Building

```python
# WRONG
from sdk.builders.tree import TreeBuilder
tree = TreeBuilder().build(manager_data, workers_data, manager_id, worker_ids)
bp_api.update(blueprint_id, {"blueprint_data": tree})

# CORRECT
client.sync(blueprint_id)  # Automatically rebuilds tree
```

### Anti-Pattern 2: Raw HTTP Requests

```python
# WRONG
import requests
response = requests.put(
    f'https://agent-prod.studio.lyzr.ai/v3/agents/{agent_id}',
    headers={'X-API-Key': API_KEY},
    json=payload
)

# CORRECT
client._agent_api.update(agent_id, payload)
client.sync(blueprint_id)
```

### Anti-Pattern 3: Reading from blueprint_data.agents

```python
# WRONG - This data may be stale
bp = client._blueprint_api.get(blueprint_id)
agent = bp['blueprint_data']['agents'][agent_id]

# CORRECT - Always fetch fresh from Agent API
manager = client.get_manager(blueprint_id)
workers = client.get_workers(blueprint_id)
```

### Anti-Pattern 4: Forgetting to Sync

```python
# WRONG - Blueprint tree not updated
client._agent_api.update(agent_id, new_payload)
# Blueprint still shows old data!

# CORRECT - Always sync after agent changes
client._agent_api.update(agent_id, new_payload)
client.sync(blueprint_id)
```

---

## Development Commands

```bash
# Install for development
pip install -e ".[dev]"

# Run tests
pytest                          # All tests
pytest tests/test_models.py -v  # Single file
pytest -k "test_delete"         # Run tests matching pattern
pytest --cov=sdk             # With coverage

# Linting and type checking
ruff check sdk/              # Lint
ruff check sdk/ --fix        # Auto-fix lint issues
mypy sdk/                    # Type check
```

---

## Architecture

### Design Principles

- **Stateless**: No local database; always fetches fresh data from APIs
- **Dual API**: Manages both Agent API (agents) and Blueprint API (pagos) in sync
- **Atomic Operations**: Automatic rollback on failure (created agents deleted if blueprint creation fails)
- **JSON-Driven**: Pydantic models as source of truth for blueprint configurations

### Data Flow

```
BlueprintConfig (user input)
        │
        ▼ PayloadBuilder.build_agent_payload()
Agent Payloads → Agent API (creates agents)
        │
        ▼ TreeBuilder.build()
ReactFlow Structure (nodes, edges, agents dict)
        │
        ▼ PayloadBuilder.build_blueprint_payload()
Blueprint Payload → Blueprint API (creates blueprint)
        │
        ▼ Blueprint.from_api_response()
Blueprint Object (returned to user)
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `BlueprintClient` | `sdk/client.py` | Main SDK interface - all CRUD operations |
| `HTTPClient` | `sdk/api/http.py` | Sync HTTP client for API communication |
| `AgentAPI` | `sdk/api/agent.py` | Agent API client (uses HTTPClient) |
| `BlueprintAPI` | `sdk/api/blueprint.py` | Blueprint API client (Pagos service) |
| `PayloadBuilder` | `sdk/builders/payload.py` | Constructs API request payloads |
| `TreeBuilder` | `sdk/builders/tree.py` | Builds ReactFlow tree structure for visualization |
| `sanitize_agent_data` | `sdk/utils/sanitize.py` | Prevents NoneType iteration errors |

### YAML Workflow (`sdk/yaml/`)

YAML-based blueprint definitions for version control and GitOps:

| Module | Purpose |
|--------|---------|
| `sdk/yaml/loader.py` | Load and parse YAML blueprint files |
| `sdk/yaml/writer.py` | Export blueprints to YAML format |
| `sdk/yaml/converter.py` | Convert between YAML and SDK models |
| `sdk/yaml/models.py` | Pydantic models for YAML structures |
| `sdk/yaml/ids.py` | Manage blueprint/agent ID mappings |

**Import patterns:**
```python
# Blueprint operations
from sdk import BlueprintClient, BlueprintConfig, AgentConfig

# YAML workflow
from pathlib import Path
blueprint = client.create_from_yaml(Path("my-blueprint/blueprint.yaml"))
blueprint = client.update_from_yaml(Path("my-blueprint/blueprint.yaml"))
client.export_to_yaml(blueprint_id, Path("./exported"))
```

---

## API Reference

### Configuration

#### Environment Variables

```bash
LYZR_API_KEY=...               # For Agent API (X-API-Key header)
BLUEPRINT_BEARER_TOKEN=...     # For Blueprint API (Bearer token)
LYZR_ORG_ID=...                # Organization context
```

#### API Endpoints

| Environment | Agent API | Blueprint API |
|-------------|-----------|---------------|
| Production | `https://agent-prod.studio.lyzr.ai` | `https://pagos-prod.studio.lyzr.ai` |

#### Blueprint API Paths

The SDK uses the correct versioned API paths that match the Pagos backend routing:

| Operation | SDK Path (Correct) | Web App Path (Wrong) |
|-----------|-------------------|---------------------|
| Create | `/api/v1/blueprints/blueprints` | `/blueprints/blueprints` |
| List | `/api/v1/blueprints/blueprints` | `/blueprints/blueprints` |
| Get | `/api/v1/blueprints/blueprints/{id}` | `/blueprints/blueprints/{id}` |
| Update | `/api/v1/blueprints/blueprints/{id}` | `/blueprints/blueprints/{id}` |
| Delete | `/api/v1/blueprints/blueprints/{id}` | `/blueprints/blueprints/{id}` |
| Share | `/api/v1/blueprints/blueprints/{id}/share` | `/blueprints/blueprints/{id}/share` |
| Clone | `/api/v1/blueprints/blueprints/clone` | `/blueprints/blueprints/clone` |

**Why the `/api/v1` prefix is required:**

The Pagos backend routes are defined as:
```python
# pagos/main.py
app.include_router(blueprints_router, prefix="/api/v1/blueprints", ...)

# pagos/app/blueprints/endpoints.py
router = APIRouter(prefix="/blueprints", ...)
```

This results in full paths: `/api/v1/blueprints` + `/blueprints` = `/api/v1/blueprints/blueprints`

**Note:** The web app (`agent-studio-ui/src/services/blueprintApiService.ts`) is missing the `/api/v1` prefix. It may work in production due to nginx/API gateway rewrite rules, but the SDK uses the correct paths that match the backend directly.

#### Model Provider Prefixes

| Provider | Model Prefix | Credential ID |
|----------|--------------|---------------|
| OpenAI | (none) | `lyzr_openai` |
| Anthropic | `anthropic/` | `lyzr_anthropic` |
| Google | `gemini/` | `lyzr_google` |
| Groq | `groq/` | `lyzr_groq` |
| Bedrock | `bedrock/` | `lyzr_bedrock` |
| Perplexity | `perplexity/` | `lyzr_perplexity` |

### Models with Built-in Web Search

Only specific models have real-time web search capability:

| Provider | Model | Web Search |
|----------|-------|------------|
| **Anthropic** | All Claude models | ✅ `web_search_options` |
| **Perplexity** | `perplexity/sonar` | ❌ |
| **Perplexity** | `perplexity/sonar-pro` | ❌ |
| **Perplexity** | `perplexity/sonar-reasoning` | ✅ Internet Search |
| **Perplexity** | `perplexity/sonar-reasoning-pro` | ✅ Internet Search |
| **Perplexity** | `perplexity/sonar-deep-research` | ✅ Internet Search |

**For agents requiring real-time information**, use:
- Claude models (any) with `web_search_options`
- Perplexity `sonar-reasoning`, `sonar-reasoning-pro`, or `sonar-deep-research`

### Correct Field Names (API Mapping)

| Schema Field | API Field | Notes |
|--------------|-----------|-------|
| `role` | `agent_role` | 15-80 chars |
| `goal` | `agent_goal` | 50-300 chars |
| `context` | `agent_context` | Background/domain |
| `output_format` | `agent_output` | Output spec |
| `examples` | `examples` | **String only**, not array |
| `usage_description` | `tool_usage_description` | For workers |

### Fields That Must Be Arrays (never None)

Setting these to `None` causes "NoneType is not iterable" errors during clone.

**Agent Level**: `managed_agents`, `tool_configs`, `features`, `tools`, `files`, `artifacts`, `personas`, `messages`, `a2a_tools`

**Blueprint Root**: `tags`, `shared_with_users`, `shared_with_organizations`, `user_ids`, `organization_ids`, `permissions`, `assets`

The `sanitize_agent_data()` function handles this automatically.

---

## Client Method Reference

| Category | Methods |
|----------|---------|
| **CRUD** | `create()`, `get()`, `get_all()`, `update()`, `delete()` |
| **Visibility** | `set_visibility()`, `clone()` |
| **Validation** | `doctor()`, `doctor_config()` |
| **Sync** | `sync()` |
| **Fast Path** | `update_metadata()` (skips agent sync) |
| **Worker Management** | `add_worker()`, `remove_worker()` |
| **Inspection** | `get_manager()`, `get_workers()` |
| **YAML Workflow** | `create_from_yaml()`, `update_from_yaml()`, `export_to_yaml()`, `validate_yaml()` |

---

## Exception Hierarchy

```python
from sdk.exceptions import (
    BlueprintSDKError,      # Base exception
    APIError,               # HTTP failures (status_code, endpoint, message)
    NetworkError,           # Connection failures
    TimeoutError,           # Request timeouts
    ValidationError,        # Config validation (errors list)
    AgentCreationError,     # Agent creation failed (created_ids for rollback)
    BlueprintCreationError, # Blueprint creation failed (created_agent_ids)
    SyncError,              # Agent/Blueprint sync failures
    RollbackError,          # Cleanup failures (failed_cleanups list)
)
```

---

## Testing Patterns

Tests use `unittest.mock` to patch API clients:

```python
@patch("sdk.client.AgentAPI")
@patch("sdk.client.BlueprintAPI")
def test_create(self, mock_bp_api_class, mock_agent_api_class):
    mock_agent_api = MagicMock()
    mock_bp_api = MagicMock()
    mock_agent_api_class.return_value = mock_agent_api
    mock_bp_api_class.return_value = mock_bp_api

    # Setup mock responses
    mock_agent_api.create.return_value = {"agent_id": "test-id"}
    mock_agent_api.get.return_value = {"name": "Test", ...}

    # Test client operations
    client = BlueprintClient(...)
```

---

## CLI Reference (`bp` command)

The SDK provides a comprehensive CLI for blueprint management.

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `bp create <file>` | Create blueprint from YAML | `bp create my-bp/blueprint.yaml` |
| `bp get <id>` | Fetch and display blueprint | `bp get bp-123 -f json` |
| `bp list` | List blueprints with filters | `bp list --mine -v private` |
| `bp update <file>` | Update blueprint from YAML | `bp update my-bp/blueprint.yaml` |
| `bp delete` | Delete blueprint | `bp delete --id bp-123` |
| `bp validate <file>` | Validate YAML without API calls | `bp validate my-bp/blueprint.yaml` |
| `bp sync` | Sync blueprints from API to local | `bp sync -d ./blueprints/studio` |
| `bp eval <agent-id> <query>` | Test agent with query + trace | `bp eval agent-123 "Hello"` |

### List Command Options

```bash
bp list                          # List all accessible blueprints
bp list --mine                   # Only my blueprints
bp list -v private               # Filter by visibility
bp list -c people                # Filter by category
bp list -l 100                   # Limit results
bp list --summary                # Show statistics
bp list --report                 # Generate roadmap comparison report
bp list --report -o custom.md    # Save report to custom path
bp list --csv report.csv         # Export as CSV (all columns)
```

### Roadmap Report (`bp list --report`)

Generates a comprehensive report comparing blueprints against Linear tasks.

**Output Structure:**
- Summary statistics (planned/adhoc/backlog/unowned counts)
- Planned blueprints (from roadmap, organized by status)
- Ad-hoc blueprints (created outside roadmap)
- Backlog tasks (not yet started)
- Unowned public blueprints (from other users)

**Blueprint Classification:**

| Category | Definition | Source of Truth |
|----------|------------|-----------------|
| **Planned** | Has Linear task OR in blueprint-map.yaml | `roadmap/blueprint-map.yaml` |
| **Ad-hoc** | Owned but not in roadmap | Comparison check |
| **Backlog** | Linear task without blueprint | Linear API |
| **Unowned** | Public blueprints from others | API filter |

**Status Mapping (Share Type → Linear State):**

| Share Type | Linear State | Report Section |
|------------|--------------|----------------|
| `public` | Done | ✅ Done |
| `organization` | In Review | 🔄 Review |
| `private` | In Progress | 🔨 In Progress |

### CSV Export

```bash
bp list --csv roadmap/report.csv
```

Exports all blueprint data with columns:
- `blueprint_id`, `name`, `category`, `share_type`, `classification`
- `status`, `task_id`, `linear_id`, `week`, `type`
- `platform_url`, `linear_url`, `owner`, `description`

---

## Roadmap Directory (`roadmap/`)

| File | Purpose |
|------|---------|
| `blueprint-map.yaml` | **Source of truth** - Maps Linear task IDs to blueprint IDs |
| `projects.csv` | Linear project definitions |
| `report.md` | Generated markdown report (from `bp list --report`) |
| `report.csv` | Generated CSV export (from `bp list --csv`) |
| `README.md` | Documentation |

### Blueprint Map Format

```yaml
mappings:
  # Week 1
  6d25116a-8c60-4541-...: 8fa3b79b-18cd-...  # BP-038 Ticket Triage Agent
  131af90e-613f-4af0-...: 8c08c208-3f6a-...  # BP-039 URL Powered FAQ Assistant

  # Featured (no week)
  efa3bc0f-cf11-47c2-...: 2930ae68-d2de-...  # BP-049 Legal Contract Clause Analyzer
```

The mapping file is the **source of truth** for determining which blueprints are "planned" vs "ad-hoc". Even if a Linear task is deleted after completion, blueprints in this mapping remain classified as "planned".

---

## Claude Code Automation

This repository includes a comprehensive Claude Code automation system for blueprint development. The system consists of **skills** (auto-applied knowledge), **slash commands** (manual invocations), and **sub-agents** (delegated specialists).

### Skills (`.claude/skills/`)

Skills are automatically loaded when working in this repository.

| Skill | Purpose |
|-------|---------|
| `blueprint-architecture` | Multi-agent orchestration patterns, single vs multi-agent decisions |
| `agent-persona` | Crafting agent identities (name, description, role, goal) |
| `agent-instructions` | Writing effective agent instructions with proper structure |
| `agent-technical` | Model selection, temperature tuning, feature configuration |
| `blueprint-yaml` | SDK/CLI usage, YAML schema, common errors and fixes |
| `blueprint-readme` | Documentation structure (Problem/Approach/Capabilities) |

### Slash Commands (`.claude/commands/`)

Invoke these with `/command [args]`:

| Command | Description | Example |
|---------|-------------|---------|
| `/bp-create` | Create blueprint from YAML | `/bp-create blueprints/local/blueprints/my-bp.yaml` |
| `/bp-eval` | Test agent with query and trace | `/bp-eval agent-id "test query"` |
| `/bp-architect` | Design blueprint architecture | `/bp-architect "customer support triage"` |
| `/bp-doctor` | Diagnose blueprint issues | `/bp-doctor blueprint-id` |
| `/bp-sync` | Sync blueprints from API | `/bp-sync --visibility private` |
| `/bp-linear` | Sync tasks with Linear | `/bp-linear push --dry-run` |

### Sub-Agents (`.claude/agents/`)

Sub-agents are specialized assistants that can be invoked via the Task tool:

| Agent | Model | Purpose | Skills Used |
|-------|-------|---------|-------------|
| `blueprint-architect` | sonnet | Designs multi-agent orchestration patterns | blueprint-architecture |
| `agent-crafter` | sonnet | Creates high-quality agent definitions | agent-persona, agent-instructions, agent-technical |
| `blueprint-qa` | haiku | Tests and validates blueprints | blueprint-yaml |
| `blueprint-docs` | sonnet | Writes README documentation | blueprint-readme |

### Typical Workflow

1. **Design**: Use `blueprint-architect` agent or `/bp-architect` to plan the structure
2. **Create**: Use `agent-crafter` agent to craft individual agents
3. **Build**: Use `/bp-create` to deploy the blueprint
4. **Test**: Use `/bp-eval` or `blueprint-qa` agent to validate
5. **Document**: Use `blueprint-docs` agent to write the README
6. **Diagnose**: Use `/bp-doctor` if issues arise
7. **Track**: Use `bp linear push` to sync tasks to Linear

---

## Linear Task Tracking

Blueprint development tasks are tracked in Linear. The CLI fetches tasks directly from Linear API.

### Setup

Set environment variables:

```bash
LINEAR_API_KEY=lin_api_xxx      # Linear API key
LINEAR_TEAM_ID=xxx              # Team ID for issues
```

### Commands

| Command | Description |
|---------|-------------|
| `bp linear push` | Push new tasks to Linear |
| `bp linear pull` | Pull project IDs from Linear |
| `bp linear status` | Show sync status |
| `bp linear delete-issues PROJECT_ID` | Delete all issues in a project |
| `bp linear update-initiative` | Update initiative description |

### Data Flow

```
Linear API (source of truth for tasks)
        │
        ▼ bp list --report
Fetch tasks from BP-LIB project
        │
        ▼
Compare with blueprint-map.yaml
        │
        ▼
Generate classification report
```

**Key Points:**
- Tasks are fetched directly from Linear API (no local CSV)
- `blueprint-map.yaml` maps Linear task IDs to blueprint IDs
- The mapping file persists even after Linear tasks are deleted
- Classification uses both Linear tasks AND mapping file

### projects.csv

Defines Linear projects for initialization:

```csv
id,name,initiative,team,description,state,linear_id
BP-LIB,BP Library,Blueprints,Lyzr,Blueprint instances,planned,
```
