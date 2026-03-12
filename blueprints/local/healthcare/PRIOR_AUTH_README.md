# Prior Authorization Agent

**Category:** Customer
**Tags:** healthcare, prior-authorization, insurance, claims, automation
**Blueprint ID:** (generated on deployment)

---

## Problem

Prior authorization approval for healthcare services is a critical but time-consuming process. Medical providers spend 45+ minutes per request navigating complex insurance policies, compiling clinical evidence, and generating compliant submissions.

**Key Challenges:**
- **Policy Complexity**: Each payer has different authorization requirements, approval criteria, and submission procedures
- **Evidence Gathering**: Manual compilation of relevant clinical findings from patient records is error-prone and time-consuming
- **Compliance Risk**: Incorrect submissions due to policy misinterpretation lead to denials and delays
- **Operational Bottleneck**: Administrative staff spend 6-10+ hours daily on routine authorizations
- **Patient Impact**: Authorization delays postpone care and worsen patient outcomes

**Status Quo Impact:**
- Average authorization time: 45-120 minutes per request
- Administrative cost: $15-25 per authorization (fully loaded)
- Denial rate from incomplete/incorrect submissions: 8-15%
- Average denial-to-approval cycle time: 5-10 days
- Staff frustration and burnout from repetitive manual work

---

## Approach

The Prior Authorization Agent automates the complete authorization workflow through a **specialized three-agent orchestration system**:

```
User Input (Payer Policy + Clinical Records)
            ↓
    ┌───────────────────────────────┐
    │  Prior Auth Coordinator       │
    │  (Manager Agent)              │
    │  - Orchestrates workflow      │
    │  - Coordinates specialists    │
    │  - Ensures quality            │
    └───────┬───────────┬───────────┘
            │           │
        ┌───▼──┐    ┌───▼──────────┐    ┌──────────────────┐
        │      │    │              │    │                  │
        ▼      ▼    ▼              ▼    ▼                  ▼
    Policy   Clinical          Submission
    Analyzer Evidence          Generator
             Compiler


Output: Ready-to-Submit Authorization Package
```

### Agent Specialization

**1. Payer Policy Analyzer (Worker)**
- Extracts authorization requirements from insurance policy documents
- Identifies: approval criteria, required documentation, clinical indicators
- Maps policy requirements to specific approval pathways
- Provides structured requirements for evidence compilation
- Output: Structured policy requirements

**2. Clinical Evidence Compiler (Worker)**
- Organizes patient clinical information into policy-aligned evidence
- Maps clinical findings to specific approval criteria
- Identifies evidence strength for each criterion
- Flags missing or incomplete documentation
- Output: Organized clinical evidence with criterion mapping

**3. Authorization Submission Generator (Worker)**
- Integrates policy requirements with clinical evidence
- Generates submission documents formatted to exact payer specifications
- Produces submission-ready packages with all supporting materials
- Ensures compliance with payer requirements
- Output: Complete, submission-ready authorization package

**Coordinator (Manager)**
- Orchestrates the three-agent workflow
- Ensures each specialist completes their task
- Manages workflow sequencing and data passing
- Produces final comprehensive output
- Handles edge cases and escalations

### Workflow

1. **Input**: Payer policy document + patient clinical records
2. **Step 1**: Policy Analyzer extracts authorization requirements
3. **Step 2**: Evidence Compiler organizes clinical evidence to match requirements
4. **Step 3**: Submission Generator creates submission-ready package
5. **Output**: Complete, compliant authorization ready for immediate submission

### Key Benefits

- **Speed**: 45+ minutes → 3-5 minutes (10-15x faster)
- **Accuracy**: Structured requirements reduce compliance errors
- **Quality**: Systematic approach ensures complete documentation
- **Consistency**: Standardized process eliminates variability
- **Compliance**: Exact adherence to payer specifications
- **Cost**: Reduces administrative time and staff burden

---

## Capabilities

### 1. Policy Requirement Extraction

**What It Does:**
- Analyzes insurance policy documents in plain text or structured format
- Extracts authorization requirements specific to requested service
- Identifies all approval criteria with specific values/thresholds
- Lists required documentation with specificity levels
- Maps submission procedures and contact information

**Extracted Information:**
- Service-specific approval criteria
- Diagnosis requirements
- Severity thresholds
- Conservative treatment requirements
- Clinical indicator specifications
- Required documentation types and sources
- Submission procedures and contacts
- Form requirements and versions

**Edge Case Handling:**
- Ambiguous policies with multiple interpretations
- Services not covered in provided policy
- References to external guidelines
- Multiple policy sections that might apply

### 2. Clinical Evidence Organization

**What It Does:**
- Compiles patient clinical records into organized evidence
- Maps each finding to specific payer approval criteria
- Assesses evidence strength (strong/moderate/weak)
- Identifies documentation gaps
- Prepares evidence for submission

