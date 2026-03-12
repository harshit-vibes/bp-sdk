---
description: Test an agent with a query and display response + trace
argument-hint: [agent-id] [query]
allowed-tools: Bash(bp:*)
---

## Task

Evaluate agent with ID: $1
Query: $2

### Execution

Run the evaluation:
```bash
bp eval "$1" "$2"
```

### Analysis

After getting the response and trace:

1. **Response Quality**
   - Is the response accurate and complete?
   - Does it follow the expected format?
   - Are there any errors or unexpected outputs?

2. **Delegation Pattern**
   - Did the manager delegate to the right workers?
   - Was the delegation order correct?
   - Were all expected workers called?

3. **Performance**
   - Total latency acceptable?
   - Token usage reasonable?
   - Any inefficiencies?

4. **Issues Found**
   - List any problems observed
   - Suggest fixes for each issue

### JSON Output (Alternative)

For programmatic analysis:
```bash
bp eval "$1" "$2" --json > eval_result.json
```
