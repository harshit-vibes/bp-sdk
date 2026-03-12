# YAML Schema Reference - Care Transition Coordinator

This document shows the complete YAML structure for all agents and the blueprint.

## Blueprint Definition

### File: `care-transition-coordinator.yaml`

```yaml
apiVersion: lyzr.ai/v1
kind: Blueprint

metadata:
  name: Care Transition Coordinator
  description: |
    [Blueprint description]
  category: customer                    # Business function category
  tags:
    - healthcare
    - care-transition
    - discharge
    - readmission-prevention
    - patient-safety
    - medication-safety
    - clinical-documentation
  visibility: private                   # private | organization | public
  is_template: false

root_agents:
  - agents/transition-coordinator.yaml  # Path to manager agent

ids:                                    # Filled in after creation
  blueprint: null
  agents:
    agents/transition-coordinator.yaml: null
    agents/discharge-summary-generator.yaml: null
    agents/medication-reconciler.yaml: null
    agents/followup-scheduler.yaml: null
```

**Schema Notes**:
- `apiVersion`: Always `lyzr.ai/v1`
- `kind`: Always `Blueprint`
- `metadata.category`: One of the 10 business functions (customer, healthcare, sales, etc.)
- `tags`: Searchable keywords for discovery
- `visibility`: Controls access (private = owner only, organization = org members, public = all users)
- `root_agents`: List of top-level agent files (managers)
- `ids`: Platform-provided after creation (auto-populated)

## Manager Agent Definition

### File: `agents/transition-coordinator.yaml`

```yaml
apiVersion: lyzr.ai/v1
kind: Agent

metadata:
  name: Care Transition Coordinator           # 3-5 words, descriptive
  description: |                             # 1-3 sentences
    Orchestrates the complete patient discharge process by coordinating
    three specialized agents to generate discharge summaries, reconcile
    medications, and schedule follow-ups.

spec:
  # LLM Configuration
  model: gpt-4o                              # Model for orchestration
  temperature: 0.3                           # 0.0-1.0 (0.3 for balanced)
  top_p: 1.0                                 # 0.0-1.0 (default 1.0)
  response_format: text                      # text | json_object
  store_messages: true                       # Keep conversation history
  file_output: false                         # Enable file generation

  # Persona Fields
  role: Healthcare Transition Orchestration Specialist   # 15-80 chars
  goal: |                                   # 50-300 chars
    Coordinate discharge summary generation, medication reconciliation,
    and follow-up scheduling to ensure safe, comprehensive patient
    transitions that reduce readmission risk.

  # Optional Context Fields
  context: |                                # Background information
    [Background about the domain, constraints, and context needed]

  output: |                                 # Output format spec
    [Description of expected output structure]

  examples: |                               # Few-shot examples
    [Example interactions or patterns]

  # Instructions (Required)
  instructions: |                           # Complete agent prompt
    You are the Care Transition Coordinator...

    ## Your Team
    [List of sub-agents and their roles]

    ## Workflow
    [Step-by-step process]

    ## Input Format
    [Expected input structure]

    ## Output Format
    [Required output format]

    ## Rules
    - [Constraint 1]
    - [Constraint 2]

    ## Edge Cases
    [How to handle unusual situations]

  # Features
  features:
    - memory                               # Enable conversation history

# Sub-agents (Workers)
sub_agents:
  - agents/discharge-summary-generator.yaml
  - agents/medication-reconciler.yaml
  - agents/followup-scheduler.yaml
```

**Schema Notes**:
- **Manager agents**: Have `sub_agents` list (workers they coordinate)
- **temperature**: 0.3-0.5 for managers (balanced reasoning)
- **store_messages**: Usually `true` for managers (need context)
- **features**: For managers, typically include `memory` for conversation history
- **sub_agents**: List of worker file paths (relative to agent location)

## Worker Agent Definition

### File: `agents/discharge-summary-generator.yaml`

