# Insurance Eligibility Verifier - Blueprint Manifest

## Overview
This blueprint creates a multi-agent healthcare solution for insurance eligibility verification, benefits analysis, and patient cost calculation. It reduces staff time on eligibility calls from 2-4 hours to 10-15 minutes.

**Category:** customer
**Tags:** healthcare, insurance, eligibility, benefits, verification, patient-costs
**Complexity:** Multi-agent (1 Manager + 3 Workers)
**Use Case:** Insurance coverage verification, benefits analysis, patient financial counseling

## File Structure

```
blueprints/local/healthcare/
├── insurance-eligibility-verifier.yaml          [Blueprint definition]
├── insurance-eligibility-README.md              [Documentation]
├── BLUEPRINT_MANIFEST.md                        [This file]
└── agents/
    ├── eligibility-coordinator.yaml             [Manager agent]
    ├── coverage-checker.yaml                    [Worker 1]
    ├── benefits-analyzer.yaml                   [Worker 2]
    └── patient-responsibility-calculator.yaml   [Worker 3]
```

## Files Created

### 1. Blueprint Definition
**File:** `insurance-eligibility-verifier.yaml`
**Type:** Blueprint configuration
**Lines:** 26

Defines the blueprint structure with:
- Metadata (name, description, category, tags)
- Manager reference: `agents/eligibility-coordinator.yaml`
- Workers references: coverage-checker, benefits-analyzer, patient-responsibility-calculator

**Key Details:**
- Category: `customer`
- Tags: healthcare, insurance, eligibility, benefits, verification, patient-costs

### 2. Manager Agent
**File:** `agents/eligibility-coordinator.yaml`
**Type:** Agent definition
**Lines:** 221

Orchestrates the three-worker eligibility verification workflow.

**Key Details:**
- Name: `Eligibility Coordinator`
- Role: Senior Insurance Eligibility Orchestration Specialist
- Model: `gpt-4o` (needs orchestration intelligence)
- Temperature: `0.3` (consistent decision-making)
- Handles: workflow coordination, result synthesis, edge cases

**Capabilities:**
- Coordinates coverage verification, benefits analysis, cost calculation
- Synthesizes results into comprehensive eligibility summary
- Handles edge cases: terminated coverage, multiple insurance, pre-auth, no coverage
- Manages team of 3 specialized workers

### 3. Worker 1: Coverage Checker
**File:** `agents/coverage-checker.yaml`
**Type:** Agent definition
**Lines:** 299

Verifies insurance coverage and extracts plan details.

**Key Details:**
- Name: `Coverage Checker`
- Role: Expert Insurance Coverage Verification Specialist
- Model: `gpt-4o-mini` (cost-efficient classification)
- Temperature: `0.2` (deterministic verification)
- Usage Description: Required for worker agents

**Capabilities:**
- Verify member eligibility status
- Extract deductible and out-of-pocket information
- Confirm effective coverage dates
- Support PPO, HMO, POS, Medicare, Medicaid plans
- Handle terminated and pending coverage
- Assign confidence levels (HIGH/MEDIUM/LOW)

**Output Format:**
- Member eligibility status
- Plan information
- Deductible details
- Out-of-pocket information
- Verification notes

### 4. Worker 2: Benefits Analyzer
**File:** `agents/benefits-analyzer.yaml`
**Type:** Agent definition
**Lines:** 306

Analyzes insurance benefits for specific medical services.

**Key Details:**
- Name: `Benefits Analyzer`
- Role: Expert Insurance Benefits Analysis Specialist
- Model: `gpt-4o-mini` (cost-efficient analysis)
- Temperature: `0.2` (deterministic benefit extraction)
- Usage Description: Required for worker agents

**Capabilities:**
- Identify covered vs non-covered services
- Extract service-level copay and coinsurance
- Flag pre-authorization requirements
- Identify frequency limitations and exclusions
- Support 9 service categories (preventive, surgical, etc.)
- Handle unlisted, conditional, and out-of-network services

**Output Format:**
- Service coverage status
- Benefit terms (copay/coinsurance)
- Pre-authorization requirements
- Benefit limitations
- Coverage notes

### 5. Worker 3: Patient Responsibility Calculator
**File:** `agents/patient-responsibility-calculator.yaml`
**Type:** Agent definition
**Lines:** 348

Calculates patient out-of-pocket costs with accurate financial responsibility.

