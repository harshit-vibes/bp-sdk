# Prior Authorization Agent - Quick Start Guide

Get started with the Prior Authorization Agent in 5 minutes.

---

## Installation

### Option 1: Using SDK (Recommended)

```bash
# Install bp-sdk if not already installed
pip install bp-sdk

# Navigate to blueprint directory
cd blueprints/local/healthcare

# Create the blueprint from YAML
bp create prior-authorization-agent.yaml

# Expected output:
# Blueprint created successfully!
# Blueprint ID: bp_xxxxx
# Manager Agent ID: agent_xxxxx
# Worker IDs: agent_xxxxx, agent_xxxxx, agent_xxxxx
```

### Option 2: Manual Upload

1. Log into Lyzr Agent Studio
2. Click "Create Blueprint"
3. Upload `prior-authorization-agent.yaml`
4. Verify agents are created
5. Test with sample authorization request

---

## Basic Usage

### Step 1: Prepare Your Input

You need three things:
1. **Payer Policy Document** - Insurance company's policy for the service
2. **Patient Clinical Records** - Relevant medical records
3. **Insurance Information** - Patient's policy and group numbers

**Example Input:**
```
Service: MRI of the lumbar spine
Payer: Blue Cross Blue Shield (BCBS)
Patient: John Doe, DOB: 1/15/1960, Policy #: BC12345678

Policy Document:
[Paste full BCBS policy for advanced imaging]

Clinical Records:
- Chief Complaint: Lower back pain for 6 months
- Physical Exam: Positive straight leg raise, limited ROM
- Imaging Request: Rule out herniated disk
- Conservative Treatment: Physical therapy x 6 weeks (minimal improvement)
```

### Step 2: Run the Blueprint

Using the CLI:
```bash
# Chat with the manager agent directly
bp chat bp_xxxxx

# Paste your input and press Enter
# Agent will process through all three specialists
```

Or via Agent Studio:
1. Open your Prior Authorization Agent blueprint
2. Click "Chat"
3. Paste your authorization request
4. Review the structured output

### Step 3: Review Output

The agent produces a complete package:

**1. Policy Requirements (from Policy Analyzer)**
- Service Category
- Approval Criteria
- Required Documentation
- Clinical Indicators
- Submission Procedures

**2. Clinical Evidence (from Evidence Compiler)**
- Diagnosis Verification
- Severity Assessment
- Conservative Treatment Documentation
- Evidence Strength Rating
- Documentation Status

**3. Submission Package (from Submission Generator)**
- Completed Authorization Form
- Medical Necessity Statement
- Evidence Integration
- Supporting Documents List
- Submission Instructions

**4. Coordinator Summary**
- Workflow Status
- Overall Quality Assessment
- Next Steps

### Step 4: Submit Authorization

Once you have the complete output package:

1. **Review**: Read through the generated submission
2. **Sign**: Add provider signature (print and sign, or e-signature)
3. **Attach**: Include supporting clinical documents
4. **Submit**: Follow payer-specific submission method (fax, email, portal)
5. **Track**: Monitor for authorization decision

---

## Common Scenarios

### Scenario 1: Simple Routine Authorization

**Time**: ~3 minutes end-to-end

**What to provide:**
- Clear policy document section
- Recent clinical records (last 2-4 weeks)
- Standard insurance information

**Expected output:**
- Well-structured policy requirements
- Complete evidence compilation
- Submission-ready package

**Success indicator:** "Ready for Submission" status in coordinator summary

---

### Scenario 2: Complex Case with Missing Evidence

**Time**: ~5 minutes (includes gap identification)

**What to provide:**
- Full policy document (may have complex criteria)
- Available clinical records (even if incomplete)
- Insurance and service details

**Expected output:**
- Policy requirements clearly extracted
- Evidence gaps identified with recommendations
- Partial submission noting missing items
- Guidance for obtaining missing documentation

**Success indicator:** Clear "Missing Documentation" list with guidance

---

### Scenario 3: Urgent Authorization