```yaml
apiVersion: lyzr.ai/v1
kind: Agent

metadata:
  name: Discharge Summary Generator           # 3-5 words
  description: |                             # 1-3 sentences
    Synthesizes clinical information into comprehensive, patient-friendly
    discharge summaries. Includes diagnosis, treatment overview, medications,
    and follow-up instructions in clear language.

spec:
  # LLM Configuration
  model: gpt-4o                              # Complex synthesis task
  temperature: 0.3                           # Consistent documentation
  top_p: 1.0
  response_format: text
  store_messages: false                      # Workers usually stateless
  file_output: false

  # Persona Fields
  role: Clinical Documentation Specialist    # 15-80 chars
  goal: |                                   # 50-300 chars
    Generate clear, comprehensive discharge summaries that consolidate
    clinical information, improve patient understanding, and support
    continuity of care.

  # Optional Fields
  context: |                                # Domain context
    You are preparing discharge documentation that will be reviewed
    by healthcare providers and read by patients...

  output: |                                 # Output specification
    Return a structured discharge summary with provider and patient
    versions...

  # Instructions (Required)
  instructions: |                           # Complete agent prompt
    You are the Discharge Summary Generator...

    ## Process
    ### Step 1: Extract Key Information
    [Details]

    ### Step 2: Organize Content
    [Details]

    ## Input
    [Expected input format]

    ## Output
    ```
    [Required output format with sections]
    ```

    ## Rules
    - [Safety rules]
    - [Quality rules]

  # Worker-Specific Fields
  usage: |                                  # REQUIRED for workers
    Use this agent to generate comprehensive discharge summaries from
    clinical information. Pass the agent complete clinical records and
    it will produce a professional summary ready for provider review
    and patient distribution.

  # Features
  features: []                               # No special features needed

# No sub-agents
sub_agents: []
```

**Schema Notes**:
- **Worker agents**: Have `sub_agents: []` (empty list)
- **temperature**: 0.1-0.3 for classifiers, 0.2-0.3 for analyzers
- **store_messages**: Usually `false` (stateless workers)
- **usage**: REQUIRED for workers - explains when/how to use
- **features**: Empty for workers unless they need special capabilities

## Another Worker Agent Example

### File: `agents/medication-reconciler.yaml`

```yaml
apiVersion: lyzr.ai/v1
kind: Agent

metadata:
  name: Medication Reconciler
  description: |
    Compares pre-admission, in-hospital, and discharge medications to
    identify discrepancies, duplications, and dangerous interactions.
    Ensures safe medication transitions and prevents adverse events.

spec:
  model: gpt-4o
  temperature: 0.2                          # VERY low for safety
  top_p: 1.0
  response_format: text
  store_messages: false
  file_output: false

  role: Pharmacotherapy Safety Specialist
  goal: |
    Reconcile medications across care transitions to eliminate
    discrepancies, detect interactions, and ensure safe medications.

  context: |
    Medication reconciliation is critical to patient safety...

  instructions: |
    You are the Medication Reconciler...

    ## Process
    ### Step 1: Compile Medication Lists
    ### Step 2: Match and Identify Discrepancies
    ### Step 3: Screen for Drug Interactions
    ### Step 4: Verify Appropriateness
    ### Step 5: Generate Recommendations

    ## Output
    ```
    [Detailed medication reconciliation report]
    ```

  usage: |
    Use this agent to reconcile medications at discharge. Provide
    pre-admission medications, in-hospital medications, and proposed
    discharge medications. The agent identifies discrepancies and
    interactions.

  features: []

sub_agents: []
```

**Key Difference from Summary Generator**:
- Even LOWER temperature (0.2) because medication safety is critical
- Focus on drug interactions and safety
- Clear output format for easy parsing

## Third Worker Agent Example

### File: `agents/followup-scheduler.yaml`

```yaml
apiVersion: lyzr.ai/v1
kind: Agent

metadata:
  name: Follow-up Scheduler
  description: |
    Schedules appropriate follow-up appointments based on discharge
    diagnosis and clinical needs. Coordinates with care team to book
    appointments before patient leaves hospital.

spec:
  model: gpt-4o
  temperature: 0.3                          # Balanced for planning
  top_p: 1.0
  response_format: text
  store_messages: false
  file_output: false

  role: Care Continuity Scheduling Specialist
  goal: |
    Coordinate timely follow-up appointments for post-discharge care
    based on clinical diagnosis, ensuring continuity and reducing
    readmission risk.

  context: |
    Follow-up care is critical to preventing readmissions...

  instructions: |
    You are the Follow-up Scheduler...

    ## Process
    ### Step 1: Identify Clinical Needs
    ### Step 2: Determine Follow-up Urgency
    ### Step 3: Recommend Appropriate Providers
    ### Step 4: Create Scheduling Plan
    ### Step 5: Identify Barriers and Solutions

  usage: |
    Use this agent to create a comprehensive follow-up care schedule
    at discharge. Provide discharge diagnosis, patient demographics,
    and available providers. The agent creates a scheduling plan with
    barrier identification.

  features: []

sub_agents: []
```

## Field Validation Rules

