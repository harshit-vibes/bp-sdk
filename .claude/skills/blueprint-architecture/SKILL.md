---
name: blueprint-architecture
description: Design multi-agent orchestration patterns for Lyzr blueprints. Use when architecting new blueprints, deciding between single vs multi-agent, or designing agent hierarchies and delegation patterns.
allowed-tools: Read, Grep, Glob
---

# Blueprint Architecture

## When to Use Single Agent vs Multi-Agent

### Single Agent (Standalone)
Use when:
- Task is focused and well-defined
- No need for specialized sub-tasks
- Simple input → output transformation
- Examples: FAQ bot, content generator, simple classifier

### Multi-Agent (Manager + Workers)
Use when:
- Task requires multiple specialized skills
- Workflow has distinct phases
- Different parts need different models (cost optimization)
- Examples: Research synthesis, ticket triage, document processing

## Decision Framework

**Question 1: Is the task complex?**
- **No** → Use Single Agent
- **Yes** → Continue to Question 2

**Question 2: Can it be decomposed into specialized sub-tasks?**
- **No** → Use Single Agent (with tools)
- **Yes** → Use Multi-Agent (Manager + Workers)

## Manager-Worker Pattern

### Manager Agent Responsibilities
- Orchestrate the overall workflow
- Delegate to appropriate workers
- Synthesize worker outputs
- Handle errors and edge cases
- Produce final response

### Worker Agent Responsibilities
- Execute specialized tasks
- Return structured results
- Handle their domain's edge cases
- Be efficient (use lighter models)

### Configuration

**Manager:**
- Model: `gpt-4o` or `claude-sonnet` (orchestration intelligence)
- Temperature: 0.3-0.5 (balanced reasoning)
- Has `managed_agents` list

**Workers:**
- Model: `gpt-4o-mini` (cost-efficient)
- Temperature: 0.2-0.3 (consistent outputs)
- Has `usage_description` (tells manager when to use)

## Orchestration Patterns

### 1. Sequential Pipeline
- **Manager** receives input
  - Delegates to **Worker A**
  - Receives result, delegates to **Worker B**
  - Synthesizes final output

Use when: Tasks must complete in order, each step depends on previous.

### 2. Parallel Fan-Out
- **Manager** receives input
  - Delegates simultaneously to:
    - **Worker A**
    - **Worker B**
    - **Worker C**
  - Combines all results into final output

Use when: Independent tasks can run simultaneously.

### 3. Conditional Routing
- **Manager** receives input
  - Evaluates condition
  - Routes to **Worker A** (if condition met) OR **Worker B** (otherwise)
  - Returns worker's output

Use when: Different paths based on input characteristics.

### 4. Iterative Refinement
- **Manager** receives input
  - Delegates to **Worker** for initial draft
  - Reviews result
  - Delegates back to **Worker** for refinement
  - Returns polished output

Use when: Quality requires multiple passes.

## Agent Specialization Strategies

### By Function
- Classifier → Assessor → Router
- Researcher → Analyzer → Synthesizer

### By Domain
- Technical Expert → Business Expert → Communication Expert

### By Output Type
- Data Extractor → Formatter → Validator

## Example Architectures

### Ticket Triage (Sequential)
```yaml
Manager: Triage Coordinator
Workers:
  - Category Classifier  (categorize ticket)
  - Priority Assessor    (assess urgency)
  - Team Router          (route to team)
```

### Research Synthesis (Parallel)
```yaml
Manager: Research Coordinator
Workers:
  - Perspective A Researcher  (parallel)
  - Perspective B Researcher  (parallel)
  - Perspective C Researcher  (parallel)
  - Synthesizer               (combine results)
```

### Document Processing (Conditional)
```yaml
Manager: Document Processor
Workers:
  - Type Detector       (identify document type)
  - Contract Analyzer   (if contract)
  - Invoice Processor   (if invoice)
  - General Extractor   (default)
```

## Best Practices

1. **Minimize Worker Count**: 2-4 workers is ideal. More adds latency.
2. **Clear Boundaries**: Each worker should have a single responsibility.
3. **Structured Outputs**: Workers should return consistent JSON/structured data.
4. **Usage Descriptions**: Write clear `usage_description` for each worker.
5. **Model Matching**: Use expensive models only where needed.
6. **Error Handling**: Manager should handle worker failures gracefully.

## Reference Files

- Example blueprint: `blueprints/local/blueprints/ticket-triage.yaml`
- Example agents: `blueprints/local/agents/*.yaml`
