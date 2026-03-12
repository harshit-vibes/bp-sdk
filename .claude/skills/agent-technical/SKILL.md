---
name: agent-technical
description: Configure technical parameters for agents including model selection, temperature, top_p, response format, and features. Use when optimizing agent performance, managing costs, or debugging output quality issues.
allowed-tools: Read, Write, Edit
---

# Agent Technical Configuration

## Model Selection

### Available Models

| Provider | Model | Best For | Cost | Speed |
|----------|-------|----------|------|-------|
| **OpenAI** | `gpt-4o` | Complex reasoning, orchestration | High | Medium |
| **OpenAI** | `gpt-4o-mini` | Simple tasks, workers | Low | Fast |
| **Anthropic** | `anthropic/claude-sonnet-4-20250514` | Balanced tasks | Medium | Medium |
| **Anthropic** | `anthropic/claude-opus-4-20250514` | Complex analysis | High | Slow |
| **Perplexity** | `perplexity/sonar-pro` | Real-time search | Medium | Fast |
| **Perplexity** | `perplexity/sonar-reasoning-pro` | Search + reasoning | High | Medium |

### Model Selection Guide

```
┌─────────────────────────────────────────────────────┐
│                  Is this a manager agent?           │
├─────────────────┬───────────────────────────────────┤
│       Yes       │              No                   │
│                 │                                   │
│    gpt-4o       │    Is the task simple?            │
│    claude-sonnet│         │                         │
│                 │    ┌────┴────┐                    │
│                 │   Yes       No                    │
│                 │    │         │                    │
│                 │ gpt-4o-mini  │                    │
│                 │              │                    │
│                 │    Does it need web search?       │
│                 │         │                         │
│                 │    ┌────┴────┐                    │
│                 │   Yes       No                    │
│                 │    │         │                    │
│                 │ perplexity/  │                    │
│                 │ sonar-pro    │                    │
│                 │          gpt-4o-mini              │
└─────────────────┴───────────────────────────────────┘
```

### By Agent Type

| Agent Type | Recommended Model | Temperature |
|------------|-------------------|-------------|
| **Manager/Coordinator** | `gpt-4o`, `claude-sonnet` | 0.3-0.5 |
| **Classifier** | `gpt-4o-mini` | 0.1-0.2 |
| **Assessor/Analyzer** | `gpt-4o-mini` | 0.2-0.3 |
| **Router** | `gpt-4o-mini` | 0.1-0.2 |
| **Generator/Writer** | `gpt-4o`, `claude-sonnet` | 0.5-0.7 |
| **Researcher** | `perplexity/sonar-pro` | 0.3-0.5 |

## Temperature

Temperature controls randomness/creativity.

### Values

| Temperature | Behavior | Use Case |
|-------------|----------|----------|
| `0.0 - 0.2` | Deterministic, consistent | Classification, extraction |
| `0.3 - 0.5` | Balanced | Analysis, routing, orchestration |
| `0.6 - 0.8` | Creative, varied | Content generation, brainstorming |
| `0.9 - 1.0` | Highly random | Creative writing, exploration |

### By Task

```yaml
# Classification
temperature: 0.2

# Analysis
temperature: 0.3

# Orchestration
temperature: 0.3

# Content generation
temperature: 0.6

# Creative writing
temperature: 0.8
```

## Top-P (Nucleus Sampling)

Controls diversity by limiting token selection to top probability mass.

| top_p | Effect | Use Case |
|-------|--------|----------|
| `1.0` | Consider all tokens (default) | Most tasks |
| `0.9` | Slightly more focused | Balanced output |
| `0.5` | Much more focused | Very deterministic |

**Recommendation:** Keep `top_p: 1.0` and adjust temperature instead.

## Response Format

### Text (Default)
```yaml
response_format: text
```
For: Natural language responses, explanations, summaries.

### JSON Object
```yaml
response_format: json_object
```
For: Structured data extraction, API responses.

