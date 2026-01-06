# Blueprint Builder: Improvement Suggestions

## Problem Analysis

After extensive testing, I identified several critical issues affecting both test reliability and user experience:

### Core Issues Discovered

1. **Non-deterministic AI Behavior**: The AI agent sometimes asks follow-up questions indefinitely instead of proceeding to architecture design, even when given comprehensive answers.

2. **HITL Parsing from Text**: The backend embeds HITL JSON in markdown text rather than using dedicated SSE events, requiring client-side parsing with potential for race conditions.

3. **State Persistence Bugs**: UI state (like `isEditing`) persists across mode changes, causing wrong buttons to appear.

4. **Long LLM Response Times**: Each conversation turn takes 10-30 seconds due to real API calls, making full journey tests take 2-5+ minutes.

---

## Suggestions for Faster Test Suite

### 1. Deterministic Test Mode (Recommended)

Add a `test_mode` parameter that makes the agent deterministic:

```python
# api/routes/chat.py
@router.post("/stream")
async def stream_chat(chat_request: ChatRequest, request: Request):
    if settings.test_mode:
        # Use fixed responses for predictable flow
        yield from test_mode_responses(chat_request.message)
        return
    # Normal flow...
```

**Test mode behaviors:**
- First message → Ask 2 standard questions
- Second message → Emit `confirm_architecture` HITL immediately
- Approve → Emit `review_agent` HITL for each agent
- All approved → Emit `create_blueprint`

### 2. Backend Mock Fixtures

Create reusable mock fixtures for the FastAPI backend:

```typescript
// e2e/fixtures/mock-backend.ts
export class MockBackend {
  private responses: Map<string, SSEResponse[]> = new Map();

  // Predefined journey stages
  static quickJourney() {
    return new MockBackend()
      .onMessage(/.*/, exploreResponse)
      .onMessage(/approve|proceed/, architectureHitl)
      .onHitlApprove('confirm_architecture', agentHitl)
      .onHitlApprove('review_agent', blueprintCreated);
  }

  start(port = 8001) { /* Start mock server */ }
}

// Usage in tests
test('quick journey', async ({ page }) => {
  const mock = MockBackend.quickJourney();
  await mock.start(8001);
  // Test runs in seconds instead of minutes
});
```

### 3. Snapshot Testing for UI States

Instead of testing the full journey, test individual states:

```typescript
// e2e/snapshots/stages.spec.ts
test.describe('Stage Snapshots', () => {
  test('explore stage with conversation', async ({ page }) => {
    // Inject state directly
    await page.evaluate(() => {
      window.__TEST_STATE__ = {
        currentStage: 2,
        screenType: 'review',
        isConversational: true,
        reviewContent: '# Questions\n1. What is your use case?',
      };
    });
    await page.goto('/');
    await expect(page).toHaveScreenshot('explore-conversation.png');
  });

  test('architecture hitl', async ({ page }) => {
    await page.evaluate(() => {
      window.__TEST_STATE__ = {
        currentStage: 3,
        hitl: {
          type: 'confirm_architecture',
          preview: { /* architecture data */ }
        },
      };
    });
    await page.goto('/');
    await expect(page.getByRole('button', { name: /approve/i })).toBeVisible();
  });
});
```

### 4. API Response Caching

Cache LLM responses for repeated test runs:

```python
# api/services/cache.py
class ResponseCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir

    def get_or_fetch(self, message_hash: str, fetch_fn):
        cache_file = self.cache_dir / f"{message_hash}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        response = fetch_fn()
        cache_file.write_text(json.dumps(response))
        return response

# Enable with: CACHE_RESPONSES=true pytest
```

### 5. Parallel Test Sharding

Run different journey variations in parallel:

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    {
      name: 'journey-happy-path',
      testMatch: '**/journey-happy.spec.ts',
    },
    {
      name: 'journey-revise',
      testMatch: '**/journey-revise.spec.ts',
    },
    // Each can run on separate workers
  ],
});
```

---

## Suggestions for Better User Journey

### 1. Explicit Stage Transitions via HITL

Instead of parsing JSON from text, emit dedicated SSE events:

```python
# Current (problematic)
yield {"event": "text", "data": "...markdown with ```json HITL```"}

# Proposed (reliable)
yield {"event": "text", "data": "...clean markdown..."}
yield {"event": "hitl", "data": {"type": "confirm_architecture", ...}}
```

**Backend Change** (`api/routes/chat.py`):
```python
async def event_generator():
    full_response = ""
    async for chunk in inference_service.stream(...):
        full_response += chunk
        yield {"event": "text", "data": json.dumps({"content": chunk})}

    # Parse and emit HITL as separate event (already exists but may not fire)
    clean_text, structured = hitl_service.parse_response(full_response)
    if structured and structured.action == AgentAction.HITL:
        yield {"event": "hitl", "data": json.dumps(structured.hitl.model_dump())}
```

### 2. Progress Indicator with Stages

Show users exactly where they are and what's coming:

```
[1. Define] → [2. Explore ✓] → [3. Design (current)] → [4. Build] → [5. Launch]
              │                 │
              │                 └─ "I'm designing your architecture..."
              └─ "Answering 2 of 3 questions..."
```

**Frontend Component**:
```tsx
// Already exists but could show more detail
<StageHeader
  stage={3}
  substep="Designing architecture..."
  progress={2} // of 3 sub-steps
