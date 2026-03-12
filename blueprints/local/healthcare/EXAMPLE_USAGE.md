# Care Transition Coordinator - Example Usage

This document shows practical examples of how to use the Care Transition Coordinator blueprint in real discharge scenarios.

## Example 1: Post-Surgical Patient Discharge

### Patient Scenario
- 72-year-old male
- Admitted for knee replacement surgery
- 3-day hospital stay
- Comorbidities: Hypertension, Type 2 diabetes, mild kidney disease
- On 8 medications at home
- Lives with spouse, good social support

### Input to Coordinator

```
PATIENT DISCHARGE INFORMATION

Patient: John Smith | Age: 72 | MRN: 12345678
Admission Date: 2025-01-13 | Discharge Date: 2025-01-16 | LOS: 3 days

DISCHARGE DIAGNOSIS
- Right total knee replacement (primary)
- Hypertension (on treatment)
- Type 2 diabetes (on treatment)
- Mild chronic kidney disease (stage 3b)

HOSPITAL COURSE
Patient admitted for elective right total knee replacement. Surgery on 1/13
without complications. Post-op course uncomplicated. Pain well-controlled.
Patient ambulating with walker. Dressing clean and dry. No signs of infection.
Patient and spouse educated on post-op care. Discharged to home with VNA.

MEDICATIONS PRE-ADMISSION
1. Lisinopril 10mg daily (hypertension)
2. Amlodipine 5mg daily (hypertension)
3. Metformin 1000mg BID (diabetes)
4. Glyburide 5mg daily (diabetes)
5. Atorvastatin 20mg daily (cholesterol)
6. Aspirin 81mg daily (cardioprotection)
7. Omeprazole 20mg daily (acid reflux)
8. Multivitamin daily

MEDICATIONS IN-HOSPITAL
1. Lisinopril 10mg daily
2. Amlodipine 5mg daily
3. Metformin 1000mg BID (held day of surgery, restarted)
4. Glyburide 5mg daily (held day of surgery, restarted)
5. Atorvastatin 20mg daily
6. Aspirin 81mg daily
7. Omeprazole 20mg daily
8. Hydromorphone 2-4mg IV Q4H PRN (post-op pain)
9. Enoxaparin 40mg SC daily (DVT prophylaxis)
10. Cephalexin 500mg QID (surgical prophylaxis)

PROPOSED DISCHARGE MEDICATIONS
1. Lisinopril 10mg daily
2. Amlodipine 5mg daily
3. Metformin 1000mg BID (restart, but hold with contrast if imaging needed)
4. Glyburide 5mg daily
5. Atorvastatin 20mg daily
6. Aspirin 81mg daily (resume after 10 days post-op)
7. Omeprazole 20mg daily
8. Oxycodone 5mg Q6H PRN (post-op pain)
9. Enoxaparin 40mg SC daily x 14 days (DVT prophylaxis)
10. Cephalexin 500mg QID x 5 days (surgical prophylaxis)
11. Docusate 100mg daily (stool softener)

PHYSICAL EXAM AT DISCHARGE
- Alert and oriented x3
- BP 138/82, HR 78, RR 16, O2 sat 98% RA
- Knee dressing clean, dry, intact
- No calf swelling, normal color
- Good distal pulses
- Able to bear weight with walker, good pain control
- No signs of infection

PATIENT DEMOGRAPHICS
Age: 72 | Sex: M | Lives with: Spouse
Social: Retired, no transportation barriers, health literate
Allergies: NKDA (no known drug allergies)

AVAILABLE PROVIDERS
- PCP: Dr. Sarah Johnson (Internal Medicine) - same clinic as hospital
- Orthopedic Surgeon: Dr. Michael Chen (did surgery)
- Cardiologist: Dr. Patricia Martinez (established relationship)
- Insurance: Medicare with supplemental coverage
```

### How to Use Coordinator

```bash
# Create instance with patient information
coordinator = client.get("coordinator-agent-id")

input_text = """
Patient: John Smith, 72M
Admission: 1/13-1/16 for right knee replacement
Diagnosis: Post-op right TKA, HTN, DM2, CKD3b
[Include full clinical information above]
"""

# Send to coordinator
response = coordinator.chat(input_text)

# The coordinator will:
# 1. Send to Discharge Summary Generator
#    → Produces summary with post-op instructions, precautions
# 2. Send to Medication Reconciler
#    → Identifies that aspirin is appropriately held x10 days
#    → Flags metformin precaution with imaging
#    → Verifies no dangerous interactions
# 3. Send to Follow-up Scheduler
#    → Schedules orthopedic follow-up: 2-3 weeks
#    → Schedules VNA for wound check: 48 hours
#    → PCP follow-up: 2 weeks
# 4. Integrates all outputs
```

