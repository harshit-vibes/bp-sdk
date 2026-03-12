---
name: agent-instructions
description: Write clear, effective agent instructions and prompts. Use when creating new agents, improving existing prompts, or debugging agent behavior issues. Covers step-by-step processes, edge cases, output formats, and constraints.
allowed-tools: Read, Write, Edit
---

# Agent Instruction Engineering

## Instruction Structure

Every agent instruction should have these components:

```yaml
instructions: |
  # Identity Statement
  You are [role]. [Key responsibility].

  ## Context
  [Background information the agent needs]

  ## Process
  [Step-by-step workflow]

  ## Input Format
  [Expected input structure]

  ## Output Format
  [Required output structure]

  ## Rules & Constraints
  [Hard constraints and guardrails]

  ## Edge Cases
  [How to handle unusual situations]
```

## Component Details

### 1. Identity Statement
First 1-2 sentences establishing who the agent is.

```yaml
# Good
You are the Support Ticket Triage Coordinator. You manage a team
of specialists to process incoming support tickets efficiently.

# Bad
You are an AI assistant. You help with things.
```

### 2. Context Section
Background information needed to perform the task.

```yaml
## Context
You operate within a support organization with these teams:
- Billing Team: Payment issues, refunds, invoices
- Technical Team: Product bugs, integrations, APIs
- Account Team: Access, permissions, account management

Tickets arrive via email, chat, and phone. Average volume: 500/day.
SLA requirements: P1 = 1hr, P2 = 4hr, P3 = 24hr, P4 = 72hr.
```

### 3. Process Section
Step-by-step workflow with clear actions.

```yaml
## Process

### Step 1: Analyze Input
Read the ticket subject and description carefully.
Identify key terms and customer sentiment.

### Step 2: Classify Category
Match against the 5 categories:
- BILLING: payment, invoice, charge, refund, subscription
- TECHNICAL: error, bug, crash, integration, API
- ACCOUNT: login, access, permission, password, settings
- FEATURE: request, suggestion, enhancement, new
- GENERAL: other inquiries

### Step 3: Assess Priority
Consider these factors:
- Business impact (revenue, users affected)
- Urgency keywords (urgent, ASAP, critical, down)
- Customer tier (enterprise, pro, free)

### Step 4: Generate Output
Format the result according to the output specification.
```

### 4. Input Format
Define what the agent expects to receive.

```yaml
## Input Format
Expect tickets in this format:
```
Subject: [ticket subject line]
Description: [full ticket description]
Customer: [customer name or ID] (optional)
Attachment: [attachment info] (optional)
```

If format differs, adapt and process anyway.
```

### 5. Output Format
Define the exact structure of outputs.

```yaml
## Output Format
Return results in this exact format:

```
=== TRIAGE RESULT ===

CLASSIFICATION
- Category: [BILLING|TECHNICAL|ACCOUNT|FEATURE|GENERAL]
- Confidence: [HIGH|MEDIUM|LOW]
- Key Indicators: [comma-separated terms]

PRIORITY
- Level: [P1|P2|P3|P4]
- Response SLA: [1|4|24|72] hours
- Escalation: [Yes|No]

ROUTING
- Team: [team-name]
- Notes: [any special handling]
===
```
```

### 6. Rules & Constraints
Hard boundaries the agent must follow.

```yaml
## Rules
- NEVER modify customer data
- NEVER share internal system information
- ALWAYS include confidence scores
- ALWAYS cite key indicators
- If unsure, default to GENERAL category and P3 priority
- Maximum response length: 500 words
```

### 7. Edge Cases
Handle unusual situations explicitly.

```yaml
## Edge Cases

### Incomplete Tickets
If subject or description is missing:
- Process with available information
- Flag as "INCOMPLETE_DATA" in notes
- Assign MEDIUM confidence

### Multiple Issues
If ticket contains multiple issues:
- Focus on the primary/most urgent issue
- Note secondary issues in routing notes
- Recommend ticket splitting

### Non-English Tickets
If ticket is not in English:
- Process to best ability
- Note language in routing
- Route to multilingual team if available
```

## Manager vs Worker Instructions

### Manager Agent Instructions

Managers coordinate other agents. Their instructions should:
- List and describe their team
- Define the workflow order
- Specify what to pass between agents
- Handle synthesis of results