**Key Details:**
- Name: `Patient Responsibility Calculator`
- Role: Healthcare Financial Calculation Specialist
- Model: `gpt-4o-mini` (cost-efficient calculation)
- Temperature: `0.2` (deterministic calculations)
- Usage Description: Required for worker agents

**Capabilities:**
- Calculate copay responsibility
- Compute deductible responsibility
- Calculate coinsurance amounts
- Apply out-of-pocket maximum limits
- Provide line-item cost breakdown
- Handle unknown service costs, deductible/OOP scenarios

**Output Format:**
- Service information
- Cost breakdown (copay, deductible, coinsurance)
- Out-of-pocket maximum application
- Cost summary
- Financial notes and disclaimers

### 6. Documentation
**File:** `insurance-eligibility-README.md`
**Type:** Blueprint documentation
**Lines:** 450+

Comprehensive documentation including:

**Sections:**
1. **Problem:** Healthcare eligibility verification challenges
2. **Approach:** Three-worker orchestration architecture
3. **Capabilities:** Coverage verification, benefits analysis, cost calculation
4. **Key Metrics:** Operational efficiency, accuracy, business impact
5. **Agent Roles:** Detailed responsibilities and configurations
6. **Usage Examples:** Three real-world scenarios with inputs/outputs
7. **Implementation Guide:** Deployment steps and data formats
8. **Integration Points:** Upstream and downstream system connections
9. **Success Metrics:** KPIs with baselines and targets
10. **Limitations:** Coverage, accuracy, and compliance notes
11. **Troubleshooting:** Common issues and resolutions
12. **Best Practices:** For healthcare organizations and patient communication

## Agent Configuration Summary

| Agent | Model | Temp | Type | Purpose |
|-------|-------|------|------|---------|
| Eligibility Coordinator | gpt-4o | 0.3 | Manager | Orchestrate workflow |
| Coverage Checker | gpt-4o-mini | 0.2 | Worker | Verify coverage |
| Benefits Analyzer | gpt-4o-mini | 0.2 | Worker | Analyze benefits |
| Patient Responsibility Calculator | gpt-4o-mini | 0.2 | Worker | Calculate costs |

## Key Features

### Coverage Verification
- Member eligibility verification with carrier
- Deductible and out-of-pocket extraction
- Plan type identification (PPO, HMO, POS, Medicare, Medicaid)
- Effective date verification
- Terminated/pending coverage detection

### Benefits Analysis
- Service coverage determination (covered/not covered/conditional)
- Service-specific copay/coinsurance extraction
- Pre-authorization requirement identification
- Frequency and limitation detection
- Exclusion identification

### Patient Cost Calculation
- Accurate copay computation
- Deductible responsibility calculation
- Coinsurance amount calculation
- Out-of-pocket maximum application
- Itemized cost breakdown

### Edge Cases
- Terminated coverage before service date
- Multiple insurance plans (secondary insurance)
- Pre-authorization requirements
- No active coverage found
- Unknown service costs
- Out-of-network services
- Service cost variations

## Workflow

```
Eligibility Request
    ↓
Eligibility Coordinator (Manager)
    ├─→ Coverage Checker
    │   └─→ Coverage Status, Deductible, OOP Max
    ├─→ Benefits Analyzer
    │   └─→ Coverage, Copay, Coinsurance, Pre-Auth
    └─→ Patient Responsibility Calculator
        └─→ Copay, Deductible, Coinsurance, Total Cost
    ↓
Comprehensive Eligibility Summary
```

## Deployment Instructions

### Step 1: Validate YAML Files
```bash
cd blueprints/local/healthcare
bp validate insurance-eligibility-verifier.yaml
```

### Step 2: Create Blueprint
```bash
bp create insurance-eligibility-verifier.yaml
```

This will:
1. Create Eligibility Coordinator agent
2. Create Coverage Checker worker agent
3. Create Benefits Analyzer worker agent
4. Create Patient Responsibility Calculator worker agent
5. Create Insurance Eligibility Verifier blueprint
6. Link agents to blueprint

### Step 3: Test Deployment
```bash
bp eval <manager-agent-id> \
  "Verify coverage for John Smith, DOB 05/15/1975, Aetna member 123456789, office visit on 01/20/2025"
```

### Step 4: Integrate with Workflows
- Connect to patient intake system
- Route requests to eligibility verification
- Capture results in patient financial counseling system
- Track metrics and feedback

## Configuration Details