### Expected Output

```
===== CARE TRANSITION COORDINATION PACKAGE =====

PATIENT INFORMATION
Name: John Smith | Age: 72 | MRN: 12345678

===== DISCHARGE SUMMARY =====
[Discharge summary with provider and patient versions]

PROVIDER SUMMARY
Admission: Right total knee replacement - uncomplicated post-op course.
Patient: Discharged to home with spouse support, VNA ordered, excellent
functional recovery. Continue current medications with modifications below.

PATIENT-FRIENDLY SUMMARY
You had knee replacement surgery. You did great! Take pain medicine as needed.
Do NOT put full weight on leg for 2 weeks. Ice and elevate knee. Dressing
should stay clean and dry. Call if redness, swelling, or warmth develops.

===== MEDICATION SAFETY ALERT =====
Critical Issues: 0
Major Interactions: 0
VERIFIED SAFE
✓ All discharge medications appropriate for post-operative knee replacement
✓ No dangerous interactions identified
✓ Hold aspirin appropriately x10 days post-op
⚠️ Metformin note: Hold if contrast imaging needed; resume 48 hours after imaging

[Full medication reconciliation report]

===== FOLLOW-UP CARE SCHEDULE =====

URGENT (Schedule Within 3-7 Days)
1. Visiting Nurse Association - Wound Check
   Reason: Post-operative wound assessment
   Timing: 48 hours after discharge (1/18)
   Contact: (555) 123-4567

ROUTINE (Schedule Within 7-14 Days)
1. Orthopedic Surgeon (Dr. Michael Chen) - Post-op Follow-up
   Reason: Assess knee range of motion, healing
   Timing: 2-3 weeks after discharge (1/30-2/6)
   Contact: (555) 234-5678
   Special: Bring crutches or walker, wear loose clothing

STANDARD (Schedule Within 30 Days)
1. Primary Care Physician (Dr. Sarah Johnson) - General Follow-up
   Reason: Monitor post-operative recovery, manage chronic conditions
   Timing: 2 weeks after discharge (1/30)
   Contact: (555) 345-6789

PATIENT EDUCATION CHECKLIST
Before patient leaves hospital, ensure:
☑ Reviewed discharge summary with patient and spouse
☑ Reviewed medication list (8 continue, 2 new, 1 stopped, dates)
☑ Discussed activity restrictions: No full weight x2 weeks
☑ Provided written wound care instructions
☑ Discussed pain management and when to call
☑ Addressed transportation to VNA appointments
☑ Verified insurance coverage for PT visits
☑ Provided 24-hour contact number for questions

DISCHARGE READINESS ASSESSMENT
✓ Clinical Documentation: Complete
✓ Medication Safety: Verified
✓ Follow-up Scheduled: Yes (3 appointments booked)
✓ Patient Understanding: Education completed

RED FLAGS REQUIRING MONITORING
- Monitor for DVT: Call if calf swelling, warmth, or pain
- Monitor for infection: Call if fever, redness, or drainage
- Metformin with contrast: Remember to hold if imaging needed

COORDINATION COMPLETED - Ready for Patient Discharge
```

### Clinical Impact

- **Safe Discharge**: All medication interactions verified, aspirin appropriately held
- **Clear Instructions**: Patient understands post-op restrictions and warning signs
- **Scheduled Follow-up**: VNA visit tomorrow, orthopedic follow-up planned
- **Provider Continuity**: Orthopedic and PCP coordinated for optimal recovery
- **Reduced Risk**: Clear instructions reduce infection risk and readmission risk

---

## Example 2: Complex Medical Patient Discharge

### Patient Scenario
- 68-year-old female
- Admitted for acute heart failure exacerbation
- 5-day hospital stay
- Comorbidities: HFrEF, AFib, CKD stage 4, diabetes
- On 12 medications at baseline
- Lives alone, some functional limitations
- Limited health literacy

### Key Coordination Points

**Medication Reconciliation Challenge**
- Pre-admission: 12 medications
- In-hospital: 15 medications (added diuretics, antibiotics)
- Discharge: Need to adjust to new regimen (diuretics increased, added SGLT2i)
- **Reconciler identifies**: New heart failure medications, diuretic dose increase, timing of electrolyte monitoring

**Follow-up Challenge**
- High-risk for 30-day readmission
- Lives alone, limited transportation
- Needs close cardiology follow-up and labs
- **Scheduler identifies**: Urgent cardiology (3-5 days), frequent labs, home health referral needed

