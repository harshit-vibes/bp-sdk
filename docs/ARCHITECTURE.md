# BP-SDK Simplified Architecture

> **Version**: 2.0 (Planned)
> **Status**: Design Document
> **Date**: December 2024

---

## Executive Summary

This document outlines the simplified architecture for BP-SDK v2.0. The redesign focuses on:

1. **Dict-based inputs** - Users provide JSON/dict payloads, SDK handles transformations
2. **Multi-root hierarchy** - Blueprint accepts `root_agent_ids[]`, SDK resolves full tree
3. **Schema-driven validation** - Models define exhaustive fields + validation rules
4. **Centralized quirk handling** - All API quirks in one place
5. **Simplified API surface** - Fewer methods, consistent patterns

---

## Design Principles

### 1. User Controls Structure
```
User creates agents (with sub-agent IDs) → User creates blueprint (with root agent IDs)
SDK's job: Fetch agents, resolve hierarchy, build tree, handle API quirks
```

### 2. Models as Source of Truth
- All fields defined in models with validation rules
- Schemas compile structured input → API format
- No scattered validation logic

### 3. Single Responsibility
- `models.py` - Field definitions + validation rules
- `schemas/` - Structured input compilation (instructions, readme)
- `utils/quirks.py` - API quirk handling (sanitization, mapping)
- `client.py` - Orchestration only

---

## File Structure

```
sdk/
├── __init__.py                 # Public exports
├── client.py                   # BlueprintClient (~250 lines)
├── models.py                   # Agent, Blueprint models (~300 lines)
├── exceptions.py               # SDKError, APIError, ValidationError (~40 lines)
│
├── schemas/
│   ├── __init__.py             # Schema registry
│   ├── instructions.py         # Agent instructions schema
│   └── readme.py               # Blueprint readme schema
│
├── utils/
│   └── quirks.py               # All API quirk handling (~200 lines)
│
├── api/
│   ├── __init__.py
│   ├── agent.py                # Agent API client (keep as-is)
│   └── blueprint.py            # Blueprint API client (keep as-is)
│
└── builders/
    └── tree.py                 # Multi-root tree builder (~150 lines)
```

**Total: ~1000 lines** (down from ~2000+)

---

## Models (`models.py`)

### Design: Models Power Validation

```python
# Models define:
# 1. All fields (exhaustive)
# 2. Validation rules per field
# 3. API field mappings
# 4. Default values
# 5. Required vs optional

# Validation is driven by model definitions, not scattered code
```

### Agent Model

```python
@dataclass
class AgentField:
    """Field definition for Agent model."""
    name: str                           # SDK field name
    api_name: str | None = None         # API field name (if different)
    type: type = str                    # Python type
    required: bool = False              # Is field required?
    default: Any = None                 # Default value
    validation: dict | None = None      # Validation rules

AGENT_FIELDS = [
    # Identity
    AgentField("name", required=True, validation={"min_length": 1, "max_length": 100}),
    AgentField("description", required=True, validation={"min_length": 20}),

    # Instructions (SDK schema field)
    AgentField("instructions", api_name="agent_instructions", required=True,
               validation={"min_length": 50, "min_words": 10}),

    # Persona fields (SDK → API mapping)
    AgentField("role", api_name="agent_role",
               validation={"min_length": 15, "max_length": 80,
                          "forbidden": ["worker", "helper", "bot", "agent", "assistant"]}),
    AgentField("goal", api_name="agent_goal",
               validation={"min_length": 50, "max_length": 300}),
    AgentField("context", api_name="agent_context"),
    AgentField("output_format", api_name="agent_output"),
    AgentField("examples", type=str),  # String, not array

    # LLM config
    AgentField("model", default="gpt-4o"),
    AgentField("temperature", type=float, default=0.3,
               validation={"min": 0.0, "max": 1.0}),
    AgentField("top_p", type=float, default=1.0,
               validation={"min": 0.0, "max": 1.0}),

    # Features
    AgentField("features", type=list, default_factory=list,
               validation={"allowed": ["memory", "voice", "context", "file_output",
                                       "image_output", "reflection", "groundedness",
                                       "fairness", "rai", "llm_judge"]}),

    # Worker-specific
    AgentField("usage_description", api_name="tool_usage_description",
               validation={"required_for_worker": True}),

    # Sub-agents (manager only)
    AgentField("managed_agents", type=list, default_factory=list),
]
```

### Blueprint Model

