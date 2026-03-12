---
name: blueprint-yaml
description: Create and manage blueprints using YAML definitions and the bp CLI. Use when creating blueprints, updating existing ones, validating configurations, or debugging SDK issues.
allowed-tools: Read, Write, Edit, Bash(bp:*), Bash(python:*)
---

# Blueprint YAML Workflow

## Directory Structure

```
blueprints/local/
├── blueprints/
│   └── my-blueprint/
│       └── blueprint.yaml       # Blueprint definition
└── agents/
    ├── manager-agent.yaml       # Manager agent
    ├── worker-1.yaml            # Worker agent
    └── worker-2.yaml            # Worker agent
```

## Blueprint YAML Schema

```yaml
apiVersion: lyzr.ai/v1
kind: Blueprint

metadata:
  name: "Blueprint Name"                    # Required, max 100 chars
  description: |                            # Required
    Multi-line description of what this
    blueprint does.
  category: customer-service                # Optional
  tags:                                     # Optional, max 20
    - tag1
    - tag2
  visibility: private                       # private|organization|public
  readme: |                                 # Optional, markdown
    ## The Problem
    ...

root_agents:                                # Required, at least 1
  - ../agents/manager-agent.yaml

# Auto-populated after creation (do not edit manually)
ids:
  blueprint: "uuid-here"
  agents:
    ../agents/manager-agent.yaml: "agent-id"
```

## Agent YAML Schema

```yaml
apiVersion: lyzr.ai/v1
kind: Agent

metadata:
  name: "Agent Name"                        # Required, max 100 chars
  description: |                            # Required
    What this agent does.

spec:
  # LLM Configuration
  model: gpt-4o                             # Default: gpt-4o
  temperature: 0.3                          # 0.0-1.0, default: 0.3
  top_p: 1.0                                # 0.0-1.0, default: 1.0
  response_format: text                     # text|json_object
  store_messages: true                      # default: true
  file_output: false                        # default: false

  # Persona (optional)
  role: "Expert Role Description"           # 15-80 chars
  goal: |                                   # 50-300 chars
    What success looks like for this agent.
  context: |                                # Optional
    Background information.
  output: |                                 # Optional
    Output format specification.
  examples: |                               # Optional (string, not array!)
    User: Example input
    Assistant: Example output

  # Instructions (required)
  instructions: |
    You are...

  # Worker-specific
  usage: |                                  # Required for workers
    Use this agent when you need to...

  # Features
  features:                                 # Optional list
    - memory
    - rai

# Sub-agents (makes this a manager)
sub_agents:                                 # Optional
  - worker-1.yaml
  - worker-2.yaml
```

## CLI Commands

### Create Blueprint
```bash
bp create blueprints/local/blueprints/my-blueprint/blueprint.yaml
```

Creates blueprint and all agents in Lyzr Studio. Writes IDs back to YAML files.

### Update Blueprint
```bash
bp update blueprints/local/blueprints/my-blueprint/blueprint.yaml
```

Updates existing blueprint. Requires `ids` section in YAML.

### Validate Blueprint
```bash
bp validate blueprints/local/blueprints/my-blueprint/blueprint.yaml
```

Validates YAML without API calls. Checks:
- File references exist
- YAML syntax valid
- Configuration valid
- No circular dependencies

### Delete Blueprint
```bash
bp delete --file blueprints/local/blueprints/my-blueprint/blueprint.yaml
# or
bp delete --id uuid-here
```

Deletes blueprint and all agents. Clears IDs from YAML if using `--file`.

### Get Blueprint
```bash
bp get uuid-here                    # Display details
bp get uuid-here -o ./exported      # Export to YAML
bp get uuid-here -f json            # Display as JSON
```

### List Blueprints
```bash
bp list                             # All accessible
bp list --mine                      # Only owned by me
bp list -v private                  # Only private
bp list -c customer-service         # By category
bp list --summary                   # Statistics
```

### Sync Blueprints
```bash
bp sync                             # Sync to ./blueprints/studio
bp sync -d ./my-bps                 # Custom directory
bp sync -v public                   # Only public
bp sync --clean                     # Remove stale local files
bp sync --dry-run                   # Preview changes
```