**Discharge Summary Challenge**
- Complex medication changes
- Multiple new diagnoses (acute on chronic heart failure)
- Patient with limited health literacy
- **Generator creates**: Very clear patient-friendly version with pictures/diagrams, simplified medication list

### Coordinator Workflow

```
INPUT: Complex HF discharge with multiple medication changes
  ↓
DISCHARGE SUMMARY GENERATOR
→ Creates comprehensive summary with simplified patient version
→ Flags key points: New diuretics, new medications, daily weights
  ↓
MEDICATION RECONCILER
→ Identifies 8 medication changes
→ Flags potential hyperkalemia risk (ACE-I + K-sparing diuretic)
→ Verifies no warfarin interactions (patient on apixaban)
→ Grades issue: MAJOR - recommend potassium monitoring
  ↓
FOLLOW-UP SCHEDULER
→ Identifies barriers: Lives alone, limited transportation
→ Schedules urgent cardiology (3-5 days)
→ Schedules home health nursing
→ Arranges lab work at local lab (near home)
→ Identifies: Needs rides to cardiology - social work referral
  ↓
INTEGRATED PACKAGE
→ Manager flags MAJOR medication issue for physician review
→ All urgent appointments scheduled before discharge
→ Social work involved for transportation solutions
→ Patient education materials translated to Spanish
```

---

## Example 3: Uncomplicated Discharge

### Patient Scenario
- 45-year-old male
- Admitted for acute appendicitis
- 2-day hospital stay
- No significant comorbidities
- On 2 medications at home
- Good social support, health literate

### Coordinator Workflow (Fast Path)

```
INPUT: Simple appendectomy, 2-day stay, no complications
  ↓
DISCHARGE SUMMARY
→ Quick turnaround: Simple surgery summary
→ Patient-friendly: Take pain meds, avoid heavy lifting 2 weeks
  ↓
MEDICATION RECONCILIATION
→ Minimal issues: Continue home meds, add antibiotics x10 days
→ No interactions: Simple approval
  ↓
FOLLOW-UP SCHEDULING
→ One appointment: Surgeon follow-up 2 weeks
→ One instruction: No strenuous activity x2 weeks
  ↓
INTEGRATED PACKAGE
→ Everything integrated in <30 minutes
→ Patient ready to go home
→ All instructions clear
```

---

## Integration Examples

### Integration with EHR

```python
# Pull data from EHR
from your_ehr_system import get_discharge_data

patient_data = get_discharge_data(mrn="12345678")

# Format for coordinator
discharge_input = f"""
PATIENT: {patient_data['name']}, {patient_data['age']}
ADMISSION: {patient_data['admit_date']} to {patient_data['discharge_date']}
DIAGNOSIS: {patient_data['diagnosis']}

PRE-ADMISSION MEDICATIONS:
{patient_data['home_medications']}

IN-HOSPITAL MEDICATIONS:
{patient_data['hospital_meds']}

DISCHARGE MEDICATIONS:
{patient_data['discharge_meds']}

[Complete clinical summary]
"""

# Send to coordinator
coordinator = client.get("coordinator-id")
response = coordinator.chat(discharge_input)

# Save outputs
save_to_ehr(patient_data['mrn'], response)
```

### Integration with Discharge Coordinator Workflow

```python
# After coordinator produces integrated package
package = coordinator.output

# Extract key information
discharge_summary = package.sections['DISCHARGE_SUMMARY']
medication_alerts = package.sections['MEDICATION_ALERTS']
follow_ups = package.sections['FOLLOW_UP_SCHEDULE']

# Coordinator books appointments
for appointment in follow_ups['appointments']:
    book_appointment(
        patient_mrn=patient.mrn,
        provider=appointment['provider'],
        date=appointment['recommended_date'],
        urgency=appointment['urgency']
    )

# Send to patient portal
patient_portal.post_discharge_materials(
    patient_id=patient.mrn,
    summary=discharge_summary['patient_version'],
    medications=medication_alerts['medication_list'],
    appointments=follow_ups['patient_copy'],
    warning_signs=discharge_summary['warning_signs']
)

# Notify providers
notify_pcp(patient.mrn, discharge_summary)
notify_specialists(patient.mrn, discharge_summary)
```

---

## Real-Time Coordination Example

### Scenario: Physician Orders Discharge at 2:00 PM

