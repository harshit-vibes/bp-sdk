# Care Transition Coordinator Blueprint - Complete Index

## Overview

This directory contains **Blueprint 10: Care Transition Coordinator**, a healthcare multi-agent orchestration system designed to reduce 30-day hospital readmissions through comprehensive discharge planning.

The blueprint uses **1 manager agent** coordinating **3 specialized worker agents** to generate discharge summaries, reconcile medications, and schedule follow-up appointments.

## Files Created

### Blueprint Definition (1 file)

**`care-transition-coordinator.yaml`**
- Root blueprint configuration
- Metadata: name, description, category, tags, visibility
- References manager agent
- Blueprint IDs section (filled after creation)

### Agent Definitions (4 files)

All agents in `agents/` subdirectory:

**Manager Agent:**
- `transition-coordinator.yaml` - Orchestrates discharge workflow

**Worker Agents (3 specialists):**
- `discharge-summary-generator.yaml` - Generates discharge summaries
- `medication-reconciler.yaml` - Identifies medication safety issues
- `followup-scheduler.yaml` - Creates follow-up care schedule

### Documentation (4 files)

**Problem/Approach/Capabilities:**
- `CARE_TRANSITION_README.md` - Comprehensive problem, approach, capabilities, and clinical impact documentation

**Technical Documentation:**
- `BLUEPRINT_SUMMARY.md` - Overview of all agents, workflow, design decisions, and deployment
- `YAML_SCHEMA_REFERENCE.md` - Complete YAML schema with examples and validation rules
- `INDEX.md` - This file

## Quick Navigation

### For Understanding the Blueprint
1. Start with **CARE_TRANSITION_README.md** for problem/approach/capabilities
2. Read **BLUEPRINT_SUMMARY.md** for architecture and workflow
3. Review **YAML_SCHEMA_REFERENCE.md** for technical details

### For Deployment
1. Review blueprint metadata in `care-transition-coordinator.yaml`
2. Review manager agent in `agents/transition-coordinator.yaml`
3. Review worker agents in `agents/`
4. Use YAML_SCHEMA_REFERENCE.md for validation

### For Integration
1. Identify integration points in CARE_TRANSITION_README.md
2. Plan data flow from EHR to agents
3. Plan implementation with discharge coordinator
4. Set up follow-up tracking

## Agent Architecture

```
BLUEPRINT: Care Transition Coordinator
└── MANAGER: Transition Coordinator (gpt-4o, temp=0.3)
    ├── WORKER: Discharge Summary Generator (gpt-4o, temp=0.3)
    ├── WORKER: Medication Reconciler (gpt-4o, temp=0.2)
    └── WORKER: Follow-up Scheduler (gpt-4o, temp=0.3)
```

## Workflow Summary

```
Patient Discharge Information
        ↓
[1. Generate Discharge Summary]
        ↓
[2. Reconcile Medications]
        ↓
[3. Schedule Follow-ups]
        ↓
Integrated Discharge Package
```

## Key Specifications

### Blueprint Metadata
- **Name**: Care Transition Coordinator
- **Category**: customer (healthcare use case)
- **Tags**: healthcare, care-transition, discharge, readmission-prevention, patient-safety, medication-safety, clinical-documentation
- **Visibility**: private (can be changed to organization/public after testing)

### Manager Agent
- **Name**: Care Transition Coordinator
- **Model**: gpt-4o (orchestration intelligence)
- **Temperature**: 0.3 (balanced reasoning)
- **Role**: Healthcare Transition Orchestration Specialist
- **Goal**: Coordinate discharge processes to reduce 30-day readmissions
- **Sub-agents**: 3 workers
- **Store Messages**: true (needs conversation history)

### Worker Agents

**Discharge Summary Generator**
- Model: gpt-4o
- Temperature: 0.3 (consistent documentation)
- Role: Clinical Documentation Specialist
- Output: Provider-reviewed and patient-friendly discharge summaries

**Medication Reconciler**
- Model: gpt-4o
- Temperature: 0.2 (deterministic for safety)
- Role: Pharmacotherapy Safety Specialist
- Output: Medication safety report with interaction detection

**Follow-up Scheduler**
- Model: gpt-4o
- Temperature: 0.3 (balanced planning)
- Role: Care Continuity Scheduling Specialist
- Output: Follow-up care schedule with barrier identification

## File Locations

All files are in:
```
/Users/harshitchoudhary/Documents/Work/Lyzr/projects/bp-sdk/blueprints/local/healthcare/
```

### Blueprint File Structure
```
care-transition-coordinator.yaml          ← Root blueprint
agents/
  ├── transition-coordinator.yaml         ← Manager
  ├── discharge-summary-generator.yaml    ← Worker 1
  ├── medication-reconciler.yaml          ← Worker 2
  └── followup-scheduler.yaml             ← Worker 3
```

### Documentation File Structure
```
CARE_TRANSITION_README.md        ← Main documentation
BLUEPRINT_SUMMARY.md             ← Technical summary
YAML_SCHEMA_REFERENCE.md         ← Schema reference
INDEX.md                         ← This file
```

## YAML Schema Summary

### Blueprint File
```yaml
apiVersion: lyzr.ai/v1
kind: Blueprint
metadata:
  name: Care Transition Coordinator
  category: customer
  tags: [healthcare, care-transition, ...]
  visibility: private
root_agents:
  - agents/transition-coordinator.yaml
ids:
  blueprint: null  # Auto-populated after creation
  agents: {}
```

