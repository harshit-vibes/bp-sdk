---
description: Diagnose issues with a blueprint configuration
argument-hint: [blueprint-yaml-path | blueprint-id]
allowed-tools: Bash(bp:*), Read, Grep
---

## Task

Diagnose blueprint: $ARGUMENTS

### Diagnostic Steps

1. **Validate YAML Syntax**
   ```bash
   bp validate $ARGUMENTS
   ```

2. **Check File References**
   - Verify all referenced agent files exist
   - Check relative paths are correct

3. **Validate Agent Configurations**
   For each agent file:
   - Name: 1-100 characters
   - Description: Required
   - Role: 15-80 characters (if provided)
   - Goal: 50-300 characters (if provided)
   - Instructions: Required
   - Usage: Required for workers

4. **Check for Common Issues**
   - Placeholder text like `[PLACEHOLDER]`
   - Generic role terms (worker, helper, bot, agent, assistant)
   - Missing usage_description for workers
   - Circular dependencies

5. **Test Agent Connectivity**
   If blueprint exists (has IDs):
   ```bash
   bp eval <manager-id> "Hello, are you working?"
   ```

### Report Format

```
## Blueprint Diagnosis Report

### File Validation
- [PASS/FAIL] Blueprint YAML syntax
- [PASS/FAIL] Agent file references
- [PASS/FAIL] Agent YAML syntax

### Configuration Validation
- [PASS/FAIL] Metadata complete
- [PASS/FAIL] Agent personas valid
- [PASS/FAIL] Instructions complete
- [PASS/FAIL] Worker usage descriptions

### Issues Found
1. [Issue description] - [Severity: HIGH/MEDIUM/LOW]
   Fix: [How to fix]

2. [Issue description] - [Severity]
   Fix: [How to fix]

### Recommendations
- [Suggestion 1]
- [Suggestion 2]
```

### Common Fixes

**Placeholder text:**
Change `[CATEGORY]` to actual values like `BILLING, TECHNICAL, ACCOUNT`

**Generic role:**
Change `AI Assistant` to `Senior Support Triage Specialist`

**Missing worker usage:**
Add `usage: Use this agent when you need to...` to worker spec