```python
BLUEPRINT_FIELDS = [
    # Identity
    BlueprintField("name", required=True, validation={"min_length": 1, "max_length": 100}),
    BlueprintField("description", required=True, validation={"min_length": 20}),

    # Hierarchy
    BlueprintField("root_agent_ids", type=list, required=True,
                   validation={"min_length": 1}),

    # Visibility (part of blueprint, not separate)
    BlueprintField("visibility", api_name="share_type", default="private",
                   validation={"allowed": ["private", "organization", "public"]}),

    # Catalog
    BlueprintField("category"),
    BlueprintField("tags", type=list, default_factory=list,
                   validation={"max_length": 20}),

    # Documentation (SDK schema field)
    BlueprintField("readme", type=(str, dict)),  # Raw markdown or schema dict

    # Orchestration
    BlueprintField("orchestration_type", default="Manager Agent"),
    BlueprintField("orchestration_name"),
]
```

---

## Schemas (`schemas/`)

### Purpose
Schemas handle **structured input compilation**:
- User provides dict with sections
- SDK compiles to final string/format
- Validation rules from schema definition

### Instructions Schema

```python
INSTRUCTIONS_SCHEMA = {
    "version": "1.0",
    "sections": [
        {
            "key": "role",
            "label": "Role",
            "api_field": "agent_role",
            "validation": "from_model",  # Uses AGENT_FIELDS validation
        },
        {
            "key": "goal",
            "label": "Goal",
            "api_field": "agent_goal",
            "validation": "from_model",
        },
        {
            "key": "context",
            "label": "Context",
            "api_field": "agent_context",
        },
        {
            "key": "output_format",
            "label": "Output Format",
            "api_field": "agent_output",
        },
        {
            "key": "examples",
            "label": "Examples",
            "api_field": "examples",
        },
        {
            "key": "body",
            "label": "Instructions",
            "compile_only": True,  # Goes into compiled text, not separate field
            "required": True,
        },
    ],
    "compile_to": "agent_instructions",
}
```

### README Schema

```python
README_SCHEMA = {
    "version": "1.0",
    "sections": [
        {"key": "overview", "label": "Overview", "required": True},
        {"key": "use_cases", "label": "Use Cases", "type": "list"},
        {"key": "agents", "label": "Agents", "type": "dict"},
        {"key": "configuration", "label": "Configuration"},
        {"key": "examples", "label": "Examples"},
        {"key": "limitations", "label": "Limitations"},
    ],
    "compile_to": "blueprint_info.documentation_data.markdown",
}
```

---

## API Quirks (`utils/quirks.py`)

### All Quirks in One Place

| Quirk | Problem | Solution |
|-------|---------|----------|
| **Iterable fields** | 23 fields must be arrays, never None | `sanitize_agent()`, `sanitize_blueprint()` |
| **String fields** | `examples` etc. must be strings, not arrays | Field type enforcement |
| **Field mapping** | SDK uses `role`, API uses `agent_role` | `FIELD_MAPPING` dict |
| **managed_agents** | Lost during updates if not preserved | `preserve_managed_agents()` |
| **Provider resolution** | Model name → provider + credential | `resolve_provider()` |
| **Feature building** | Feature name → API config object | `build_features()` |
| **blueprint_data.agents** | Stale snapshot, may not reflect latest | Always fetch from Agent API |

### Implementation

```python
# All quirk-related constants and functions in one file

AGENT_ITERABLE_FIELDS = [...]
BLUEPRINT_ITERABLE_FIELDS = [...]
STRING_FIELDS = [...]
FIELD_MAPPING = {...}
PROVIDER_MAP = {...}
FEATURE_CONFIGS = {...}

def sanitize_agent(data: dict) -> dict: ...
def sanitize_blueprint(data: dict) -> dict: ...
def preserve_managed_agents(current: dict, updates: dict) -> dict: ...
def resolve_provider(model: str) -> tuple[str, str]: ...
def build_features(names: list[str]) -> list[dict]: ...
def map_fields(data: dict) -> dict: ...
```

---

## Client (`client.py`)

### Public API

```python
class BlueprintClient:
    # Agent Operations
    def create_agent(self, payload: dict) -> dict
    def get_agent(self, agent_id: str) -> dict
    def update_agent(self, agent_id: str, updates: dict) -> dict
    def delete_agent(self, agent_id: str) -> bool

    # Blueprint Operations
    def create_blueprint(self, config: dict) -> Blueprint
    def get_blueprint(self, blueprint_id: str) -> Blueprint
    def list_blueprints(self, page=1, page_size=50, **filters) -> tuple[list[Blueprint], dict]
    def update_blueprint(self, blueprint_id: str, updates: dict, sync_agents=False) -> Blueprint
    def delete_blueprint(self, blueprint_id: str, delete_agents=True) -> bool
    def clone_blueprint(self, blueprint_id: str, new_name=None) -> Blueprint

    # Internal (not public)
    def _build_tree_from_agents(self, root_agent_ids: list[str]) -> dict
    def _extract_root_ids(self, blueprint_data: dict) -> list[str]
```

