# UI Backlog

## Pending Features

### Stage Navigation
**Priority**: Medium
**Complexity**: High

Currently, the stage indicators serve as a progress indicator only. Users cannot click to navigate between stages.

**Current behavior**:
- Stages show as visually clickable (hover effects)
- Clicking stages does nothing
- Flow is linear/wizard-style

**Desired behavior**:
- Allow clicking on completed stages to view their content
- Optional: Allow editing previous stages and continuing from there

**Implementation requirements**:
1. Add `goToStage(stageId)` method to `useBuilder` hook
2. Track separate state for "viewing stage" vs "actual progress stage"
3. Show content from previous stages in read-only mode
4. Add UI to distinguish viewing vs editing modes
5. Handle data dependencies:
   - Stage 1 (Define): Statement input
   - Stage 3 (Design): Requires architecture data
   - Stage 4 (Build): Requires architecture + track approved agents
   - Stage 5 (Launch): Requires all agents approved

**Files to modify**:
- `src/lib/hooks/use-builder.ts` - Add goToStage method and viewing state
- `src/components/shell/app-shell.tsx` - Wire up onStageClick handler
- `src/components/shell/stage-header.tsx` - Update click behavior
- `src/components/screens/review-screen.tsx` - Add read-only mode indicator

---

## Completed Features

### Setup Screen with API Credentials
- Welcome screen for API key input
- Cookie storage (30 days)
- JWT token validation with countdown timer

### Blueprint Metadata Display
- Shows Blueprint ID, Manager ID, Org ID, share_type, created_at
- Removed duplicate CTA button

### Manager Chat
- Functional chat with manager agent on final screen
- Calls `/api/builder/chat` endpoint

### Stage Reset Fix
- Stage indicators properly reset when creating new blueprint

---

## UI Parity with Claude Code Experience

**Priority**: High
**Complexity**: High

### Gap Analysis

| Dimension | Claude Code | Current UI | Gap |
|-----------|-------------|------------|-----|
| **Validation** | 25+ field validators, content rules | 3 boolean checks | Critical |
| **Field Control** | All fields editable | 3 dropdown selections | Critical |
| **Determinism** | YAML → identical output | AI generates differently | High |
| **Guidance** | 6 specialized skills | None | High |
| **Artifacts** | Git-versioned YAML | Database only | Medium |
| **Error Messages** | Field-level with fixes | HTTP status only | High |

### User Requirements

- **Scope**: Full Parity - all 25+ fields, all validation, YAML export/import
- **AI Role**: AI as Generator + Validation (keep generation, add validation)
- **Priorities**: Validation, Field Control, Guidance, YAML Export/Import

### Implementation Phases

#### Phase 1: Validation System
Port SDK Pydantic rules to Zod schemas:
- `name`: 1-100 chars
- `role`: 15-80 chars, no generic terms (worker, helper, bot, agent, assistant)
- `goal`: 50-300 chars
- `instructions`: min 50 chars, 10 words
- `temperature`: 0-1 (not 0-2)
- Placeholder detection: TODO, FIXME, XXX, [placeholder], {placeholder}
- Weak pattern detection: "be helpful", "you are an AI assistant"

#### Phase 2: Field-Level Control (AgentEditor)
Allow editing all 25+ agent fields before approval:
- Essential: name, description, role, goal
- Technical: model, temperature, top_p, response_format
- Context: instructions, context, examples
- Features: features[], tools[], web_search

#### Phase 3: Guidance System
Port Claude Code skill knowledge to UI:
- Field tooltips with character limits
- Model recommender (manager vs worker, task type)
- Quality scoring (0-100)
- Smart defaults based on context

#### Phase 4: YAML Export/Import
- Export blueprint to YAML matching SDK schema
- Import YAML to edit in UI
- Version comparison

### Detailed Design

See plan file: `~/.claude/plans/fluffy-crunching-lecun.md`
