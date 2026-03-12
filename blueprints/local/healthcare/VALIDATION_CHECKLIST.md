# Care Transition Coordinator - Validation Checklist

This document provides a step-by-step validation checklist for the Care Transition Coordinator blueprint.

## Pre-Deployment Validation

### Step 1: File Structure Verification

- [ ] Blueprint file exists: `care-transition-coordinator.yaml`
- [ ] Manager agent exists: `agents/transition-coordinator.yaml`
- [ ] Worker 1 exists: `agents/discharge-summary-generator.yaml`
- [ ] Worker 2 exists: `agents/medication-reconciler.yaml`
- [ ] Worker 3 exists: `agents/followup-scheduler.yaml`
- [ ] All files have correct location in `blueprints/local/healthcare/`

### Step 2: YAML Format Validation

For each file, verify:

**`care-transition-coordinator.yaml`**
- [ ] `apiVersion: lyzr.ai/v1`
- [ ] `kind: Blueprint`
- [ ] `metadata.name`: Non-empty string
- [ ] `metadata.description`: Non-empty string
- [ ] `metadata.category: customer`
- [ ] `metadata.tags`: List of strings (at least 1)
- [ ] `metadata.visibility`: One of [private, organization, public]
- [ ] `root_agents`: List with one entry pointing to manager
- [ ] `ids` section present (can be null initially)
- [ ] No syntax errors (valid YAML)

