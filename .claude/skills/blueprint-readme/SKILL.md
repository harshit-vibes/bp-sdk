---
name: blueprint-readme
description: Write beautiful, comprehensive blueprint documentation following the Problem-Approach-Capabilities structure. Use when documenting new blueprints, improving existing docs, or creating user-facing documentation.
allowed-tools: Read, Write, Edit
---

# Blueprint README Writing

## Structure

Every blueprint README should follow this structure:

```markdown
## The Problem

### The Situation
[What exists today, the current state]

### The Challenge
[Why current solutions fall short]

### What's At Stake
[Consequences of not solving this]

---

## The Approach

### The Key Insight
[The "aha" that makes this solution work]

### The Method
[How the solution works, agent roles]

### Why This Works
[What makes this approach effective]

---

## Capabilities

### Core Capabilities
- [Main thing it does #1]
- [Main thing it does #2]
- [Main thing it does #3]
- [Main thing it does #4]

### Extended Capabilities
- [Additional capability #1]
- [Additional capability #2]
- [Additional capability #3]

### Boundaries
- [What it doesn't do #1]
- [What it doesn't do #2]
- [What it doesn't do #3]

---

## Getting Started

### Prerequisites
- [Requirement #1]
- [Requirement #2]

### Your First Run
[Example input to try]

### Pro Tips
- [Tip #1]
- [Tip #2]
- [Tip #3]
```

## Section Details

### The Problem

#### The Situation
Describe the current state without the solution. Focus on:
- What teams/users currently do
- Tools they use today
- Volume/scale of the problem

**Example:**
```markdown
### The Situation
Support teams receive hundreds of tickets daily across multiple channels.
Each ticket needs to be read, understood, categorized, prioritized, and
assigned to the right team. This manual process is time-consuming,
inconsistent, and error-prone.
```

#### The Challenge
Explain why existing approaches fail. Focus on:
- Expertise required
- Consistency issues
- Resource constraints

**Example:**
```markdown
### The Challenge
Effective ticket triage requires expertise in understanding customer issues,
knowledge of support team capabilities, and consistent application of priority
criteria. Human agents have varying levels of expertise and may prioritize
differently, leading to inconsistent customer experiences.
```

#### What's At Stake
Describe consequences of not solving the problem. Focus on:
- Business impact
- Customer impact
- Operational impact

**Example:**
```markdown
### What's At Stake
Misrouted tickets cause delays and frustration. Critical issues may languish
in the wrong queue while urgent customers wait. Support costs increase as
agents spend time on triage instead of resolution. Customer satisfaction
drops when response times are unpredictable.
```

### The Approach

#### The Key Insight
The conceptual breakthrough. One paragraph explaining why this approach works.

**Example:**
```markdown
### The Key Insight
Ticket triage follows a predictable workflow: categorize the issue, assess
urgency, then route to the right team. Each step benefits from specialization.
Category classification requires understanding product domains. Priority
assessment requires evaluating business impact. Routing requires knowledge
of team capabilities.
```

#### The Method
How the solution works. Describe:
- The agents and their roles
- The workflow/sequence
- How they collaborate

**Example:**
```markdown
### The Method
A Triage Coordinator orchestrates three specialized workers. The Category
Classifier analyzes ticket content to identify the primary issue type. The
Priority Assessor evaluates urgency based on impact and severity indicators.
The Team Router matches the classified, prioritized ticket to the best-suited
support team.
```

#### Why This Works
Why this approach succeeds. Focus on:
- Consistency benefits
- Specialization benefits
- Scale benefits

**Example:**
```markdown
### Why This Works
Specialized agents apply consistent criteria every time. The Category
Classifier learns domain-specific terminology. The Priority Assessor
maintains uniform SLA standards. The Team Router knows each team's expertise.
The coordinator ensures clean handoffs. The result is fast, consistent,
accurate ticket triage at scale.
```

### Capabilities

#### Core Capabilities
4-6 main things the blueprint does. Use bullet points with specifics.

**Example:**
```markdown
### Core Capabilities
- Classifies tickets into 5 categories: Billing, Technical, Account, Feature, General
- Assigns priority levels P1-P4 with corresponding SLAs (1hr to 72hr)
- Routes to 6 specialized teams based on category and priority
- Provides confidence scores and reasoning for all decisions
```

#### Extended Capabilities
Additional features beyond the core. 3-4 items.

**Example:**
```markdown
### Extended Capabilities
- Handles incomplete tickets with appropriate flags
- Identifies escalation requirements for critical issues
- Provides ticket summaries for quick agent review
- Maintains consistent formatting for downstream systems
```

#### Boundaries
What the blueprint explicitly doesn't do. Important for managing expectations.

**Example:**
```markdown
### Boundaries
- Classification based on ticket content only (no historical context)
- Routing to predefined team structure (customize for your organization)
- Priority assessment based on content indicators (no customer tier data)
- English language tickets only (extend for multilingual support)
```