**Organized Evidence Includes:**
- Diagnosis verification with supporting findings
- Severity assessment with specific values
- Conservative treatment documentation
- Required supporting documentation status
- Evidence strength rating for each criterion

**Quality Metrics:**
- Completeness assessment (complete/substantial/incomplete)
- Documentation quality rating
- Gap identification and recommendations
- Evidence-to-criterion mapping

### 3. Submission Generation

**What It Does:**
- Creates complete authorization submission packages
- Formats submissions exactly to payer specifications
- Integrates clinical evidence with policy requirements
- Produces submission-ready documents
- Provides supporting documentation organization

**Submission Components:**
- Completed authorization forms (payer-specific)
- Medical necessity statement
- Clinical evidence citations
- Patient demographics
- Insurance information
- Provider credentials and contact
- Supporting documentation list
- Submission instructions

**Quality Assurance:**
- Checklist verification of all required elements
- Format compliance confirmation
- Evidence integration verification
- Completeness validation

### 4. Workflow Orchestration

**What It Does:**
- Manages complete three-agent authorization workflow
- Handles data passing between specialists
- Ensures quality at each stage
- Manages edge cases and escalations
- Produces final comprehensive output

**Orchestration Features:**
- Sequential workflow execution
- Quality gates between stages
- Error detection and escalation
- Final output validation
- Metadata tracking (time, quality scores)

---

## Usage Examples

### Example 1: Routine Prior Authorization

**Input:**
```
Service: MRI of lumbar spine for patient with back pain
Payer: Blue Cross Blue Shield
Patient: John Smith, DOB 1/15/1960, Policy #12345678
Insurance: Group #ABC123, Effective: 1/1/2024

Payer Policy: [BCBS Prior Auth Policy for Advanced Imaging - Section 5.2]

Clinical Records:
- Chief Complaint: Chronic lower back pain for 6 months
- Exam: Limited range of motion, positive straight leg raise
- Conservative Treatment: Physical therapy for 6 weeks (minimal improvement)
- MRI Indication: Rule out herniated disk
```

**Process:**
1. Policy Analyzer extracts BCBS MRI authorization requirements
2. Evidence Compiler organizes clinical findings (6-month history, conservative care attempt, exam findings)
3. Submission Generator creates BCBS-compliant authorization
4. Coordinator produces ready-to-submit package

**Output:**
- Structured policy requirements
- Organized clinical evidence mapping to criteria
- Completed BCBS authorization form
- Medical necessity statement
- Supporting documentation list
- Submission contact information

**Time Saved:** ~45 minutes → ~3 minutes

---

### Example 2: Complex Authorization with Missing Evidence

**Input:**
```
Service: Robotic surgical system use for prostate cancer treatment
Payer: UnitedHealthcare
Patient: Robert Johnson, DOB 3/22/1955, Policy #87654321
Insurance: Individual, Effective: 3/15/2023

Payer Policy: [UHC Prior Auth Policy for Robotic Prostate Surgery - Section 7.1]

Clinical Records:
- Diagnosis: Localized prostate cancer (Gleason 7)
- PSA: 8.2 ng/mL
- Staging: T2b, N0, M0
- Pathology: Not yet available (pending biopsy results)
```

**Process:**
1. Policy Analyzer identifies UHC requirements including pathology confirmation
2. Evidence Compiler notes missing pathology results, flags as "INCOMPLETE"
3. Coordinator identifies critical gap
4. Submission Generator creates submission noting missing evidence with explanation
5. Package includes recommendation for resubmission when pathology available

**Output:**
- Flag that authorization is CONDITIONAL pending pathology
- Clear documentation of what's missing
- Recommendation for obtaining pathology
- Partial submission with current evidence
- Process for expedited resubmission once results available

**Risk Mitigation:** Proactive flagging prevents denial for incomplete documentation

---

### Example 3: Urgent Authorization Request

**Input:**
```
Service: Emergency revision surgery for failed hip replacement
Payer: Aetna
Patient: Margaret Williams, DOB 7/8/1945, Policy #55555555
Insurance: Medicare Supplement, Effective: 6/1/2023

Urgency: URGENT - Surgery scheduled for tomorrow (8/15/2024)

Payer Policy: [Aetna Prior Auth Policy for Orthopedic Revision Surgery - Section 3.5]

Clinical Records:
- Original Surgery: Right hip replacement 18 months ago
- Current Complaint: Severe pain, hip instability, concern for dislocation
- Imaging: X-ray shows component migration
- Exam: Severe hip pain with minimal range of motion
```

**Process:**
1. Coordinator flags as "URGENT" priority
2. Policy Analyzer extracts EXPEDITED authorization pathway
3. Evidence Compiler fast-tracks evidence organization
4. Submission Generator marks submission as "EXPEDITED REQUEST"
5. Coordinator provides urgent payer contact numbers

