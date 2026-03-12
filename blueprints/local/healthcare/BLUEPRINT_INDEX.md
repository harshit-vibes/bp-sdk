# Healthcare Blueprints - Index

Central reference for all healthcare-focused Lyzr blueprints.

---

## Overview

Healthcare blueprints address critical operational challenges in medical organizations through specialized multi-agent systems.

**Available Blueprints:**
1. **Prior Authorization Agent** (Blueprint 5) ← CURRENT
2. Initial Patient Screener (Blueprint 1) - Coming Soon
3. Insurance Verification Agent (Blueprint 2) - Coming Soon
4. Clinical Notes Summarizer (Blueprint 3) - Coming Soon
5. Discharge Planner (Blueprint 4) - Coming Soon

---

## Blueprint 5: Prior Authorization Agent

**Status**: ✅ Production Ready (v1.0)
**Deployed**: January 2025
**Category**: customer
**Tags**: healthcare, prior-authorization, insurance, claims, automation

### Quick Summary
Automates healthcare prior authorization requests. Reduces processing time from 45+ minutes to 3-5 minutes by orchestrating three specialized agents:
- Policy Analyzer: Extracts requirements from insurance policies
- Evidence Compiler: Organizes clinical evidence
- Submission Generator: Creates submission-ready packages

### Key Metrics
- **Speed**: 45+ min → 3-5 min (10-25x faster)
- **Quality**: 100% requirement coverage, zero compliance errors
- **Cost**: ~$0.15-0.25 per request vs 30-45 min staff time

### Four Agents
1. **Prior Auth Coordinator** (Manager, gpt-4o)
   - Orchestrates workflow
   - Manages data flow
   - Ensures quality
2. **Payer Policy Analyzer** (Worker, gpt-4o-mini)
   - Extracts authorization requirements
   - Identifies approval criteria
   - Lists required documentation
3. **Clinical Evidence Compiler** (Worker, gpt-4o-mini)
   - Organizes clinical evidence
   - Maps to approval criteria
   - Assesses evidence strength
4. **Auth Submission Generator** (Worker, gpt-4o)
   - Creates submission documents
   - Ensures payer compliance
   - Produces ready-to-submit packages

### Files
```
blueprints/local/healthcare/
├── prior-authorization-agent.yaml           Blueprint definition
├── agents/
│   ├── prior-auth-coordinator.yaml          Manager agent
│   ├── payer-policy-analyzer.yaml           Policy extraction worker
│   ├── clinical-evidence-compiler.yaml      Evidence compilation worker
│   └── auth-submission-generator.yaml       Submission generation worker
├── PRIOR_AUTH_README.md                     Full documentation (comprehensive)
├── DEPLOYMENT_SUMMARY.md                    Deployment guide
├── QUICKSTART.md                            Getting started guide
└── BLUEPRINT_INDEX.md                       This file
```

### Documentation Guide
| Document | Purpose | Read Time | For Whom |
|----------|---------|-----------|----------|
| QUICKSTART.md | Get started in 5 minutes | 5 min | Everyone |
| PRIOR_AUTH_README.md | Complete reference | 30 min | Everyone |
| DEPLOYMENT_SUMMARY.md | Technical deployment | 20 min | Technical |

### Key Sections in PRIOR_AUTH_README.md

**What to Read First:**
- Problem (Why 45+ minutes is a problem)
- Approach (How three agents solve it)

**Then Deep Dive:**
- Capabilities (What each agent does)
- Usage Examples (Real scenarios with outputs)
- Technical Architecture (How it works)

**For Implementation:**
- Error Handling (What if something goes wrong)
- Quality Metrics (How to measure success)
- Deployment Notes (How to set up)

### Quick Start (5 Minutes)

```bash
# 1. Create the blueprint
cd blueprints/local/healthcare
bp create prior-authorization-agent.yaml

# 2. Test with sample authorization
bp chat <blueprint-id>

# 3. Provide:
# - Payer policy document
# - Patient clinical records
# - Insurance information

# 4. Get:
# - Policy requirements extracted
# - Clinical evidence organized
# - Submission-ready package
```

### Use Cases
- Routine authorization requests (simple, fast)
- Complex cases with missing evidence (identifies gaps)
- Urgent authorizations (expedited processing)
- Multiple payers (standardized approach)