### Manager Agent (Eligibility Coordinator)
- **Model:** gpt-4o (required for orchestration)
- **Temperature:** 0.3 (consistent coordination)
- **Context:** Healthcare eligibility verification with staff coordination
- **Responsibilities:**
  - Manage 3 specialized worker agents
  - Execute 4-step verification workflow
  - Synthesize results into comprehensive summary
  - Handle edge cases and exceptions
  - Provide actionable next steps

### Worker Agents (All Three)
- **Model:** gpt-4o-mini (cost optimization)
- **Temperature:** 0.2 (deterministic, consistent)
- **Store Messages:** false (stateless per request)
- **Features:** None (focused on specific tasks)

**Coverage Checker:**
- Focus: Coverage baseline extraction
- Input: Patient, insurance, service date
- Output: Coverage status, deductible, OOP max

**Benefits Analyzer:**
- Focus: Service-level benefit analysis
- Input: Coverage data + service type
- Output: Benefits, pre-auth, limitations

**Patient Responsibility Calculator:**
- Focus: Cost calculation
- Input: Coverage + benefits + service cost
- Output: Patient financial responsibility

## Quality Metrics

### Coverage Verification Accuracy
- Target: 98%+ accuracy
- Baseline: 85% (manual verification)
- Improvement: +13% accuracy

### Pre-Authorization Identification
- Target: 100% catch rate
- Baseline: 90%
- Improvement: +10% catch rate

### Time Savings
- Target: 10-15 minutes per verification
- Baseline: 2-3 hours (120-180 minutes)
- Improvement: 90% time reduction

### Cost Estimate Accuracy
- Target: 99%+ accuracy
- Baseline: 80%
- Improvement: +19% accuracy

## Output Examples

### Example Output 1: Active Coverage, Simple Case
```
=== ELIGIBILITY VERIFICATION SUMMARY ===

COVERAGE STATUS
Overall Status: COVERED
Plan Type: PPO
Effective Dates: 01/01/2025 to 12/31/2025
Deductible: $1,500 | Deductible Met: $500

BENEFITS FOR OFFICE_VISIT
Covered: YES
Coinsurance: 20%
Copay: $40
Prior Auth Required: NO
Limitations: None

PATIENT FINANCIAL RESPONSIBILITY
Estimated Copay: $40
Estimated Coinsurance: $0
Deductible Responsibility: $500
Out-of-Pocket Max: $6,000
Estimated Total Cost: $540

NEXT STEPS
1. Schedule appointment with in-network provider
2. Provide patient with $540 cost estimate
===
```

### Example Output 2: Pre-Authorization Required
```
=== ELIGIBILITY VERIFICATION SUMMARY ===

COVERAGE STATUS
Overall Status: COVERED
Plan Type: PPO
Effective Dates: 01/01/2025 to 12/31/2025
Deductible: Fully Met

BENEFITS FOR KNEE_ARTHROSCOPY
Covered: YES
Coinsurance: 20%
Prior Auth Required: YES

PATIENT FINANCIAL RESPONSIBILITY
Estimated Total Cost: $600 (20% coinsurance)

NEXT STEPS
1. Obtain pre-authorization from plan before procedure
2. Typical approval: 5-7 business days
3. Provide authorization number to facility
===
```

## Support & Troubleshooting

### Validation Errors
If `bp validate` fails:
1. Check YAML indentation (2 spaces)
2. Verify file paths in blueprint definition
3. Ensure agent files exist in specified locations
4. Check for YAML syntax errors

### Agent Creation Failures
If agent creation fails:
1. Verify API credentials (LYZR_API_KEY, BLUEPRINT_BEARER_TOKEN)
2. Check organization ID (LYZR_ORG_ID)
3. Verify network access to agent-api and pagos services
4. Check model availability (gpt-4o, gpt-4o-mini)

### Coverage Verification Failures
If verification returns "UNABLE_TO_VERIFY":
1. Verify member ID matches insurance card
2. Check carrier portal availability
3. Confirm service date is within coverage period
4. Contact carrier customer service

## Related Resources

- **BP-SDK Documentation:** /Users/harshitchoudhary/Documents/Work/Lyzr/projects/bp-sdk/README.md
- **Agent Persona Skills:** .claude/skills/agent-persona/
- **Agent Instructions Skills:** .claude/skills/agent-instructions/
- **Agent Technical Skills:** .claude/skills/agent-technical/
- **Blueprint YAML Skills:** .claude/skills/blueprint-yaml/

## Changelog

### Version 1.0 (2025-01-15)
- Initial blueprint creation
- Three-worker orchestration pattern
- Support for major insurance plan types
- Comprehensive documentation
- Edge case handling for common scenarios
