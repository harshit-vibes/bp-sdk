---
description: Create a new blueprint from YAML definition
argument-hint: [blueprint-yaml-path]
allowed-tools: Bash(bp:*), Read, Write, Edit
---

## Context

Current directory: !`pwd`

## Task

Create a new blueprint from the YAML file at path: $ARGUMENTS

### Steps

1. **Check for README**
   Read the blueprint YAML file and check if `metadata.readme` exists.
   - If README is missing, generate it first (Step 2)
   - If README exists, skip to Step 3

2. **Generate README (if missing)**
   Use the blueprint-docs agent to generate a README following the Problem-Approach-Capabilities structure:
   - Read the blueprint.yaml and all agent YAML files
   - Write the README content to `metadata.readme` field in the blueprint YAML
   - The README must include: The Problem, The Approach, Capabilities, Getting Started

3. **Validate Blueprint**
   Run `bp validate $ARGUMENTS` to check for errors before creation.
   - README is mandatory - validation will fail without it
   - Fix any errors before proceeding

4. **Create Blueprint**
   Run `bp create $ARGUMENTS` to create the blueprint in Lyzr Studio.

5. **Verify Creation**
   - Check that IDs were written back to the YAML file
   - Display the Studio URL for the created blueprint

6. **Test with Eval**
   Optionally run `bp eval <manager-id> "test query"` to verify the blueprint works.

### README Structure (Problem-Approach-Capabilities)

```markdown
## The Problem
### The Situation
### The Challenge
### What's At Stake

---

## The Approach
### The Key Insight
### The Method
### Why This Works

---

## Capabilities
### Core Capabilities
### Extended Capabilities
### Boundaries

---

## Getting Started
### Prerequisites
### Your First Run
### Pro Tips
```

### Error Handling

- If README is missing, generate it using blueprint-docs agent before validation
- If validation fails, explain the errors and suggest fixes
- If creation fails, check API credentials (LYZR_API_KEY, BLUEPRINT_BEARER_TOKEN, LYZR_ORG_ID)
- If IDs not written, check file permissions

### Output

Report:
- Blueprint ID
- Manager Agent ID
- Worker Agent IDs
- Studio URL
- README generation status (generated or already existed)
- Any warnings or issues