/>
```

### 3. "Skip to Architecture" Button

Allow power users to bypass Explore stage:

```tsx
// In explore conversation
{questionCount > 2 && (
  <Button variant="outline" onClick={() => sendMessage("Proceed to architecture now")}>
    Skip Questions → Design Architecture
  </Button>
)}
```

### 4. Estimated Time Display

Set expectations for LLM response times:

```tsx
{isLoading && (
  <div className="text-muted-foreground">
    <Loader2 className="animate-spin" />
    <span>Thinking... (~10-30 seconds)</span>
  </div>
)}
```

### 5. Agent Prompt Improvements

Update the agent's system prompt to be more decisive:

```python
# Current agent behavior: Asks many questions
# Proposed: More structured flow

SYSTEM_PROMPT = """
You are a Blueprint Builder assistant. Follow this EXACT flow:

## Stage 2: Explore (MAX 2 conversation turns)
- Ask up to 3 clarifying questions in your FIRST response
- After receiving answers, IMMEDIATELY proceed to Stage 3
- NEVER ask more than 2 rounds of questions

## Stage 3: Design
- Propose architecture and emit HITL JSON immediately
- Format: ```json {"action": "hitl", "hitl": {...}} ```

CRITICAL: Do not ask questions indefinitely. Move forward after 2 exchanges.
"""
```

### 6. Conversation History Summary

Show users what they've discussed:

```tsx
<Accordion>
  <AccordionItem title="Conversation Summary">
    <ul>
      <li>Use case: Customer support automation</li>
      <li>Volume: 500 daily inquiries</li>
      <li>Constraints: GPT-4, English only</li>
    </ul>
  </AccordionItem>
</Accordion>
```

---

## Architecture Improvements

### 1. Decouple HITL from Text Streaming

```
Current Flow:
┌──────────┐    text chunks + embedded JSON    ┌──────────┐
│ Backend  │ ────────────────────────────────► │ Frontend │
└──────────┘                                   └──────────┘
                                                     │
                                                Parse JSON from text
                                                     │
                                                Update UI state

Proposed Flow:
┌──────────┐    text chunks (clean)            ┌──────────┐
│ Backend  │ ────────────────────────────────► │ Frontend │
│          │    hitl event (structured)        │          │
│          │ ────────────────────────────────► │          │
└──────────┘                                   └──────────┘
                                                     │
                                                Handle separate events
```

### 2. State Machine for Journey Flow

```typescript
// lib/hooks/use-journey-state-machine.ts
const journeyMachine = createMachine({
  initial: 'define',
  states: {
    define: {
      on: { SUBMIT: 'explore' }
    },
    explore: {
      on: {
        HITL_ARCHITECTURE: 'design',
        MESSAGE: 'explore', // Stay in explore
      }
    },
    design: {
      on: {
        APPROVE: 'build',
        REVISE: 'design',
      }
    },
    build: {
      on: {
        AGENT_APPROVED: [
          { target: 'build', cond: 'hasMoreAgents' },
          { target: 'launch' }
        ],
        REVISE: 'build',
      }
    },
    launch: {
      type: 'final'
    }
  }
});
```

### 3. Backend Session State

Store journey progress on the backend:

```python
# api/models/session.py
class JourneySession(BaseModel):
    session_id: str
    stage: Literal['define', 'explore', 'design', 'build', 'launch']
    explore_questions_asked: int = 0
    architecture_approved: bool = False
    agents_approved: list[str] = []
    total_agents: int = 0

    def can_proceed_to_design(self) -> bool:
        return self.explore_questions_asked >= 1

# In chat handler
if session.explore_questions_asked >= 2 and "proceed" in message.lower():
    # Force transition to design
    session.stage = 'design'
```

---

## Priority Order

| Priority | Suggestion | Impact | Effort |
|----------|-----------|--------|--------|
| 1 | Fix SSE HITL events (separate from text) | High | Medium |
| 2 | Add test mode for deterministic flow | High | Low |
| 3 | Update agent prompt for decisiveness | High | Low |
| 4 | Add mock backend fixtures | Medium | Medium |
| 5 | State machine for journey | Medium | High |
| 6 | Response caching for tests | Medium | Low |
| 7 | Progress indicators | Low | Low |
| 8 | Skip button for power users | Low | Low |

---

## Quick Wins (Implement Today)

1. **Already Fixed**: `ActionGroup` state reset on mode change ✅

2. **CRITICAL: Set JSON Output Mode for Builder Agent**

   The builder agent (ID: `695aad9ba45696ac999e18cf`) must be configured with:

   ```json
   {
     "response_format": {"type": "json_object"}
   }
   ```

   And the system prompt must specify the exact JSON schema:

   ```
   You MUST always respond with valid JSON in this exact format:

   For conversation responses:
   {"action": "continue", "message": "Your response here"}

   For architecture proposal:
   {"action": "hitl", "hitl": {"type": "confirm_architecture", "title": "...", ...}}

   For agent review:
   {"action": "hitl", "hitl": {"type": "review_agent", "title": "...", "preview": {...}}}

   NEVER output plain text. ALWAYS output valid JSON.
   ```

3. **Agent Prompt Update**: Add explicit instructions to proceed after 2 exchanges

4. **Test Mode Flag**: Add `TEST_MODE=true` env var that uses fixed responses

5. **SSE Event Fix**: Ensure HITL is emitted as separate event, not just text

---

## Summary

The core issues are:
1. **AI non-determinism** → Fix with explicit prompts or test mode
2. **HITL in text** → Fix with dedicated SSE events
3. **Slow tests** → Fix with mocks + caching
4. **UI state bugs** → Fixed with `useEffect` reset

Implementing the top 3-4 suggestions would dramatically improve both test reliability and user experience.