```
2:00 PM - Physician order: "Patient ready for discharge"
  ↓
2:02 PM - Discharge coordinator collects all clinical data
  ↓
2:05 PM - Sends to Coordinator: Full discharge package
  ↓
2:08 PM - Discharge Summary Generator produces summary
         (includes provider review version and patient version)
  ↓
2:12 PM - Medication Reconciler reviews medications
         (identifies 2 drug interactions, recommends change)
  ↓
2:15 PM - Physician approves medication change
  ↓
2:18 PM - Follow-up Scheduler creates appointment schedule
         (coordinates with 3 specialty offices)
  ↓
2:25 PM - Manager integrates all outputs
         (quality assurance check)
  ↓
2:28 PM - Complete discharge package ready
         (all critical issues resolved)
  ↓
2:30 PM - Discharge coordinator:
         • Reviews patient education with patient
         • Books confirmed follow-up appointments
         • Sends materials to patient portal
         • Gives discharge copies to patient
  ↓
2:45 PM - Patient safely discharged home
```

---

## Success Metrics Tracking

### Example Output for Measurement

```
DISCHARGE COORDINATION SUMMARY

Patient: John Doe | MRN: 123456
Discharge Date: 2025-01-20 | Time to Coordination: 28 minutes

MEDICATION SAFETY
- Total medications: 8
- Discrepancies found: 2
- Interactions identified: 0 (critical), 0 (major), 1 (moderate)
- Recommendations: All addressed

FOLLOW-UP COMPLIANCE
- Total appointments scheduled: 3
- Urgent (3-7 days): 1
- Routine (7-14 days): 1
- Standard (14-30 days): 1
- Patient barriers identified: 1 (transportation)
- Solutions provided: Yes (van service arranged)

PATIENT EDUCATION
- Discharge summary reviewed: Yes
- Medications reviewed: Yes
- Activity restrictions understood: Yes
- Warning signs reviewed: Yes
- Questions answered: Yes

QUALITY ASSURANCE
- Documentation completeness: 100%
- Consistency checks: Passed
- Red flags: 0
- Clinical review required: No

READMISSION RISK REDUCTION
- Early follow-up scheduled: Yes (within 7 days)
- Medication safety verified: Yes
- Comprehensive discharge summary: Yes
- Barrier identification: Yes
- Estimated readmission risk reduction: 25-30%
```

---

## Troubleshooting Examples

### Issue: Medication Interaction Identified

**Scenario**: Patient on warfarin, discharged with new antibiotic that increases warfarin levels

```
MEDICATION RECONCILER OUTPUT
⚠️ CRITICAL INTERACTION IDENTIFIED
Drug A: Warfarin 5mg daily
Drug B: Ciprofloxacin 500mg BID (new)

Interaction: Ciprofloxacin increases warfarin effect
Risk: Increased bleeding risk
Recommendation: MUST CHANGE BEFORE DISCHARGE
- Option 1: Use different antibiotic (not fluoroquinolone)
- Option 2: If must use cipro, reduce warfarin by 25-50%
        Monitor INR in 3 days

MANAGER RESPONSE:
- Flags for physician review immediately
- Waits for physician decision
- Updates medication list before discharge
- Reschedules medication reconciliation if needed
- Patient education updated
- Does not discharge until resolved
```

### Issue: Patient with Language Barrier

**Scenario**: Spanish-speaking patient with limited English

```
FOLLOW-UP SCHEDULER OUTPUT
⚠️ LANGUAGE BARRIER IDENTIFIED
Patient speaks: Spanish (primary), Limited English

Recommendations:
1. Interpreter needed for follow-up appointments:
   - Phone number: Spanish-speaking interpreter
   - Schedule interpreter at each appointment

2. Written materials needed in Spanish:
   - Discharge summary (Spanish)
   - Medication list (Spanish)
   - Follow-up instructions (Spanish)
   - Warning signs (Spanish with pictures)

3. Contact number with Spanish speakers:
   - Provide number that has Spanish-speaking staff

MANAGER RESPONSE:
- Flags language barrier
- Ensures all materials translated
- Coordinates interpreter services
- Includes in patient education verification
```

---

## Best Practices

1. **Timing**: Start discharge coordination as soon as patient cleared for discharge
2. **Completeness**: Ensure all three workers complete before final discharge
3. **Review**: Physician should review medication recommendations and red flags
4. **Implementation**: Discharge coordinator should book all appointments before patient leaves
5. **Education**: Complete patient education using discharge coordinator before discharge
6. **Follow-up**: Track readmission rates and adjust process based on outcomes

---

## Getting Started

To use these examples:

1. Prepare patient discharge information per the input format
2. Submit to Care Transition Coordinator agent
3. Review integrated output for completeness
4. Implement recommendations before discharge
5. Track readmission rates and appointment compliance
6. Adjust instructions based on clinical feedback

For more information, see:
- CARE_TRANSITION_README.md - Clinical background
- BLUEPRINT_SUMMARY.md - Technical architecture
- VALIDATION_CHECKLIST.md - Pre-deployment checklist