### When to Use
**YES, use when:**
- Processing routine prior authorization requests
- Need to reduce administrative time
- Want consistent, compliant submissions
- Have clear policy documents and clinical records

**NO, don't use when:**
- Case requires clinical judgment beyond evidence review
- Clinical records are incomplete/unavailable
- Policy documents are in non-English language
- Exception/appeals processing needed (separate system)

### Agent Configuration

| Agent | Model | Temp | Purpose | Speed |
|-------|-------|------|---------|-------|
| Coordinator | gpt-4o | 0.3 | Orchestration | Medium |
| Policy Analyzer | gpt-4o-mini | 0.2 | Extraction | Fast |
| Evidence Compiler | gpt-4o-mini | 0.2 | Organization | Fast |
| Submission Gen | gpt-4o | 0.3 | Generation | Medium |

**Why these choices:**
- Manager uses gpt-4o for complex orchestration reasoning
- Workers use gpt-4o-mini for cost-efficient extraction/organization
- Submission generator uses gpt-4o for quality writing
- Low temperatures (0.2-0.3) for deterministic, consistent output

### Success Metrics

Track these to measure impact:

| Metric | Baseline | Target | Timeline |
|--------|----------|--------|----------|
| Time per auth | 45-120 min | <5 min | Week 1 |
| Completeness | 85-90% | >99% | Week 2 |
| Approval rate | 92-95% | >97% | Week 4 |
| Resubmission | 8-10% | <2% | Week 4 |
| Staff satisfaction | Baseline | >80% | Week 2 |

### Implementation Steps

1. **Deploy**: Upload YAML files to Agent Studio
2. **Test**: Run with sample authorization
3. **Validate**: Check output quality
4. **Integrate**: Connect to your systems
5. **Train**: Brief staff on usage
6. **Monitor**: Track metrics
7. **Optimize**: Gather feedback and iterate

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Policy analysis incomplete | Provide full policy text, not summary |
| Evidence gaps identified | Obtain missing clinical records |
| Submission format errors | Verify payer form version is current |
| Long processing time | Check input size, try section-by-section |

See QUICKSTART.md "Troubleshooting" section for detailed solutions.

### Integration Points

**Inputs From:**
- Electronic Health Records (EHR)
- Document Management Systems
- Insurance databases
- Patient portals

**Outputs To:**
- Payer submission systems
- Authorization tracking databases
- Clinical workflows
- Staff notification systems

### Support & Resources

| Need | Where to Go |
|------|------------|
| Quick start | QUICKSTART.md |
| Complete docs | PRIOR_AUTH_README.md |
| Deployment | DEPLOYMENT_SUMMARY.md |
| Technical help | support@lyzr.ai |
| Bug reports | [GitHub Issues] |
| Feedback | blueprint-feedback@lyzr.ai |

### Important Notes

**What it does:**
- ✅ Extracts policy requirements
- ✅ Organizes clinical evidence
- ✅ Creates submission documents
- ✅ Ensures compliance
- ✅ Reduces time 10-25x

**What it doesn't do:**
- ❌ Provide clinical judgment
- ❌ Modify clinical information
- ❌ Override medical decision-making
- ❌ Guarantee approval (clinical merit dependent)
- ❌ Appeal denied authorizations

**Safeguards:**
- Never modifies clinical data
- Flags all gaps clearly
- Requires human review
- Maintains audit trail
- Transparent about limitations

---

## Related Healthcare Blueprints (Coming Soon)

### Blueprint 1: Initial Patient Screener
**Purpose**: Pre-qualification assessment for healthcare services
**Status**: In Development (Q1 2025)
**Agents**: 3-4 specialized agents

**Capabilities:**
- Patient intake information extraction
- Medical history assessment
- Service eligibility determination
- Risk stratification

---

### Blueprint 2: Insurance Verification Agent
**Purpose**: Real-time insurance eligibility checking
**Status**: In Development (Q1 2025)
**Agents**: 2-3 specialized agents

**Capabilities:**
- Coverage verification
- Benefits extraction
- Co-pay/deductible determination
- Prior authorization requirements check

---