### Method Behavior

| Method | Behavior |
|--------|----------|
| `create_agent` | Validates → Compiles instructions → Maps fields → Sanitizes → Creates |
| `update_agent` | Validates → Compiles → Maps → Preserves managed_agents → Updates |
| `create_blueprint` | Validates → Compiles readme → Resolves hierarchy → Builds tree → Creates |
| `update_blueprint` | Validates → Compiles → Optionally syncs tree → Updates |
| `list_blueprints` | Always returns `(blueprints, pagination)` |

---

## Exceptions (`exceptions.py`)

### Simplified Hierarchy

```python
class SDKError(Exception):
    """Base exception with message and details dict."""
    message: str
    details: dict

class APIError(SDKError):
    """HTTP/API errors with endpoint and status_code."""
    endpoint: str
    status_code: int

class ValidationError(SDKError):
    """Validation failures with errors list and optional warnings."""
    errors: list[str]
    warnings: list[str]
```

### Removed
- `AgentCreationError` - Use `APIError` or `ValidationError`
- `BlueprintCreationError` - Use `APIError` or `ValidationError`
- `SyncError` - Use `SDKError`
- `NetworkError` - Use `APIError`
- `TimeoutError` - Use `APIError`

---

## Tree Builder (`builders/tree.py`)

### Multi-Root Support

```python
class TreeBuilder:
    def build_multi_root(
        self,
        agents: dict[str, dict],      # All agents {id: data}
        root_ids: list[str],          # Root agent IDs
        edges: list[tuple[str, str]], # (parent_id, child_id) pairs
    ) -> dict:
        """Build ReactFlow tree supporting multiple root agents."""
        # Calculate positions for multi-root layout
        # Build nodes for all agents
        # Build edges from parent-child pairs
        # Return {agents, nodes, edges, tree_structure, manager_agent_id}
```

### Position Calculation

```
Root 1          Root 2          Root 3
  │               │               │
  ├── Child 1.1   ├── Child 2.1   └── Child 3.1
  └── Child 1.2   └── Child 2.2       ├── Grandchild 3.1.1
                                      └── Grandchild 3.1.2
```

---

## Usage Examples

### Creating Agents

```python
from sdk import BlueprintClient

client = BlueprintClient(
    agent_api_key="...",
    blueprint_bearer_token="...",
    organization_id="...",
)

# Create worker with structured instructions
worker = client.create_agent({
    "name": "Resume Screener",
    "description": "Screens candidate resumes against job requirements",
    "instructions": {
        "role": "Resume Analysis Specialist",
        "goal": "Efficiently screen candidates by analyzing resumes against job requirements",
        "context": "You work in a fast-paced HR department handling high volume recruiting",
        "output_format": "JSON with score (1-10) and reasoning",
        "body": "You are a resume screening specialist. When given a resume and job description...",
    },
    "model": "gpt-4o",
    "temperature": 0.3,
    "features": ["memory"],
    "usage_description": "Use for screening and analyzing candidate resumes",
})

# Create manager with sub-agents
manager = client.create_agent({
    "name": "HR Manager",
    "description": "Orchestrates HR workflows across specialized workers",
    "instructions": {
        "role": "HR Operations Coordinator",
        "goal": "Efficiently orchestrate hiring workflows by delegating to specialized workers",
        "body": "You are an HR manager who coordinates hiring workflows...",
    },
    "model": "gpt-4o",
    "managed_agents": [
        {"id": worker["agent_id"], "name": "Resume Screener", "usage_description": "..."},
    ],
})
```

### Creating Blueprint

```python
# Create blueprint from root agents
blueprint = client.create_blueprint({
    "name": "HR Assistant",
    "description": "Automates HR workflows with intelligent agents",
    "root_agent_ids": [manager["agent_id"]],  # SDK resolves full hierarchy
    "category": "Human Resources",
    "tags": ["hr", "recruiting", "automation"],
    "visibility": "private",
    "readme": {
        "overview": "This blueprint automates common HR workflows",
        "use_cases": [
            "Resume screening",
            "Interview scheduling",
            "Candidate communication",
        ],
        "agents": {
            "HR Manager": "Orchestrates all HR tasks",
            "Resume Screener": "Analyzes resumes against requirements",
        },
        "configuration": "1. Ensure OpenAI API key is configured\n2. Set up email integration",
    },
})

print(blueprint.studio_url)
```