**`agents/transition-coordinator.yaml`**
- [ ] `apiVersion: lyzr.ai/v1`
- [ ] `kind: Agent`
- [ ] `metadata.name`: Non-empty, 3-5 words, descriptive
- [ ] `metadata.description`: 1-3 sentences
- [ ] `spec.model`: Valid model name (gpt-4o)
- [ ] `spec.temperature`: 0.3 (in range 0.0-1.0)
- [ ] `spec.role`: 15-80 characters
- [ ] `spec.goal`: 50-300 characters
- [ ] `spec.instructions`: Non-empty, complete prompt
- [ ] `sub_agents`: List with 3 entries (worker paths)
- [ ] No `usage` field (managers don't have usage)
- [ ] No syntax errors (valid YAML)

**`agents/discharge-summary-generator.yaml`**
- [ ] `apiVersion: lyzr.ai/v1`
- [ ] `kind: Agent`
- [ ] `metadata.name`: Descriptive
- [ ] `metadata.description`: Clear explanation
- [ ] `spec.model`: gpt-4o
- [ ] `spec.temperature`: 0.3
- [ ] `spec.role`: Valid (15-80 chars)
- [ ] `spec.goal`: Valid (50-300 chars)
- [ ] `spec.instructions`: Complete with sections
- [ ] `spec.usage`: PRESENT (required for workers)
- [ ] `sub_agents: []` (empty for worker)
- [ ] No syntax errors

**`agents/medication-reconciler.yaml`**
- [ ] `apiVersion: lyzr.ai/v1`
- [ ] `kind: Agent`
- [ ] `spec.model`: gpt-4o
- [ ] `spec.temperature`: 0.2 (lower for safety)
- [ ] `spec.role`: Valid (15-80 chars)
- [ ] `spec.goal`: Valid (50-300 chars)
- [ ] `spec.instructions`: Complete with safety sections
- [ ] `spec.usage`: PRESENT (required for workers)
- [ ] `sub_agents: []` (empty for worker)

**`agents/followup-scheduler.yaml`**
- [ ] `apiVersion: lyzr.ai/v1`
- [ ] `kind: Agent`
- [ ] `spec.model`: gpt-4o
- [ ] `spec.temperature`: 0.3
- [ ] `spec.role`: Valid (15-80 chars)
- [ ] `spec.goal`: Valid (50-300 chars)
- [ ] `spec.instructions`: Complete with urgency levels
- [ ] `spec.usage`: PRESENT (required for workers)
- [ ] `sub_agents: []` (empty for worker)

### Step 3: Path Reference Validation

- [ ] Blueprint references manager: `agents/transition-coordinator.yaml`
- [ ] Manager references workers (3 relative paths):
  - [ ] `agents/discharge-summary-generator.yaml`
  - [ ] `agents/medication-reconciler.yaml`
  - [ ] `agents/followup-scheduler.yaml`
- [ ] All paths are relative (no absolute paths)
- [ ] All paths resolve from agent file location

### Step 4: Content Validation

**Manager Agent Instructions**
- [ ] Includes "Your Team" section describing workers
- [ ] Includes "Workflow" section with numbered steps
- [ ] Includes "Input" section with expected data
- [ ] Includes "Output" section with format
- [ ] Includes "Rules" section with constraints
- [ ] Includes "Edge Cases" section

**Worker Agent Instructions (all 3)**
- [ ] Clear identity statement in first paragraph
- [ ] "Context" section providing background
- [ ] "Process" section with numbered steps
- [ ] "Input" section with expected format
- [ ] "Output" section with required format
- [ ] "Rules" section with constraints
- [ ] "Edge Cases" section for unusual situations

**All Instructions**
- [ ] Uses consistent formatting
- [ ] Includes examples where helpful
- [ ] Clear and unambiguous
- [ ] Complete (not truncated)

### Step 5: Metadata Validation

**Blueprint Metadata**
- [ ] Name: "Care Transition Coordinator" (exact)
- [ ] Category: "customer" (correct)
- [ ] Tags include: healthcare, care-transition, discharge
- [ ] Visibility: private (appropriate for initial deployment)
- [ ] Description: Clear and comprehensive

**Agent Metadata**
- [ ] Manager: "Care Transition Coordinator"
- [ ] Worker 1: "Discharge Summary Generator"
- [ ] Worker 2: "Medication Reconciler"
- [ ] Worker 3: "Follow-up Scheduler"
- [ ] All names distinct and descriptive
- [ ] All descriptions 1-3 sentences

### Step 6: Model and Configuration Validation

**Manager Agent**
- [ ] Model: gpt-4o (correct for orchestration)
- [ ] Temperature: 0.3 (correct for balanced reasoning)
- [ ] store_messages: true (correct for manager)
- [ ] Features: memory (optional, recommended)

**Worker 1 (Discharge Summary)**
- [ ] Model: gpt-4o (correct for synthesis)
- [ ] Temperature: 0.3 (consistent documentation)
- [ ] store_messages: false (stateless worker)
- [ ] Features: empty list

**Worker 2 (Medication Reconciler)**
- [ ] Model: gpt-4o (correct for analysis)
- [ ] Temperature: 0.2 (VERY low for safety)
- [ ] store_messages: false (stateless)
- [ ] Features: empty list

**Worker 3 (Follow-up Scheduler)**
- [ ] Model: gpt-4o (correct for planning)
- [ ] Temperature: 0.3 (balanced)
- [ ] store_messages: false (stateless)
- [ ] Features: empty list

### Step 7: Instruction Structure Validation

Check each agent's instructions contain these sections:

**Discharge Summary Generator**
- [ ] "You are..." identity statement
- [ ] "Context" - Background about discharge documentation
- [ ] "Process" - Steps 1-4 (extract, organize, write, quality check)
- [ ] "Input" - Clinical information format
- [ ] "Output" - Structured summary with provider + patient versions
- [ ] "Rules" - Accuracy and completeness constraints
- [ ] "Usage" - When to use this worker

**Medication Reconciler**
- [ ] "You are..." identity statement
- [ ] "Context" - Background about medication safety
- [ ] "Process" - Steps 1-5 (compile, match, interactions, verify, recommend)
- [ ] "Input" - Three medication lists
- [ ] "Output" - Reconciliation report with recommendations
- [ ] "Rules" - Safety constraints
- [ ] "Usage" - When to use this worker

**Follow-up Scheduler**
- [ ] "You are..." identity statement
- [ ] "Context" - Background about follow-up care
- [ ] "Process" - Steps 1-5 (identify needs, urgency, providers, plan, barriers)
- [ ] "Input" - Discharge diagnosis and patient info
- [ ] "Output" - Scheduling plan with urgency levels
- [ ] "Rules" - Scheduling constraints
- [ ] "Usage" - When to use this worker

**Manager Coordinator**
- [ ] "You are..." identity statement
- [ ] "Your Team" - Description of 3 workers
- [ ] "Workflow" - Steps 1-7 of coordination process
- [ ] "Input" - Complete discharge package format
- [ ] "Output" - Integrated discharge package format
- [ ] "Rules" - Coordination constraints
- [ ] "Edge Cases" - Complex cases, barriers, non-English

### Step 8: Output Format Validation

All agents have clearly specified output formats:

**Discharge Summary Generator**
- [ ] Output includes sections: Patient Info, Diagnosis, Course, etc.
- [ ] Two versions: provider and patient-friendly
- [ ] Clear visual structure with headers and dividers
- [ ] Example output provided

**Medication Reconciler**
- [ ] Output includes: Matching analysis, discrepancies, interactions
- [ ] Interactions graded: CRITICAL, MAJOR, MODERATE
- [ ] Recommendations section with action items
- [ ] Summary table for easy review

**Follow-up Scheduler**
- [ ] Output includes: Urgent, routine, standard appointments
- [ ] Barrier assessment section
- [ ] Appointment summary table
- [ ] Patient education checklist

**Manager Coordinator**
- [ ] Output includes all sub-agent outputs
- [ ] Executive summary of discharge status
- [ ] Integrated package with quality assurance
- [ ] Red flags clearly highlighted

### Step 9: Safety Validation

**Medication Safety**
- [ ] Temperature is 0.2 (very low for safety)
- [ ] Instructions include interaction screening
- [ ] Output includes severity grading
- [ ] Recommendations are actionable

**Documentation Safety**
- [ ] Discharge summary instructions emphasize accuracy
- [ ] Patient version uses plain language
- [ ] Warning signs clearly highlighted

**Clinical Safety**
- [ ] Manager ensures workflow order (summary → medication → follow-up)
- [ ] Follow-up scheduling identifies urgent cases (3-7 days)
- [ ] Manager performs quality assurance review

### Step 10: Completeness Validation

- [ ] All 5 YAML agent files present and complete
- [ ] Blueprint file present and complete
- [ ] Documentation files present (README, SUMMARY, REFERENCE, CHECKLIST)
- [ ] No incomplete sections or TODO comments
- [ ] All cross-references accurate

## Deployment Readiness

### Before Running Commands

- [ ] All validation steps 1-10 passed
- [ ] No syntax errors in any YAML files
- [ ] All paths are correct and relative
- [ ] All agent references exist
- [ ] File permissions allow read/write

### Command Validation

Run these commands to validate:

```bash
# Check file existence
ls -la blueprints/local/healthcare/care-transition-coordinator.yaml
ls -la blueprints/local/healthcare/agents/transition-coordinator.yaml
ls -la blueprints/local/healthcare/agents/discharge-summary-generator.yaml
ls -la blueprints/local/healthcare/agents/medication-reconciler.yaml
ls -la blueprints/local/healthcare/agents/followup-scheduler.yaml
```

If all files exist, proceed to:

```bash
# Validate blueprint YAML
bp validate blueprints/local/healthcare/care-transition-coordinator.yaml

# Check for configuration issues
bp doctor blueprints/local/healthcare/care-transition-coordinator.yaml
```

## Test Scenarios

After deployment, test with these scenarios:

### Test 1: Basic Discharge Coordination
- Input: Simple acute care discharge
- Expected: All three workers execute successfully
- Check: Output includes all three components

### Test 2: Complex Medication List
- Input: Patient with 10+ medications, potential interactions
- Expected: Medication reconciler flags interactions
- Check: Recommendations are actionable

### Test 3: Follow-up Barriers
- Input: Patient with transportation and language barriers
- Expected: Follow-up scheduler identifies barriers
- Check: Solutions are provided

### Test 4: High-Risk Discharge
- Input: Post-surgical patient with complications
- Expected: Manager flags as urgent follow-up
- Check: Scheduling plan shows 3-7 day urgency

## Post-Deployment Verification

### Week 1
- [ ] Blueprint deployed successfully
- [ ] Manager agent accessible and responsive
- [ ] All three worker agents responding correctly
- [ ] Test discharge completed successfully

### Week 2-4
- [ ] 5+ discharges processed
- [ ] No errors or agent failures
- [ ] Integration with discharge coordinator workflow
- [ ] Patient education materials being used

### Month 2
- [ ] Continuous operation verified
- [ ] Data collection for readmission tracking
- [ ] Feedback from discharge coordinators
- [ ] Adjustment of instructions if needed

## Sign-Off

When all checks pass:

- [ ] Technical validation complete
- [ ] Deployment-ready certification
- [ ] Clinical review complete (if applicable)
- [ ] Ready for production use

**Validated By**: [Name]
**Date**: [Date]
**Status**: ✓ Ready for Deployment

---

## Troubleshooting

If validation fails, check:

1. **YAML Syntax Errors**
   - Ensure proper indentation (2 spaces)
   - Check for special characters in strings
   - Validate with YAML linter

2. **Path Resolution Issues**
   - Verify all paths are relative
   - Check path spelling exactly
   - Ensure agents/ directory exists

3. **Missing Fields**
   - Compare with YAML_SCHEMA_REFERENCE.md
   - Verify required fields present
   - Check field names exactly

4. **Temperature Out of Range**
   - Manager and workers: 0.0-1.0
   - Safety tasks: 0.2-0.3 (medication)
   - Balanced tasks: 0.3-0.5

5. **Missing usage Description**
   - All workers MUST have usage field
   - Manager MUST NOT have usage field
   - Check exact field name: spec.usage

See YAML_SCHEMA_REFERENCE.md for complete debugging guide.