```yaml
instructions: |
  You are the Research Coordinator managing 3 research specialists.

  ## Your Team
  1. **Query Generator** - Creates search queries from topics
  2. **Research Analyst** - Gathers and analyzes information
  3. **Synthesis Writer** - Combines findings into reports

  ## Workflow
  For each research request:

  ### Step 1: Query Generator
  Send the topic. Receive search queries.

  ### Step 2: Research Analyst
  Send the queries. Receive raw findings.

  ### Step 3: Synthesis Writer
  Send all findings. Receive final report.

  ## Rules
  - Call each specialist ONCE in order
  - Pass complete outputs between steps
  - Do NOT do specialists' work yourself
  - Do NOT skip any specialist
```

### Worker Agent Instructions

Workers perform specific tasks. Their instructions should:
- Focus on one capability
- Be detailed about the specific task
- Define clear input/output contracts
- Handle their domain's edge cases

```yaml
instructions: |
  You are the Category Classifier. Your ONLY job is to categorize
  support tickets into one of 5 categories.

  ## Categories

  ### BILLING
  Payment, invoices, charges, refunds, subscriptions, pricing
  Keywords: payment, invoice, charge, refund, subscription, bill, price

  ### TECHNICAL
  Product issues, bugs, errors, integrations, API problems
  Keywords: error, bug, crash, not working, integration, API, broken

  ### ACCOUNT
  Access, permissions, login, password, settings, profile
  Keywords: login, password, access, permission, settings, account

  ### FEATURE
  Feature requests, suggestions, enhancements
  Keywords: request, wish, would like, suggestion, please add

  ### GENERAL
  Everything else that doesn't fit above categories
  Keywords: question, inquiry, information, help, other

  ## Input
  A support ticket with subject and description.

  ## Output
  Return ONLY this format:
  ```
  Category: [CATEGORY_NAME]
  Confidence: [HIGH|MEDIUM|LOW]
  Key Indicators: [term1, term2, term3]
  ```

  ## Rules
  - Pick exactly ONE category
  - HIGH confidence: 3+ matching keywords
  - MEDIUM confidence: 1-2 matching keywords
  - LOW confidence: no direct matches, best guess
```

## Quality Checklist

### Completeness
- [ ] Identity statement present
- [ ] Context provided
- [ ] Process defined step-by-step
- [ ] Input format specified
- [ ] Output format specified
- [ ] Rules and constraints listed
- [ ] Edge cases handled

### Clarity
- [ ] No ambiguous terms
- [ ] Specific examples provided
- [ ] Numbers and thresholds explicit
- [ ] Actions are verbs (not "consider" but "classify")

### Testability
- [ ] Output is deterministic for same input
- [ ] Can verify correctness against spec
- [ ] Edge cases produce defined behavior

## Anti-Patterns

### Vague Instructions
```yaml
# Bad
instructions: |
  Help with support tickets. Be helpful and accurate.

# Good
instructions: |
  You are the Ticket Classifier. Categorize each ticket into exactly
  one of 5 categories: BILLING, TECHNICAL, ACCOUNT, FEATURE, GENERAL.
  Return the category, confidence level, and key indicators.
```

### Missing Output Format
```yaml
# Bad
instructions: |
  Analyze the data and return insights.

# Good
instructions: |
  Analyze the data and return:
  ```
  Summary: [one sentence]
  Key Metrics:
  - [metric1]: [value]
  - [metric2]: [value]
  Recommendations:
  1. [action1]
  2. [action2]
  ```
```

### Unbounded Tasks
```yaml
# Bad
instructions: |
  Research everything about the topic.

# Good
instructions: |
  Research the topic with these constraints:
  - Maximum 5 sources
  - Focus on last 2 years
  - Prioritize peer-reviewed sources
  - Output max 500 words
```

## Template for New Agents

```yaml
instructions: |
  You are [Agent Name]. [One sentence role description].

  ## Context
  [Background information needed for the task]

  ## Your Task
  [Clear description of what to accomplish]

  ## Process
  ### Step 1: [Action]
  [Details]

  ### Step 2: [Action]
  [Details]

  ### Step 3: [Action]
  [Details]

  ## Input
  [Expected input format]

  ## Output
  [Required output format with example]

  ## Rules
  - [Constraint 1]
  - [Constraint 2]
  - [Constraint 3]

  ## Edge Cases
  ### [Case 1]
  [How to handle]

  ### [Case 2]
  [How to handle]
```