### Agent Files
```yaml
apiVersion: lyzr.ai/v1
kind: Agent
metadata:
  name: [Agent Name]
  description: [1-3 sentences]
spec:
  model: gpt-4o
  temperature: 0.2-0.3
  role: [15-80 chars]
  goal: [50-300 chars]
  instructions: |
    [Complete agent prompt with structure]
  usage: |  # REQUIRED for workers
    [How to use this worker]
sub_agents:  # Empty [] for workers, populated for managers
  - agents/...
```

## Clinical Impact

### Target Outcomes
- Reduce 30-day readmissions by 20-30%
- Improve follow-up appointment compliance by 15-25%
- Prevent 10-15% of drug-related readmissions
- Increase patient understanding of discharge care

### Success Metrics
- 30-day readmission rate
- Appointment compliance rate
- Medication discrepancy detection rate
- Patient satisfaction score
- Documentation completeness score

## Implementation Checklist

### Before Deployment
- [ ] Review all YAML files for correctness
- [ ] Validate blueprint: `bp validate care-transition-coordinator.yaml`
- [ ] Test blueprint creation: `bp create care-transition-coordinator.yaml`
- [ ] Test each worker agent individually
- [ ] Test manager orchestration of all workers

### During Deployment
- [ ] Integrate with hospital EHR system
- [ ] Connect discharge coordinator workflow
- [ ] Set up follow-up appointment booking
- [ ] Create patient portal for discharge materials
- [ ] Train discharge staff on blueprint workflow

### After Deployment
- [ ] Monitor 30-day readmission rates
- [ ] Track appointment compliance
- [ ] Measure patient satisfaction
- [ ] Assess documentation quality
- [ ] Identify gaps and improvements

## Reference Documentation

See individual files for detailed information:

### CARE_TRANSITION_README.md
- Problem statement (why discharge coordination matters)
- Approach (how the three agents work together)
- Capabilities (what each agent does)
- Clinical impact evidence
- Implementation notes
- Success metrics
- Future enhancements

### BLUEPRINT_SUMMARY.md
- Files created and locations
- Blueprint metadata
- Agent specifications and capabilities
- Workflow diagram
- Design decisions and rationale
- Clinical impact summary
- Deployment considerations
- Next steps for implementation

### YAML_SCHEMA_REFERENCE.md
- Complete YAML schema for blueprints
- Complete YAML schema for agents
- Field validation rules
- Path reference conventions
- Common mistakes to avoid
- File organization example
- Deployment validation commands

## Key Concepts

### Manager-Worker Pattern
- **Manager (Coordinator)**: Orchestrates workflow, integrates results
- **Workers (Specialists)**: Perform focused tasks (summary, medication, scheduling)
- **Coordination**: Manager dispatches work, collects results, integrates them

### Safety in Healthcare
- **Deterministic Outputs**: Low temperature (0.2-0.3) for safety-critical tasks
- **Interaction Detection**: Medication reconciler identifies dangerous drug combinations
- **Multiple Review Points**: Manager integrates specialist outputs, care team reviews before discharge

### Clinical Workflow
- **Timing**: Process begins when patient cleared for discharge
- **Completion**: All tasks must complete before patient leaves hospital
- **Integration**: Results integrated into single discharge package
- **Implementation**: Discharge coordinator books appointments immediately

## Related Resources

### Clinical Evidence
- Hospital Readmission Reduction Program (HRRP)
- ACCP Medication Reconciliation Guidelines
- AHRQ Care Transitions Program
- American College of Healthcare Executives standards

### Technical Resources
- Lyzr Blueprint SDK documentation
- YAML schema validation
- Agent API specification
- Blueprint creation and deployment

## Frequently Asked Questions

**Q: Why use a manager agent instead of just calling workers directly?**
A: Manager agents ensure correct workflow sequence, integrate outputs, and perform quality assurance. They're the orchestration layer that coordinates complex multi-step processes.

**Q: Why such low temperature (0.2) for medication reconciler?**
A: Medication safety is critical. Lower temperature produces more deterministic, consistent outputs - important when identifying dangerous drug interactions.

**Q: Can I customize the agents?**
A: Yes. You can modify instructions, adjust temperature, change models, add features. The structure and workflow should remain consistent for safety.

**Q: How does this integrate with our EHR?**
A: The blueprint expects structured clinical data as input. Your EHR integration would extract patient data and pass it to the coordinator agent.

**Q: What about patient privacy?**
A: All patient data stays within your secure environment. The agents don't send data to external systems. Discharge summaries are stored according to your compliance policies.

**Q: How do I measure success?**
A: Track readmission rates (primary metric), appointment compliance (process metric), and patient satisfaction (satisfaction metric). See CARE_TRANSITION_README.md for detailed metrics.

## Support and Next Steps

### To Deploy This Blueprint
1. Read CARE_TRANSITION_README.md for clinical context
2. Review BLUEPRINT_SUMMARY.md for technical overview
3. Study YAML files in agents/ directory
4. Validate with: `bp validate care-transition-coordinator.yaml`
5. Create with: `bp create care-transition-coordinator.yaml`

### For Integration Help
- Review integration points in CARE_TRANSITION_README.md
- Contact your discharge coordinator team
- Plan data flow from EHR to agents
- Set up follow-up tracking system

### For Customization
- Modify agent instructions (agents/*.yaml)
- Adjust temperatures based on your risk tolerance
- Add custom fields or outputs
- Integrate with your specific EHR and workflows

---

**Blueprint Version**: 1.0
**Created**: 2025-01-15
**Status**: Ready for Deployment
**Location**: `/Users/harshitchoudhary/Documents/Work/Lyzr/projects/bp-sdk/blueprints/local/healthcare/`