### Updating

```python
# Update blueprint metadata
blueprint = client.update_blueprint(blueprint.id, {
    "name": "HR Assistant Pro",
    "visibility": "organization",
    "tags": ["hr", "enterprise"],
})

# Update and sync agent changes
blueprint = client.update_blueprint(blueprint.id, {}, sync_agents=True)
```

### Listing

```python
# Always returns (blueprints, pagination)
blueprints, pagination = client.list_blueprints(
    page=1,
    page_size=20,
    category="Human Resources",
    share_type="public",
)

print(f"Found {pagination['total']} blueprints")
for bp in blueprints:
    print(f"- {bp.name}: {bp.studio_url}")
```

---

## Migration Guide

### From v1.0 to v2.0

| v1.0 | v2.0 |
|------|------|
| `BlueprintConfig(...)` | `{"name": ..., "root_agent_ids": [...]}` |
| `AgentConfig(...)` | `{"name": ..., "instructions": {...}}` |
| `client.create(config)` | `client.create_blueprint(config)` |
| `client.get_all()` | `client.list_blueprints()[0]` |
| `client.get_all_with_pagination()` | `client.list_blueprints()` |
| `client.set_visibility(id, Visibility.PUBLIC)` | `client.update_blueprint(id, {"visibility": "public"})` |
| `client.sync(id)` | `client.update_blueprint(id, {}, sync_agents=True)` |
| `client.add_worker(id, worker)` | Create agent, update manager's managed_agents, sync |
| `client.remove_worker(id, worker_id)` | Delete agent, update manager's managed_agents, sync |
| `client.doctor(id)` | Validation happens automatically on create/update |

---

## Implementation Phases

### Phase 1: Models & Exceptions
- [ ] Define `Agent` model with all fields and validation rules
- [ ] Define `Blueprint` model with all fields and validation rules
- [ ] Implement model-driven validation
- [ ] Simplify exceptions to 3 classes

### Phase 2: Schemas & Quirks
- [ ] Create `schemas/instructions.py`
- [ ] Create `schemas/readme.py`
- [ ] Consolidate all quirks into `utils/quirks.py`

### Phase 3: Tree Builder
- [ ] Update `TreeBuilder` for multi-root support
- [ ] Update position calculation for nested hierarchies

### Phase 4: Client
- [ ] Rewrite `client.py` with new API
- [ ] Integrate models, schemas, quirks
- [ ] Remove deprecated methods

### Phase 5: Tests & Docs
- [ ] Update all tests
- [ ] Update README.md
- [ ] Update CLAUDE.md

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Lines of code | ~2000+ | ~1000 |
| Public methods | 15+ | 10 |
| Model classes | 8 | 2 |
| Exception classes | 7 | 3 |
| Validation files | 3 | 1 (model-driven) |

---

## Appendix: Complete Field Reference

### Agent Fields (Exhaustive)

| SDK Field | API Field | Type | Required | Validation |
|-----------|-----------|------|----------|------------|
| `name` | `name` | str | ✅ | 1-100 chars |
| `description` | `description` | str | ✅ | ≥20 chars |
| `instructions` | `agent_instructions` | str/dict | ✅ | ≥50 chars, ≥10 words |
| `role` | `agent_role` | str | | 15-80 chars, no generic terms |
| `goal` | `agent_goal` | str | | 50-300 chars |
| `context` | `agent_context` | str | | |
| `output_format` | `agent_output` | str | | |
| `examples` | `examples` | str | | String only, not array |
| `model` | `model` | str | | Default: gpt-4o |
| `temperature` | `temperature` | float | | 0.0-1.0, default: 0.3 |
| `top_p` | `top_p` | float | | 0.0-1.0, default: 1.0 |
| `features` | `features` | list | | Valid feature names |
| `usage_description` | `tool_usage_description` | str | For workers | |
| `managed_agents` | `managed_agents` | list | | For managers |

### Blueprint Fields (Exhaustive)

| SDK Field | API Field | Type | Required | Validation |
|-----------|-----------|------|----------|------------|
| `name` | `name` | str | ✅ | 1-100 chars |
| `description` | `description` | str | ✅ | ≥20 chars |
| `root_agent_ids` | - | list | ✅ | ≥1 agent ID |
| `visibility` | `share_type` | str | | private/organization/public |
| `category` | `category` | str | | |
| `tags` | `tags` | list | | ≤20 tags |
| `readme` | `blueprint_info.documentation_data.markdown` | str/dict | | |
| `orchestration_type` | `orchestration_type` | str | | Default: Manager Agent |
| `orchestration_name` | `orchestration_name` | str | | |