### Required Fields (All Agents)
```
apiVersion: str = "lyzr.ai/v1"
kind: str = "Agent" | "Blueprint"
metadata.name: str (1-100 chars)
metadata.description: str (1+ chars)
spec.instructions: str (1+ chars)
```

### Persona Fields (Agents)
```
spec.role: str (15-80 chars) - optional but recommended for managers
spec.goal: str (50-300 chars) - optional but recommended for managers
```

### Worker-Specific
```
spec.usage: str - REQUIRED for workers, OMITTED for managers
sub_agents: list[str] - EMPTY [] for workers
```

### Manager-Specific
```
sub_agents: list[str] - POPULATED for managers
spec.usage: OMITTED (managers don't have usage description)
```

### Optional Fields
```
spec.context: str - Background information
spec.output: str - Output format specification
spec.examples: str - Few-shot examples (multiline string, NOT array)
```

### Model Configuration
```
spec.model: str = "gpt-4o" | "gpt-4o-mini" | "anthropic/claude-sonnet-4-20250514"
spec.temperature: float (0.0-1.0)
spec.top_p: float (0.0-1.0)
spec.response_format: "text" | "json_object"
spec.store_messages: bool (true for managers, false for workers)
spec.file_output: bool (false unless agent needs to generate files)
spec.features: list[str] (empty by default)
```

## Path References

### In Blueprint File
- Reference manager agents in root_agents
- Always use relative paths from blueprint file location

Example:
```yaml
# blueprint.yaml
root_agents:
  - agents/transition-coordinator.yaml  # Relative to blueprint.yaml
```

### In Manager Agent File
- Reference worker agents in sub_agents
- Always use relative paths from agent file location

Example:
```yaml
# agents/transition-coordinator.yaml
sub_agents:
  - agents/discharge-summary-generator.yaml  # Relative to this file
  - agents/medication-reconciler.yaml
  - agents/followup-scheduler.yaml
```

## Common Mistakes to Avoid

1. **Wrong temperature for worker**:
   ```yaml
   # WRONG - Too random for safety-critical task
   model: gpt-4o
   temperature: 0.7

   # CORRECT - Deterministic for medication safety
   model: gpt-4o
   temperature: 0.2
   ```

2. **Missing usage for worker**:
   ```yaml
   # WRONG - Worker without usage description
   spec:
     instructions: "..."

   # CORRECT - Worker must have usage
   spec:
     instructions: "..."
     usage: "Use this agent to..."
   ```

3. **Wrong sub_agents for worker**:
   ```yaml
   # WRONG - Worker with sub_agents
   sub_agents:
     - agents/helper.yaml

   # CORRECT - Worker must be empty
   sub_agents: []
   ```

4. **Examples as array instead of string**:
   ```yaml
   # WRONG - Examples as array
   examples:
     - "Example 1"
     - "Example 2"

   # CORRECT - Examples as multiline string
   examples: |
     Example 1
     Example 2
   ```

5. **Missing root_agents in blueprint**:
   ```yaml
   # WRONG - Blueprint with no agents
   root_agents: []

   # CORRECT - Blueprint must have at least one manager
   root_agents:
     - agents/coordinator.yaml
   ```

6. **Absolute paths instead of relative**:
   ```yaml
   # WRONG - Absolute path
   sub_agents:
     - /Users/harshitchoudhary/blueprints/agents/worker.yaml

   # CORRECT - Relative path
   sub_agents:
     - agents/worker.yaml
   ```

## File Organization

```
blueprints/local/healthcare/
├── care-transition-coordinator.yaml      # Blueprint file
├── agents/
│   ├── transition-coordinator.yaml       # Manager
│   ├── discharge-summary-generator.yaml  # Worker
│   ├── medication-reconciler.yaml        # Worker
│   └── followup-scheduler.yaml           # Worker
├── CARE_TRANSITION_README.md             # Documentation
├── BLUEPRINT_SUMMARY.md                  # Summary
└── YAML_SCHEMA_REFERENCE.md              # This file
```

## Deployment Validation

Before creating blueprint, validate YAML:

```bash
# Validate blueprint and all agents
bp validate blueprints/local/healthcare/care-transition-coordinator.yaml

# Check for common issues
bp doctor blueprints/local/healthcare/care-transition-coordinator.yaml
```

## Next Steps

After reviewing this schema reference:

1. Study actual YAML files in `agents/` directory
2. Understand how blueprint references manager agent
3. Understand how manager references workers
4. Note path resolution from each file location
5. Review persona fields (name, role, goal, description)
6. Review instruction structure (context, process, input, output, rules)
