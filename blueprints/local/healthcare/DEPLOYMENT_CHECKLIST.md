# Insurance Eligibility Verifier - Deployment Checklist

## Pre-Deployment

### Prerequisites
- [ ] Environment variables configured:
  - [ ] `LYZR_API_KEY` - Agent API key
  - [ ] `BLUEPRINT_BEARER_TOKEN` - Blueprint API token
  - [ ] `LYZR_ORG_ID` - Organization ID
- [ ] Network access to:
  - [ ] agent-prod.studio.lyzr.ai (Agent API)
  - [ ] pagos-prod.studio.lyzr.ai (Blueprint API)
- [ ] YAML files downloaded/cloned:
  - [ ] insurance-eligibility-verifier.yaml
  - [ ] agents/eligibility-coordinator.yaml
  - [ ] agents/coverage-checker.yaml
  - [ ] agents/benefits-analyzer.yaml
  - [ ] agents/patient-responsibility-calculator.yaml

### Validation
- [ ] All YAML files present in correct locations
- [ ] No file path issues or missing references
- [ ] YAML indentation correct (2 spaces)
- [ ] All agent files referenced in blueprint manifest

## Deployment Steps

### Step 1: Validate Configuration
```bash
bp validate blueprints/local/healthcare/insurance-eligibility-verifier.yaml
```
- [ ] No YAML syntax errors
- [ ] All file paths resolve
- [ ] Agent configurations valid
- [ ] Blueprint structure correct

### Step 2: Create Blueprint
```bash
bp create blueprints/local/healthcare/insurance-eligibility-verifier.yaml
```
- [ ] Manager agent created successfully
- [ ] Coverage Checker worker created
- [ ] Benefits Analyzer worker created
- [ ] Patient Responsibility Calculator worker created
- [ ] Blueprint created and linked
- [ ] Blueprint ID received and saved

### Step 3: Verify Deployment
```bash
bp get <blueprint-id> --format json
```
- [ ] Blueprint metadata correct
- [ ] Manager agent ID recorded
- [ ] Worker agent IDs recorded
- [ ] All agents linked to blueprint
- [ ] Status shows ACTIVE

### Step 4: Test Manager Agent
```bash
bp eval <manager-agent-id> \
  "Verify coverage for John Smith, Aetna member, office visit on 01/20/2025"
```
- [ ] Agent responds without errors
- [ ] Output format matches specification
- [ ] All required fields present
- [ ] Agent follows instructions

### Step 5: Test Worker Agents (Optional)
```bash
# Test Coverage Checker
bp eval <coverage-checker-id> \
  "Verify Aetna PPO coverage, member 123456789, service date 01/20/2025"

# Test Benefits Analyzer
bp eval <benefits-analyzer-id> \
  "Analyze office visit benefits under Aetna PPO with $1500 deductible, $500 met"

# Test Patient Responsibility Calculator
bp eval <patient-responsibility-calculator-id> \
  "Calculate patient cost: $40 copay, $500 deductible remaining, $6000 OOP max"
```
- [ ] Coverage Checker returns coverage baseline
- [ ] Benefits Analyzer identifies service coverage
- [ ] Calculator computes costs accurately

## Post-Deployment Configuration

### System Integration
- [ ] Connect to patient intake system
- [ ] Configure eligibility request queue
- [ ] Set up result export to EHR
- [ ] Configure patient communication system
- [ ] Set up metrics dashboard

### Workflow Setup
- [ ] Create eligibility verification intake form
- [ ] Configure request routing
- [ ] Set up result review workflow
- [ ] Create escalation procedures
- [ ] Document approval authorities

### Staff Training
- [ ] Train staff on new eligibility system
- [ ] Create quick reference guides
- [ ] Document common scenarios
- [ ] Establish feedback mechanism
- [ ] Set up support channel

### Monitoring & Optimization
- [ ] Set up metrics tracking
  - [ ] Verification time per request
  - [ ] Accuracy metrics
  - [ ] Coverage verification success rate
  - [ ] Pre-auth identification rate
  - [ ] User satisfaction

- [ ] Configure alerts for:
  - [ ] Failed verifications
  - [ ] High patient costs
  - [ ] Pre-authorization required
  - [ ] Terminated coverage

- [ ] Weekly review process:
  - [ ] Check verification accuracy
  - [ ] Review failed cases
  - [ ] Identify improvement areas
  - [ ] Update runbooks

## Troubleshooting Guide

### Issue: Validation Fails
**Problem:** `bp validate` returns errors
```
Error: File not found or invalid path
Error: YAML syntax error at line X
```

**Solution:**
1. Verify file locations:
   ```bash
   ls -la blueprints/local/healthcare/
   ls -la blueprints/local/healthcare/agents/
   ```

2. Check YAML syntax:
   ```bash
   python -m yaml blueprints/local/healthcare/insurance-eligibility-verifier.yaml
   ```

3. Verify indentation (use 2 spaces, not tabs):
   ```bash
   cat -A blueprints/local/healthcare/insurance-eligibility-verifier.yaml
   ```