**Output:**
- Submission marked EXPEDITED
- Urgency statement based on clinical findings
- Direct payer contact information for expedited review
- Expected decision timeline (same-day vs 24-hour)
- Protocol for rapid response if additional information needed

**Clinical Impact:** Prevents delay for urgent surgical cases

---

## Technical Architecture

### Agent Configuration

**Manager: Prior Auth Coordinator**
- Model: `gpt-4o` (complex orchestration requires advanced reasoning)
- Temperature: 0.3 (deterministic, consistent workflow)
- Store Messages: True (maintains conversation context)
- Role: Senior Prior Authorization Process Coordinator
- Responsibility: Orchestrate all agents, ensure quality, handle exceptions

**Worker 1: Payer Policy Analyzer**
- Model: `gpt-4o-mini` (extraction task, cost-optimized)
- Temperature: 0.2 (deterministic, exact requirement extraction)
- Store Messages: False (stateless extraction)
- Role: Expert Healthcare Policy Analysis Specialist
- Responsibility: Extract policy requirements with precision

**Worker 2: Clinical Evidence Compiler**
- Model: `gpt-4o-mini` (organization task, cost-optimized)
- Temperature: 0.2 (deterministic, exact evidence mapping)
- Store Messages: False (stateless compilation)
- Role: Expert Clinical Evidence Compilation Specialist
- Responsibility: Organize evidence, assess strength, identify gaps

**Worker 3: Authorization Submission Generator**
- Model: `gpt-4o` (content generation requires nuanced writing)
- Temperature: 0.3 (slightly flexible for professional tone)
- Store Messages: False (stateless generation)
- Role: Expert Prior Authorization Submission Specialist
- Responsibility: Create submission-ready documents

### Data Flow

```
┌─────────────────────────────────────────┐
│ User Input                              │
│ - Payer Policy Document                 │
│ - Patient Clinical Records              │
│ - Service/Procedure Details             │
│ - Insurance Information                 │
└──────────────────┬──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Policy Analyzer     │
        │  Extracts Policies   │
        └──────────┬───────────┘
                   │
        ┌──────────▼──────────────┐
        │ Policy Requirements      │
        │ - Approval Criteria     │
        │ - Documentation Needed  │
        │ - Clinical Indicators   │
        └──────────┬──────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  Evidence Compiler       │
        │  Organizes Evidence      │
        └──────────┬───────────────┘
                   │
        ┌──────────▼──────────────────┐
        │ Clinical Evidence            │
        │ - Diagnosis Verification     │
        │ - Severity Assessment        │
        │ - Evidence Strength Rating   │
        │ - Documentation Status      │
        └──────────┬──────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │  Submission Generator        │
        │  Creates Submission          │
        └──────────┬───────────────────┘
                   │
        ┌──────────▼──────────────────────────┐
        │ Authorization Submission Package     │
        │ - Completed Forms                   │
        │ - Medical Necessity Statement       │
        │ - Clinical Evidence Integration     │
        │ - Supporting Documents List         │
        │ - Submission Instructions           │
        └──────────┬───────────────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ User Output              │
        │ Ready for Submission     │
        └──────────────────────────┘
```

### Instruction Design

Each agent receives:
1. **Identity Statement**: Clear role and responsibility
2. **Context**: Background on healthcare authorization processes
3. **Process Steps**: Detailed, sequential steps for their specific task
4. **Input Format**: Expected input structure with examples
5. **Output Format**: Exact output structure required
6. **Rules & Constraints**: Hard boundaries (never modify evidence, never infer clinical info, etc.)
7. **Edge Cases**: How to handle unusual situations

---

## Error Handling

### Policy Analysis Errors

**Issue: Policy document is vague or unclear**
- Agent notes exact language that is unclear
- Marks confidence as MEDIUM or LOW
- Recommends contacting payer for clarification
- Provides best interpretation with caveat

**Issue: Service not found in provided policy**
- Agent clearly states service not found
- Notes related services that might apply
- Recommends obtaining updated policy
- Does NOT extrapolate from general knowledge

### Evidence Compilation Errors

**Issue: Critical clinical documentation is missing**
- Agent clearly identifies what's missing
- Assesses what CAN be evaluated with available records
- Rates evidence completeness as INCOMPLETE
- Specifies exactly what additional records are needed

**Issue: Clinical findings contradict authorization requirement**
- Agent presents findings exactly as documented
- Notes contradiction clearly
- Does NOT reframe or reinterpret findings
- Flags for coordinator review

### Submission Generation Errors

**Issue: Evidence doesn't fully meet all payer criteria**
- Submission clearly marks which criteria are met/unmet
- Presents best available evidence for unmet criteria
- Includes explanation of gaps in submission
- Recommends payer discussion if substantially incomplete