### Blueprint 3: Clinical Notes Summarizer
**Purpose**: Automated clinical documentation summarization
**Status**: In Development (Q2 2025)
**Agents**: 1-2 specialized agents

**Capabilities:**
- Progress note summarization
- Discharge summary generation
- Clinical extract production
- Documentation standardization

---

### Blueprint 4: Discharge Planner
**Purpose**: Post-hospital discharge coordination
**Status**: In Development (Q2 2025)
**Agents**: 5+ specialized agents

**Capabilities:**
- Discharge planning
- Follow-up appointment scheduling
- Medication reconciliation
- Care transition documentation

---

## Blueprint Comparison Matrix

| Feature | Prior Auth | Patient Screener | Insurance Verify | Notes Summary | Discharge Plan |
|---------|-----------|-----------------|------------------|---------------|----------------|
| Agents | 4 | 3-4 | 2-3 | 1-2 | 5+ |
| Complexity | Medium | Medium | Low | Low | High |
| Status | ✅ Ready | 🚧 Dev | 🚧 Dev | 🚧 Dev | 🚧 Dev |
| Primary Role | Authorization | Intake | Verification | Documentation | Coordination |

---

## How to Use This Index

### For Quick Overview
1. Read "Blueprint 5" section above
2. Review "Key Metrics" and "Quick Start"
3. Check "When to Use" section

### For Implementation
1. Read QUICKSTART.md (5 min)
2. Read PRIOR_AUTH_README.md Problem & Approach sections
3. Follow DEPLOYMENT_SUMMARY.md checklist
4. Test with sample authorization

### For Troubleshooting
1. See "Common Issues & Solutions" table above
2. Read QUICKSTART.md troubleshooting section
3. Check PRIOR_AUTH_README.md error handling section
4. Contact support@lyzr.ai

### For Integration
1. Review "Integration Points" section
2. See DEPLOYMENT_SUMMARY.md integration section
3. Design data mapping for your systems
4. Build adapters if needed

### For Advanced Usage
1. Read DEPLOYMENT_SUMMARY.md advanced section
2. Review agent YAML files for implementation details
3. Check agent instructions for specific logic
4. See API integration examples in QUICKSTART.md

---

## File Purpose Reference

| File | Purpose | Audience | Read Time |
|------|---------|----------|-----------|
| prior-authorization-agent.yaml | Root blueprint definition | Developers | 2 min |
| prior-auth-coordinator.yaml | Manager orchestration agent | Technical | 5 min |
| payer-policy-analyzer.yaml | Policy extraction worker | Technical | 5 min |
| clinical-evidence-compiler.yaml | Evidence compilation worker | Technical | 5 min |
| auth-submission-generator.yaml | Submission generation worker | Technical | 5 min |
| QUICKSTART.md | Getting started guide | End Users | 5 min |
| PRIOR_AUTH_README.md | Complete documentation | Everyone | 30 min |
| DEPLOYMENT_SUMMARY.md | Deployment & tech guide | Technical | 20 min |
| BLUEPRINT_INDEX.md | This reference guide | Everyone | 10 min |

---

## Version & Support

- **Blueprint Suite**: v1.0
- **Prior Auth Agent**: v1.0
- **Last Updated**: January 2025
- **Maintained By**: Lyzr Blueprint Team
- **Status**: Production Ready

### Support Contacts
- **Questions**: support@lyzr.ai
- **Issues**: [GitHub Issues]
- **Feedback**: blueprint-feedback@lyzr.ai
- **Community**: [Lyzr Community Forum]

---

## Next Steps

**To get started:**
1. Read QUICKSTART.md (5 minutes)
2. Deploy the blueprint
3. Test with sample authorization
4. Review output quality
5. Integrate with your systems
6. Track success metrics

**For detailed learning:**
1. Read PRIOR_AUTH_README.md sections in order
2. Study agent YAML files
3. Review technical architecture
4. Understand error handling approach

**To implement:**
1. Follow DEPLOYMENT_SUMMARY.md
2. Complete pre-deployment checklist
3. Execute deployment steps
4. Validate in staging environment
5. Roll out to production

---

**Ready to get started?** → Start with QUICKSTART.md

**Need full details?** → Read PRIOR_AUTH_README.md

**Planning implementation?** → See DEPLOYMENT_SUMMARY.md