**Note:** When using `json_object`, your instructions MUST specify the JSON schema.

```yaml
instructions: |
  Extract the following information and return as JSON:
  {
    "category": "string",
    "confidence": "HIGH|MEDIUM|LOW",
    "indicators": ["string"]
  }
```

## Features

Enable additional capabilities:

```yaml
features:
  - memory          # Conversation history (2-50 messages)
  - voice           # Voice synthesis for voice agents
  - context         # Global context attachment
  - file_output     # Generate files (docx, pdf, csv, ppt)
  - image_output    # Generate images
  - reflection      # Self-critique for accuracy
  - groundedness    # Fact verification against context
  - fairness        # Bias detection
  - rai             # Responsible AI (toxicity, PII, injection)
  - llm_judge       # Response quality assessment
```

### Feature Recommendations

| Agent Type | Recommended Features |
|------------|---------------------|
| **Manager** | `memory` |
| **Research** | `groundedness` |
| **Customer-facing** | `rai`, `fairness` |
| **Content Generator** | `reflection` |
| **Voice Agent** | `voice`, `memory` |

## Other Settings

### store_messages
```yaml
store_messages: true  # Keep conversation history (default)
store_messages: false # Stateless (each call independent)
```

Use `false` for workers that don't need context between calls.

### file_output
```yaml
file_output: true   # Enable file generation
file_output: false  # Disable (default)
```

Enable when agent needs to produce downloadable documents.

## Configuration Examples

### Manager Agent
```yaml
spec:
  model: gpt-4o
  temperature: 0.3
  top_p: 1.0
  response_format: text
  store_messages: true
  features:
    - memory
```

### Worker Classifier
```yaml
spec:
  model: gpt-4o-mini
  temperature: 0.2
  top_p: 1.0
  response_format: text
  store_messages: false
  features: []
```

### Research Agent
```yaml
spec:
  model: perplexity/sonar-pro
  temperature: 0.4
  top_p: 1.0
  response_format: text
  store_messages: true
  features:
    - groundedness
```

### Content Generator
```yaml
spec:
  model: gpt-4o
  temperature: 0.6
  top_p: 1.0
  response_format: text
  store_messages: true
  features:
    - reflection
    - file_output
```

### Customer Support Agent
```yaml
spec:
  model: gpt-4o
  temperature: 0.3
  top_p: 1.0
  response_format: text
  store_messages: true
  features:
    - memory
    - rai
    - fairness
```

## Cost Optimization

### Token Costs (Relative)
| Model | Input Cost | Output Cost |
|-------|------------|-------------|
| gpt-4o | $$$ | $$$ |
| gpt-4o-mini | $ | $ |
| claude-sonnet | $$ | $$ |
| claude-opus | $$$$ | $$$$ |
| perplexity/sonar | $$ | $$ |

### Optimization Strategies

1. **Use cheaper models for workers**
   ```yaml
   # Manager: expensive model for orchestration
   model: gpt-4o

   # Workers: cheap model for simple tasks
   model: gpt-4o-mini
   ```

2. **Minimize stored messages**
   ```yaml
   # Workers don't need history
   store_messages: false
   ```

3. **Batch similar tasks**
   Process multiple items per call when possible.

4. **Limit output length**
   Add constraints in instructions.

## Debugging

### Output Too Random
- Lower temperature: `0.3 → 0.1`
- Lower top_p: `1.0 → 0.9`
- Add explicit constraints in instructions

### Output Too Repetitive
- Raise temperature: `0.3 → 0.5`
- Review instructions for over-specificity

### Agent Not Following Instructions
- Use more capable model: `gpt-4o-mini → gpt-4o`
- Simplify instructions
- Add examples

### JSON Output Invalid
- Ensure `response_format: json_object`
- Include JSON schema in instructions
- Add validation in output format section

### High Costs
- Switch workers to `gpt-4o-mini`
- Disable unused features
- Set `store_messages: false` for workers