### Eval Agent
```bash
bp eval agent-id "Your query here"
bp eval agent-id "Query" --json     # JSON output with trace
bp eval agent-id "Query" --no-trace # Skip trace
bp eval agent-id "Query" -t 300     # 5 min timeout
```

### Version
```bash
bp version
```

## Common Workflows

### Creating a New Blueprint

1. **Create agent files:**
```bash
mkdir -p blueprints/local/agents
mkdir -p blueprints/local/blueprints/my-bp
```

2. **Write manager agent:**
```yaml
# blueprints/local/agents/my-manager.yaml
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: My Manager
  description: Orchestrates the workflow
spec:
  model: gpt-4o
  temperature: 0.3
  role: Workflow Orchestration Specialist
  goal: Coordinate workers to complete tasks efficiently
  instructions: |
    You are the workflow coordinator...
sub_agents:
  - worker-1.yaml
```

3. **Write worker agents:**
```yaml
# blueprints/local/agents/worker-1.yaml
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: Worker One
  description: Handles specific task
spec:
  model: gpt-4o-mini
  temperature: 0.2
  role: Specialized Task Handler
  goal: Complete the specific task accurately
  instructions: |
    You are Worker One...
  usage: |
    Use this worker when you need to handle the specific task.
```

4. **Write blueprint:**
```yaml
# blueprints/local/blueprints/my-bp/blueprint.yaml
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: My Blueprint
  description: Does something useful
  category: general
  tags: [demo]
  visibility: private
root_agents:
  - ../../agents/my-manager.yaml
```

5. **Validate:**
```bash
bp validate blueprints/local/blueprints/my-bp/blueprint.yaml
```

6. **Create:**
```bash
bp create blueprints/local/blueprints/my-bp/blueprint.yaml
```

7. **Test:**
```bash
bp eval <manager-agent-id> "Test query"
```

### Updating a Blueprint

1. **Edit YAML files** (metadata, agents, etc.)

2. **Validate changes:**
```bash
bp validate blueprints/local/blueprints/my-bp/blueprint.yaml
```

3. **Update:**
```bash
bp update blueprints/local/blueprints/my-bp/blueprint.yaml
```

### Debugging Issues

1. **Validation errors:**
```bash
bp validate --verbose blueprints/local/blueprints/my-bp/blueprint.yaml
```

2. **Agent behavior issues:**
```bash
bp eval <agent-id> "Test query" --json > debug.json
```
Review trace in debug.json.

3. **Check agent details:**
```bash
bp get <blueprint-id> -f json | jq .
```

## Environment Variables

```bash
# Required
export LYZR_API_KEY="your-api-key"
export BLUEPRINT_BEARER_TOKEN="your-token"
export LYZR_ORG_ID="your-org-id"

# Optional (override defaults)
export LYZR_AGENT_API_URL="https://agent-prod.studio.lyzr.ai"
export LYZR_BLUEPRINT_API_URL="https://pagos-prod.studio.lyzr.ai"
```

Or create `.env` file:
```
LYZR_API_KEY=your-api-key
BLUEPRINT_BEARER_TOKEN=your-token
LYZR_ORG_ID=your-org-id
```

## Common Errors

### "Placeholder text detected"
SDK validates against `[placeholder]` patterns.

```yaml
# Bad
output: |
  Category: [CATEGORY_NAME]

# Good
output: |
  Category: BILLING, TECHNICAL, ACCOUNT, FEATURE, or GENERAL
```

### "Role should not contain generic term"
Role field validates against: worker, helper, bot, agent, assistant

```yaml
# Bad
role: AI Assistant

# Good
role: Senior Support Triage Specialist
```

### "Missing usage_description"
Workers need `usage` field for manager to know when to use them.

```yaml
# Add to worker spec
spec:
  usage: |
    Use this worker when you need to classify tickets by category.
```

### "Blueprint must have at least one worker"
Either add workers via `sub_agents` or ensure manager has sub-agents.

```yaml
# Manager with sub_agents
sub_agents:
  - worker-1.yaml
```

## Reference Files

- Models: `sdk/models.py`
- YAML Models: `sdk/yaml/models.py`
- CLI: `sdk/cli/main.py`
- Example: `blueprints/local/blueprints/ticket-triage.yaml`