**Time**: ~4 minutes (expedited workflow)

**What to provide:**
- Policy document
- Current clinical information
- **Urgency flag** - "URGENT - surgery scheduled for tomorrow"

**Expected output:**
- Same quality, prioritized processing
- Submission marked "EXPEDITED REQUEST"
- Payer urgent contact information
- Expected decision timeline

**Success indicator:** "EXPEDITED" notation in final package

---

## Tips for Best Results

### Do This:
1. **Provide complete policy documents** - Full text, not summaries
2. **Include all relevant clinical records** - Use your most recent evaluations
3. **Be specific about the service** - "MRI lumbar spine" not just "MRI"
4. **Include conservative treatment attempts** - If policy requires them
5. **Provide current insurance info** - Verify plan is active

### Don't Do This:
1. **Use vague policy references** - Always provide full text
2. **Summarize clinical findings** - Provide actual records
3. **Modify or omit negative findings** - Agent needs complete picture
4. **Assume policy coverage** - Let agent extract actual requirements
5. **Rush without checking output** - Always review before submitting

### Pro Tips:
1. **Copy/paste policy directly** - OCR quality can vary, copy text is better
2. **Include objective values** - Lab values, imaging findings, specific measurements
3. **Note treatment dates** - Specific dates for conservative treatments
4. **Provide provider credentials** - Licenses, specialties, contact info
5. **Include insurance IDs** - Policy numbers, group numbers, member IDs

---

## Understanding the Output

### Quality Metrics in Output

**Evidence Strength Ratings:**
- **STRONG** - Multiple supporting findings, clear alignment with criteria
- **MODERATE** - Some supporting evidence, reasonable alignment
- **WEAK** - Limited evidence, may require additional documentation

**Completeness Ratings:**
- **COMPLETE** - All required documentation included
- **SUBSTANTIAL** - Most documentation included, minor gaps
- **INCOMPLETE** - Significant gaps, additional records needed

**Confidence Levels:**
- **HIGH** - Clear extraction, minimal ambiguity
- **MEDIUM** - Some interpretation needed, good confidence
- **LOW** - Significant ambiguity, recommend payer clarification

### Key Status Indicators

**Ready for Submission**
- ✓ All required elements complete
- ✓ Quality checks passed
- ✓ No critical gaps identified
- Action: Review and submit immediately

**Conditional - Missing Documentation**
- ✓ Submission can be prepared
- ✗ Some evidence gaps identified
- ⚠ Approval may be delayed pending documentation
- Action: Obtain missing records, resubmit

**Escalation Required**
- ⚠ Policy is ambiguous or unclear
- ⚠ Clinical findings conflict with requirements
- ⚠ Complex case requiring payer discussion
- Action: Contact payer for clarification before final submission

---

## Troubleshooting

### Problem: Policy Analysis Incomplete

**Symptoms:**
- Missing approval criteria
- Incomplete documentation requirements
- Vague policy extraction

**Solution:**
- Ensure you provided FULL policy text (not summary)
- Check that service type matches policy section
- Verify policy version is current
- Try providing policy section number explicitly

**Example fix:**
```
Instead of: "BCBS imaging policy"
Provide: "Blue Cross Blue Shield Prior Authorization Policy,
Section 5.2 Advanced Imaging, Effective 1/1/2024 [FULL TEXT]"
```

---

### Problem: Evidence Gaps Identified

**Symptoms:**
- "INCOMPLETE_DATA" flags
- Critical evidence missing
- Low confidence ratings

**Solution:**
- Request missing clinical records from provider
- Include recent evaluations (within 6 months)
- Obtain specific test results if policy requires them
- Include specialist consultations if needed

**Example fix:**
```
Missing: "Recent imaging studies"
Action: Request patient's recent MRI from radiology department
Timeline: Often available within 24 hours
```

---

### Problem: Submission Format Errors

**Symptoms:**
- "Format compliance issues"
- Wrong form version referenced
- Contact information incomplete

