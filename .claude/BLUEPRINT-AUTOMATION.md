# Blueprint Automation System

> Skills, Commands, and Sub-Agents for Blueprint Development

## Overview

This system provides Claude Code with specialized capabilities for creating, managing, and optimizing Lyzr blueprints and agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Blueprint Development                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SKILLS (Knowledge)              COMMANDS (Actions)                 │
│  ├── blueprint-architecture      ├── /bp-create                    │
│  ├── agent-persona               ├── /bp-architect                 │
│  ├── agent-instructions          ├── /bp-eval                      │
│  ├── agent-technical             ├── /bp-doctor                    │
│  ├── blueprint-yaml              └── /bp-sync                      │
│  └── blueprint-readme                                               │
│                                                                     │
│  SUB-AGENTS (Specialists)                                           │
│  ├── blueprint-architect     → Designs multi-agent systems          │
│  ├── agent-crafter          → Creates individual agents             │
│  ├── blueprint-qa           → Tests and validates                   │
│  └── blueprint-docs         → Writes documentation                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Skills

### 1. blueprint-architecture

**Purpose:** Knowledge of orchestration patterns and when to use them.

**Covers:**
- Single agent vs multi-agent decision framework
- Manager-worker pattern
- Parallel vs sequential delegation
- Agent specialization strategies
- Communication patterns between agents

### 2. agent-persona

**Purpose:** Crafting compelling agent identities.

**Covers:**
- Name: Concise, descriptive, action-oriented
- Description: What it does, when to use it
- Role: 15-80 chars, specific expertise
- Goal: 50-300 chars, measurable outcome

### 3. agent-instructions

**Purpose:** Writing clear, effective instructions.

**Covers:**
- Step-by-step process definition
- Edge case handling
- Output format specification
- Examples and counter-examples
- Constraints and guardrails

### 4. agent-technical

**Purpose:** Configuring technical parameters.

**Covers:**
- Model selection (gpt-4o, gpt-4o-mini, claude, perplexity)
- Temperature (0.0-1.0) - creativity vs consistency
- Provider and credential selection
- Tool configuration
- Web search capabilities

### 5. blueprint-yaml

**Purpose:** YAML workflow and SDK usage.

**Covers:**
- Blueprint YAML structure
- Agent YAML structure
- CLI commands (bp create, update, sync, eval)
- ID management
- Validation and debugging

### 6. blueprint-readme

**Purpose:** Writing beautiful documentation.

**Covers:**
- Problem statement (Situation, Challenge, Stakes)
- Approach (Insight, Method, Why It Works)
- Capabilities (Core, Extended, Boundaries)
- Getting Started (Prerequisites, First Run, Pro Tips)

## Slash Commands

### /bp-create [name] [category]
Create a new blueprint from scratch with guided workflow.

### /bp-architect [use-case]
Design a blueprint architecture for a given use case.

### /bp-eval [agent-id] [query]
Test an agent with a query and display trace.

### /bp-doctor [blueprint-id|file]
Diagnose issues with a blueprint.

### /bp-sync
Sync blueprints from API to local directory.

## Sub-Agents

### blueprint-architect
**Model:** sonnet
**Tools:** Read, Grep, Glob
**Skills:** blueprint-architecture

Designs multi-agent systems by:
1. Analyzing the use case
2. Identifying required capabilities
3. Designing agent hierarchy
4. Defining communication patterns
5. Outputting architecture diagram

### agent-crafter
**Model:** sonnet
**Tools:** Read, Write, Edit
**Skills:** agent-persona, agent-instructions, agent-technical

Creates individual agents by:
1. Understanding the agent's role
2. Crafting persona (name, description, role, goal)
3. Writing instructions
4. Configuring technical params
5. Outputting YAML definition

### blueprint-qa
**Model:** haiku
**Tools:** Bash, Read, Grep
**Skills:** blueprint-yaml

Tests and validates blueprints by:
1. Running bp validate
2. Running bp eval
3. Analyzing trace
4. Reporting issues
5. Suggesting fixes

### blueprint-docs
**Model:** sonnet
**Tools:** Read, Write, Edit
**Skills:** blueprint-readme

Writes documentation by:
1. Reading blueprint/agent configs
2. Understanding the solution
3. Writing Problem section
4. Writing Approach section
5. Writing Capabilities section
6. Writing Getting Started section

## Workflow

```
User Request
    │
    ▼
┌───────────────────┐
│ /bp-architect     │ → blueprint-architect agent
│ (Design Phase)    │   Uses: blueprint-architecture skill
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ agent-crafter     │ → Creates each agent
│ (Build Phase)     │   Uses: agent-persona, instructions, technical skills
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ /bp-create        │ → Executes bp CLI
│ (Deploy Phase)    │   Uses: blueprint-yaml skill
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ /bp-eval          │ → blueprint-qa agent
│ (Test Phase)      │   Tests and validates
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ blueprint-docs    │ → Writes README
│ (Document Phase)  │   Uses: blueprint-readme skill
└───────────────────┘
```

## Files

```
.claude/
├── skills/
│   ├── blueprint-architecture/
│   │   └── SKILL.md
│   ├── agent-persona/
│   │   └── SKILL.md
│   ├── agent-instructions/
│   │   └── SKILL.md
│   ├── agent-technical/
│   │   └── SKILL.md
│   ├── blueprint-yaml/
│   │   └── SKILL.md
│   └── blueprint-readme/
│       └── SKILL.md
├── commands/
│   ├── bp-create.md
│   ├── bp-architect.md
│   ├── bp-eval.md
│   ├── bp-doctor.md
│   └── bp-sync.md
└── agents/
    ├── blueprint-architect/
    │   └── AGENT.md
    ├── agent-crafter/
    │   └── AGENT.md
    ├── blueprint-qa/
    │   └── AGENT.md
    └── blueprint-docs/
        └── AGENT.md
```