### Getting Started

#### Prerequisites
What users need before starting.

**Example:**
```markdown
### Prerequisites
- Support ticket with subject and description
- Optional: Customer identifier for tracking
```

#### Your First Run
A concrete example to try immediately.

**Example:**
```markdown
### Your First Run
Send a ticket: 'Subject: Cannot login to my account. Description: I keep
getting an error message when trying to sign in. I have tried resetting
my password but still cannot access my dashboard. This is urgent as I
need to process orders today.'
```

#### Pro Tips
3-4 tips for getting the best results.

**Example:**
```markdown
### Pro Tips
- Include specific error messages for better technical classification
- Mention business impact for accurate priority assessment
- Keep subject lines descriptive for faster categorization
- Customize team definitions to match your organization structure
```

## Writing Guidelines

### Tone
- Professional but approachable
- Confident but not arrogant
- Specific, not vague

### Length
- The Problem: 150-250 words
- The Approach: 150-200 words
- Capabilities: 100-150 words
- Getting Started: 50-100 words

### Formatting
- Use `---` separators between major sections
- Use `###` for subsections
- Use bullet points for lists
- Use code blocks for examples

## Complete Example

```markdown
## The Problem

### The Situation
Support teams receive hundreds of tickets daily across multiple channels.
Each ticket needs to be read, understood, categorized, prioritized, and
assigned to the right team. This manual process is time-consuming,
inconsistent, and error-prone.

### The Challenge
Effective ticket triage requires expertise in understanding customer issues,
knowledge of support team capabilities, and consistent application of priority
criteria. Human agents have varying levels of expertise and may prioritize
differently, leading to inconsistent customer experiences.

### What's At Stake
Misrouted tickets cause delays and frustration. Critical issues may languish
in the wrong queue while urgent customers wait. Support costs increase as
agents spend time on triage instead of resolution. Customer satisfaction
drops when response times are unpredictable.

---

## The Approach

### The Key Insight
Ticket triage follows a predictable workflow: categorize the issue, assess
urgency, then route to the right team. Each step benefits from specialization.
Category classification requires understanding product domains. Priority
assessment requires evaluating business impact. Routing requires knowledge
of team capabilities.

### The Method
A Triage Coordinator orchestrates three specialized workers. The Category
Classifier analyzes ticket content to identify the primary issue type. The
Priority Assessor evaluates urgency based on impact and severity indicators.
The Team Router matches the classified, prioritized ticket to the best-suited
support team.

### Why This Works
Specialized agents apply consistent criteria every time. The Category
Classifier learns domain-specific terminology. The Priority Assessor
maintains uniform SLA standards. The Team Router knows each team's expertise.
The coordinator ensures clean handoffs. The result is fast, consistent,
accurate ticket triage at scale.

---

## Capabilities

### Core Capabilities
- Classifies tickets into 5 categories: Billing, Technical, Account, Feature, General
- Assigns priority levels P1-P4 with corresponding SLAs (1hr to 72hr)
- Routes to 6 specialized teams based on category and priority
- Provides confidence scores and reasoning for all decisions

### Extended Capabilities
- Handles incomplete tickets with appropriate flags
- Identifies escalation requirements for critical issues
- Provides ticket summaries for quick agent review
- Maintains consistent formatting for downstream systems

### Boundaries
- Classification based on ticket content only (no historical context)
- Routing to predefined team structure (customize for your organization)
- Priority assessment based on content indicators (no customer tier data)
- English language tickets only (extend for multilingual support)

---

## Getting Started

### Prerequisites
- Support ticket with subject and description
- Optional: Customer identifier for tracking

### Your First Run
Send a ticket: 'Subject: Cannot login to my account. Description: I keep
getting an error message when trying to sign in. I have tried resetting
my password but still cannot access my dashboard. This is urgent as I
need to process orders today.'

### Pro Tips
- Include specific error messages for better technical classification
- Mention business impact for accurate priority assessment
- Keep subject lines descriptive for faster categorization
- Customize team definitions to match your organization structure
```

## Anti-Patterns

### Vague Problem Statement
```markdown
# Bad
### The Situation
Things are difficult and could be better.

# Good
### The Situation
Support teams receive hundreds of tickets daily across multiple channels.
Each ticket needs to be read, understood, categorized, prioritized, and
assigned to the right team.
```

### Missing Boundaries
```markdown
# Bad
(No boundaries section - users don't know limitations)

# Good
### Boundaries
- English language tickets only
- No integration with external ticketing systems
- Classification based on content, not customer history
```

### Generic Getting Started
```markdown
# Bad
### Your First Run
Send a message and see what happens.

# Good
### Your First Run
Send a ticket: 'Subject: Payment failed. Description: My credit card
was charged but the order shows as failed. Order ID: 12345.'
```