**Solution:**
- Verify payer-specific form version
- Confirm current submission address
- Update provider contact information
- Check for recent policy updates

**Example fix:**
```
Issue: "Using old authorization form (v2.0)"
Solution: Download current form (v3.1) from payer website
Reference: "Forms update annually - check payer website for latest"
```

---

### Problem: Long Processing Time

**Symptoms:**
- Agent taking >10 minutes to process
- Slow response times

**Solution:**
- Check input size (very large documents may slow processing)
- Verify system resources are available
- Ensure stable internet connection
- Try resubmitting if intermittent

**Example fix:**
```
For very large policy documents (>100 pages):
1. Extract relevant sections first
2. Provide section-by-section instead of full document
3. Include specific service subsection reference
```

---

## Advanced Usage

### Batch Processing

Process multiple authorizations:

```bash
# Create a batch request file (batch.json)
{
  "requests": [
    {
      "service": "MRI lumbar spine",
      "payer": "BCBS",
      "policy": "[policy text]",
      "clinical_records": "[records]"
    },
    {
      "service": "Physical therapy",
      "payer": "UHC",
      "policy": "[policy text]",
      "clinical_records": "[records]"
    }
  ]
}

# Submit batch
bp batch process batch.json --output results.json
```

---

### API Integration

Call the blueprint programmatically:

```python
from sdk import BlueprintClient

client = BlueprintClient(
    api_key="your-api-key",
    bearer_token="your-token",
    organization_id="your-org-id"
)

# Get the blueprint
blueprint = client.get("bp_xxxxx")

# Prepare input
request = {
    "service": "MRI lumbar spine",
    "payer_policy": "[policy text]",
    "clinical_records": "[records text]",
    "patient_info": {
        "name": "John Doe",
        "dob": "1/15/1960",
        "policy_number": "BC12345678"
    }
}

# Call manager agent
response = blueprint.manager.chat(str(request))

# Parse output
output = response.content
print(output)
```

---

### Custom Workflows

Modify for your specific needs:

1. **Add Pre-Processing**: Validate inputs before sending
2. **Add Post-Processing**: Extract structured data from output
3. **Add Notifications**: Alert staff when authorization is ready
4. **Add Tracking**: Log all authorizations in your system
5. **Add Analytics**: Track approval rates and processing times

---

## Getting Help

### Quick Links
- **Documentation**: See `PRIOR_AUTH_README.md`
- **Technical Details**: See `DEPLOYMENT_SUMMARY.md`
- **Agent Instructions**: Review individual agent YAML files

### Support
- **Email**: support@lyzr.ai
- **Documentation**: https://docs.lyzr.ai
- **Community**: [Lyzr Community Forum]
- **Issues**: [GitHub Issues]

### Feedback
- **Report Issues**: Use GitHub Issues
- **Suggest Improvements**: Email blueprint-feedback@lyzr.ai
- **Share Success Stories**: Share with community@lyzr.ai

---

## Next Steps

1. **Deploy**: Set up the blueprint in your environment
2. **Test**: Try with a sample authorization request
3. **Integrate**: Connect with your clinical systems
4. **Train**: Brief your team on usage
5. **Monitor**: Track performance metrics
6. **Optimize**: Gather feedback and iterate

---

## Success Metrics

Track these metrics to measure success:

| Metric | Baseline | Target | Timeline |
|--------|----------|--------|----------|
| Time per authorization | 45-120 min | <5 min | Week 1 |
| Submission completeness | 85-90% | >99% | Week 2 |
| Approval rate | 92-95% | >97% | Week 4 |
| Resubmission rate | 8-10% | <2% | Week 4 |
| Staff satisfaction | Baseline | >80% satisfied | Week 2 |

---

**Ready to get started?**

1. Deploy the blueprint
2. Test with a sample authorization
3. Integrate with your systems
4. Track your success!

For detailed documentation, see `PRIOR_AUTH_README.md`
For technical details, see `DEPLOYMENT_SUMMARY.md`
