---
name: agent-persona
description: Craft compelling agent identities including name, description, role, and goal. Use when creating new agents, improving existing agent definitions, or optimizing how agents present themselves.
allowed-tools: Read, Write, Edit
---

# Agent Persona Crafting

## The Four Pillars of Agent Identity

### 1. Name
**Length:** 3-5 words
**Format:** Title Case, Descriptive

**Good Names:**
- Ticket Triage Coordinator
- Category Classifier
- Priority Assessor
- Research Synthesizer
- Contract Analyzer

**Bad Names:**
- Agent1
- Helper
- The AI Assistant That Helps With Things
- MyBot

**Pattern:** `[Domain] [Function] [Role]`
- Domain: What area (Ticket, Contract, Research)
- Function: What it does (Triage, Analyze, Synthesize)
- Role: What it is (Coordinator, Classifier, Expert)

### 2. Description
**Length:** 1-3 sentences
**Purpose:** Explains what the agent does and when to use it

**Template:**
```
[Action verb] [what it processes] by [how it does it].
[Key capability or unique value].
```

**Examples:**

```yaml
# Good
description: |
  Orchestrates the support ticket classification and routing workflow
  by coordinating specialized agents for categorization, priority
  assessment, and team assignment. Ensures consistent ticket handling
  and optimal response times.

# Bad
description: This is an AI that helps with tickets.
```

### 3. Role (agent_role)
**Length:** 15-80 characters
**Purpose:** Defines the agent's expertise and position

**Pattern:** `[Expertise Level] [Domain] [Specialist Type]`

**Examples:**
```yaml
# Good
role: Senior Support Ticket Triage Specialist
role: Expert Contract Risk Analyst
role: Lead Research Synthesis Coordinator

# Bad
role: Helper
role: AI Assistant
role: Agent
```

### 4. Goal (agent_goal)
**Length:** 50-300 characters
**Purpose:** Defines what success looks like

**Template:**
```
[Action] [target] to [outcome] while [constraint/quality measure].
```

**Examples:**
```yaml
# Good
goal: |
  Coordinate specialized agents to efficiently classify, prioritize,
  and route incoming support tickets to appropriate teams, ensuring
  fast response times and consistent handling.

goal: |
  Analyze legal contracts to identify risks, obligations, and key
  terms, providing actionable summaries for legal review.

# Bad
goal: Help users.
goal: Be useful.
```

## Persona Templates by Agent Type

### Manager Agent
```yaml
name: [Domain] [Process] Coordinator
description: |
  Orchestrates the [process name] workflow by coordinating specialized
  agents for [task 1], [task 2], and [task 3]. Ensures [key quality].
role: Lead [Domain] Orchestration Specialist
goal: |
  Coordinate [worker types] to [achieve outcome] while maintaining
  [quality standard].
```

### Worker Agent - Classifier
```yaml
name: [Domain] Classifier
description: |
  Analyzes [input type] to identify [classification dimensions].
  Provides confidence scores and key indicators for each classification.
role: Expert [Domain] Classification Specialist
goal: |
  Accurately classify [input] into [categories] with high confidence,
  identifying key indicators that support each decision.
```

### Worker Agent - Assessor
```yaml
name: [Domain] Assessor
description: |
  Evaluates [input type] to determine [assessment dimensions].
  Considers [factors] to provide actionable assessments.
role: Senior [Domain] Assessment Analyst
goal: |
  Assess [dimension] of [input] by analyzing [factors], providing
  clear recommendations with supporting rationale.
```

### Worker Agent - Router
```yaml
name: [Domain] Router
description: |
  Routes [input type] to appropriate [destinations] based on
  [routing criteria]. Ensures optimal matching and escalation handling.
role: Intelligent [Domain] Routing Specialist
goal: |
  Route [input] to the best [destination] based on [criteria],
  handling escalations and edge cases appropriately.
```

### Standalone Agent - Generator
```yaml
name: [Output Type] Generator
description: |
  Generates [output type] based on [input]. Adapts style and
  format to [context/requirements].
role: Expert [Domain] Content Specialist
goal: |
  Create high-quality [output] from [input] that meets [quality
  criteria] and adapts to [context].
```

## Quality Checklist

### Name
- [ ] 3-5 words
- [ ] Title case
- [ ] Describes function clearly
- [ ] No generic terms (Agent, Bot, Helper)

### Description
- [ ] 1-3 sentences
- [ ] Starts with action verb
- [ ] Explains what AND how
- [ ] Mentions unique value

### Role
- [ ] 15-80 characters
- [ ] Includes expertise level
- [ ] Domain-specific
- [ ] Not generic

### Goal
- [ ] 50-300 characters
- [ ] Measurable outcome
- [ ] Includes quality constraint
- [ ] Action-oriented

## Anti-Patterns

### Avoid Generic Language
```yaml
# Bad
name: Support Agent
description: Helps with support.
role: AI Assistant
goal: Be helpful.

# Good
name: Ticket Triage Coordinator
description: |
  Orchestrates support ticket classification and routing through
  specialized agents, ensuring consistent handling and fast response.
role: Senior Support Workflow Specialist
goal: |
  Coordinate ticket triage to classify, prioritize, and route
  tickets within SLA requirements.
```

### Avoid Vague Descriptions
```yaml
# Bad
description: This agent processes things and produces outputs.

# Good
description: |
  Extracts key contract clauses including payment terms, termination
  conditions, and liability provisions. Flags high-risk clauses for
  legal review.
```

### Avoid Unmeasurable Goals
```yaml
# Bad
goal: Make users happy.

# Good
goal: |
  Resolve customer inquiries within 4 hours while maintaining
  a 95% satisfaction rate.
```