**Issue: Required supporting documents cannot be obtained**
- Submission lists exactly what's missing
- Explains why document cannot be obtained
- Includes alternative evidence provided instead
- Explains why missing documents don't negate medical necessity

---

## Quality Metrics

### Processing Metrics
- **Speed**: Target 3-5 minutes (vs. 45-120 minutes manual)
- **Completeness**: 100% of payer requirements documented
- **Accuracy**: 0 format/compliance errors
- **Consistency**: Identical approach across all requests

### Evidence Quality
- **Coverage**: All payer-required evidence types included
- **Strength**: Explicit rating for each approval criterion
- **Gaps**: Identified and explained
- **Citations**: 100% of evidence cited with source and date

### Submission Quality
- **Compliance**: 100% adherence to payer format requirements
- **Readiness**: Requires 0 edits before submission
- **Clarity**: Clear medical necessity statement
- **Completeness**: All required fields and documents included

---

## Limitations & Considerations

### What This Agent Does Well
- Extracts structured policy requirements from documents
- Organizes and maps clinical evidence systematically
- Generates submission documents formatted to specifications
- Accelerates routine authorization requests significantly
- Reduces administrative burden and errors

### What This Agent Cannot Do
- Provide clinical judgment (clinical evidence only)
- Modify clinical records or findings (organizational only)
- Guarantee payer approval (depends on clinical merit)
- Appeal denied authorizations (evidence-based only)
- Override medical decision-making

### Important Safeguards
- **Clinical Integrity**: Never modifies clinical information
- **Policy Compliance**: Never extrapolates beyond provided policy
- **Transparency**: Clearly flags gaps and missing evidence
- **Human Review**: All submissions reviewed by provider before sending
- **Audit Trail**: Complete documentation of process and decisions

---

## Deployment Notes

### Configuration
- **Category**: customer
- **Tags**: healthcare, prior-authorization, insurance, claims, automation
- **Visibility**: private (healthcare-sensitive use case)

### Prerequisites
- Access to payer policy documents
- Complete patient clinical records
- Current insurance information
- Provider credentials and contact info

### Integration Points
- Clinical document management systems
- Insurance/payer databases
- Submission transmission systems (fax, email, portal)
- Electronic health record (EHR) systems

### Success Metrics to Track
- Time per authorization (target: <5 minutes)
- Submission completeness (target: 100%)
- Authorization approval rate (target: >95%)
- Resubmission rate due to incomplete submission (target: <5%)
- Staff satisfaction improvement (target: >80%)

---

## Support & Troubleshooting

### Common Issues

**Policy Analysis Incomplete**
- Ensure full policy document is provided (not just summary)
- Check that service type is clearly specified
- Verify policy version is current

**Evidence Gaps Identified**
- Request missing clinical records
- Prioritize obtaining evidence that specifically addresses policy criteria
- Consider requesting recent evaluation if records are >6 months old

**Submission Generation Delayed**
- Verify all policy requirements were extracted
- Ensure clinical evidence is well-organized
- Check that payer-specific forms are available

### Contact Information
- Documentation: [link to Lyzr docs]
- Support Email: support@lyzr.ai
- Issue Tracking: [GitHub/Linear link]

---

## Version History

- **v1.0** (Initial Release): Complete three-agent orchestration for prior authorization
  - Payer Policy Analyzer
  - Clinical Evidence Compiler
  - Authorization Submission Generator
  - Prior Auth Coordinator (manager)

---

## License & Usage

This blueprint is provided as part of the Lyzr Platform.

**Acceptable Use:**
- Automate prior authorization requests for healthcare organizations
- Reduce administrative burden on medical staff
- Improve authorization submission quality and compliance
- Support healthcare operations and patient care acceleration

**Not Acceptable:**
- Use for fraudulent claims or misrepresentation
- Modification of clinical evidence or records
- Circumvention of medical necessity requirements
- Compliance violations with healthcare regulations

---

## Related Blueprints

- **Initial Patient Screener**: Pre-qualification assessment for services
- **Insurance Verification Agent**: Real-time insurance eligibility checking
- **Claims Appeal Generator**: Processing denied claims and appeals
- **Patient Intake Coordinator**: Comprehensive patient onboarding and data collection

---

## Feedback & Improvements

This blueprint is actively maintained and improved based on real-world usage.

**Known Improvements in Development:**
- Multi-payer policy caching for faster repeated requests
- Insurance terminology standardization module
- Appeal/resubmission workflow enhancement
- Real-time policy database integration

**To Suggest Improvements:**
- Use the feedback button in Agent Studio
- Email: blueprint-feedback@lyzr.ai
- Linear: [Link to blueprint improvement project]

---

**Status**: Production Ready
**Last Updated**: January 2025
**Maintained By**: Blueprint Team