### Issue: Agent Creation Fails
**Problem:** Blueprint creation times out or returns error
```
Error: Failed to create agent 'Eligibility Coordinator'
Error: API returned 401 Unauthorized
```

**Solution:**
1. Verify environment variables:
   ```bash
   echo $LYZR_API_KEY
   echo $BLUEPRINT_BEARER_TOKEN
   echo $LYZR_ORG_ID
   ```

2. Test API connectivity:
   ```bash
   curl -H "X-API-Key: $LYZR_API_KEY" \
     https://agent-prod.studio.lyzr.ai/v3/health
   ```

3. Check model availability:
   ```bash
   bp list --models
   ```

4. Try creating single agent first:
   ```bash
   bp create blueprints/local/healthcare/agents/coverage-checker.yaml
   ```

### Issue: Agent Doesn't Follow Instructions
**Problem:** Agent output doesn't match expected format
```
Response is rambling or unstructured
Missing required output fields
Contradicts benefit information
```

**Solution:**
1. Review agent instructions carefully
2. Test with simple, clear input
3. Check temperature setting (should be 0.2)
4. Re-run model evaluation
5. If persistent, contact support with example

### Issue: Coverage Verification Returns No Data
**Problem:** Agent can't verify coverage
```
UNABLE_TO_VERIFY
No active coverage found
Member ID not found
```

**Solution:**
1. Verify member ID matches insurance card exactly
2. Check coverage effective dates
3. Try with different service date
4. Confirm carrier supports online verification
5. Fall back to phone verification process

### Issue: Cost Calculation Inaccurate
**Problem:** Patient cost estimate doesn't match actual
```
Estimate: $100, Actual: $250
Missing deductible component
Coinsurance calculation wrong
```

**Solution:**
1. Verify deductible/OOP met amounts are current
2. Confirm service is in-network
3. Check if service code maps correctly to benefit
4. Verify plan hasn't changed since verification
5. Request actual EOB from insurance for comparison

## Rollback Plan

If deployment issues occur:

### Quick Rollback
1. Delete agents:
   ```bash
   bp delete --id <manager-agent-id>
   bp delete --id <coverage-checker-id>
   bp delete --id <benefits-analyzer-id>
   bp delete --id <calculator-agent-id>
   ```

2. Delete blueprint:
   ```bash
   bp delete --id <blueprint-id>
   ```

3. Revert to manual process
4. Document issues encountered

### Gradual Rollback
1. Set blueprint to PRIVATE visibility
2. Test with small subset of requests
3. Gradually increase usage
4. Monitor accuracy metrics
5. Maintain parallel manual process during testing

## Success Criteria

### Functional
- [ ] All agents create without errors
- [ ] Blueprint deploys successfully
- [ ] Manager orchestrates workers correctly
- [ ] Output format matches specification
- [ ] Edge cases handled properly

### Performance
- [ ] Verification completes in <1 minute per request
- [ ] System handles 10+ concurrent requests
- [ ] No timeout errors
- [ ] Consistent response times

### Accuracy
- [ ] Coverage verification 98%+ accurate
- [ ] Pre-auth detection 100% catch rate
- [ ] Cost calculations 99%+ accurate
- [ ] No incorrect patient financial counseling

### User Satisfaction
- [ ] Staff comfortable with new process
- [ ] Clear output easy to explain to patients
- [ ] No major implementation blockers
- [ ] Positive feedback from early users

## Sign-Off

### Technical Lead
- [ ] YAML files valid and complete
- [ ] Deployment successful
- [ ] All agents functioning
- [ ] Performance acceptable

**Name:** ___________________  **Date:** ___________

### Healthcare Operations
- [ ] Workflow integrated
- [ ] Staff trained
- [ ] Metrics configured
- [ ] Ready for production

**Name:** ___________________  **Date:** ___________

### Compliance
- [ ] HIPAA compliant
- [ ] Data privacy verified
- [ ] Audit trail configured
- [ ] Regulatory approved

**Name:** ___________________  **Date:** ___________

## Post-Deployment Support

### First Week
- [ ] Daily check-ins with staff
- [ ] Monitor error rates
- [ ] Address user feedback
- [ ] Fine-tune thresholds

### First Month
- [ ] Weekly accuracy audits
- [ ] Performance optimization
- [ ] Staff feedback sessions
- [ ] Process refinement

### Ongoing
- [ ] Monthly metric review
- [ ] Quarterly stakeholder review
- [ ] Annual compliance audit
- [ ] Continuous improvement

## Contact Information

**Technical Support:**
- Email: support@lyzr.ai
- Slack: #blueprints-support
- Documentation: docs.lyzr.ai

**Healthcare Operations:**
- Project Manager: [Name]
- Healthcare IT Lead: [Name]
- Chief Compliance Officer: [Name]

**Escalation Path:**
1. Consult troubleshooting guide
2. Contact Technical Support
3. Open GitHub issue if bug suspected
4. Escalate to Lyzr engineering team if critical

---

**Last Updated:** 2025-01-15
**Version:** 1.0
**Owner:** Healthcare Blueprint Team
