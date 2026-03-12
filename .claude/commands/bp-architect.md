---
description: Design a blueprint architecture for a given use case
argument-hint: [use-case-description]
allowed-tools: Read, Glob, Grep
---

## Task

Design a blueprint architecture for: $ARGUMENTS

### Analysis Process

1. **Understand the Use Case**
   - What is the primary goal?
   - What inputs does it receive?
   - What outputs should it produce?
   - What are the key quality criteria?

2. **Identify Sub-Tasks**
   - Break down the workflow into distinct steps
   - Identify what specialized skills are needed
   - Determine dependencies between tasks

3. **Decision: Single vs Multi-Agent**
   - Use single agent if task is simple and focused
   - Use multi-agent if task has distinct specialized phases

4. **Design Agent Hierarchy**
   - Define the manager's role
   - Define each worker's specialization
   - Map the delegation workflow

### Output Format

Provide the architecture as:

```
## Blueprint Architecture: [Name]

### Overview
[1-2 sentence description]

### Decision
[Single Agent / Multi-Agent] because [reason]

### Agent Structure

#### Manager: [Name]
- Model: [gpt-4o / claude-sonnet]
- Temperature: [0.3-0.5]
- Responsibility: [What it orchestrates]

#### Worker 1: [Name]
- Model: [gpt-4o-mini]
- Temperature: [0.2-0.3]
- Responsibility: [Specific task]
- Usage: [When manager should call this]

#### Worker 2: [Name]
...

### Workflow
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Directory Structure
```
blueprints/local/
├── blueprints/[name]/
│   └── blueprint.yaml
└── agents/
    ├── [manager].yaml
    ├── [worker-1].yaml
    └── [worker-2].yaml
```

### Next Steps
1. Create agent YAML files
2. Create blueprint YAML
3. Run `bp validate`
4. Run `bp create`
5. Test with `bp eval`
```

### Reference Examples

Check existing blueprints for patterns:
- Ticket Triage: `blueprints/local/blueprints/ticket-triage.yaml`
- Agent files: `blueprints/local/agents/*.yaml`
