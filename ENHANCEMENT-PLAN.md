# UI Enhancement Plan

> Focused enhancements for the Blueprint Builder UI

---

## Design Principles

1. **Fully conversational** - Users only provide natural language input
2. **AI decides everything** - Model, temperature, architecture, agent config
3. **Quality gates in background** - Validation and retry happen silently
4. **Only quality-passed content shown** - Users see polished results
5. **Markdown-based review** - No badges, clean readable content

---

## Approved Enhancements

### 1. Suggestion Agent for Revisions

**Goal**: When user wants to revise, show 8 contextual suggestion labels using existing option component.

**Implementation**:
- New API endpoint: `POST /api/builder/suggest`
- Fast JSON-output agent generates 8 revision suggestions
- Reuse `OptionCard` component from guided-chat layout
- User clicks a suggestion or types custom feedback

```
┌─────────────────────────────────────────────────────────────┐
│ What would you like to change?                              │
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ Add detailed    │ │ Include edge    │ │ Make output     │ │
│ │ process steps   │ │ case handling   │ │ format clearer  │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ Add constraints │ │ Improve goal    │ │ Clarify role    │ │
│ │ and guardrails  │ │ specificity     │ │ description     │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│ ┌─────────────────┐ ┌─────────────────┐                     │
│ │ Change agent    │ │ Other...        │                     │
│ │ approach        │ │                 │                     │
│ └─────────────────┘ └─────────────────┘                     │
│                                                             │
│ Or describe your changes:                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. Streaming Loader Agent

**Goal**: Entertaining, contextual loading text during wait times.

**Implementation**:
- Very fast model (gpt-4o-mini or haiku)
- Streams funny/contextual text while user waits
- Knows current stage context (designing, crafting agent name, creating)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    ◐ ◓ ◑ ◒                                  │
│                                                             │
│   "Teaching your Ticket Classifier the ancient art of      │
│    inbox archaeology... 🔍"                                 │
│                                                             │
│   "Almost there! Just convincing it that 'URGENT!!!' in    │
│    all caps doesn't always mean urgent..."                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Streaming behavior**:
- Start streaming immediately when loading begins
- New witty line every 3-5 seconds
- Context-aware (mentions agent name, stage, domain)
- Stops when actual content is ready

---

### 3. Unified Stage Progress

**Goal**: Single progress indicator with N/M for build phase.

**Current**: 5 separate stages (Define, Explore, Design, Build, Complete)
**New**: 3 unified stages with sub-progress

```
┌─────────────────────────────────────────────────────────────┐
│  ✓ Define  ───────  ● Build (2/4)  ───────  ○ Complete     │
└─────────────────────────────────────────────────────────────┘
```

**Stages**:
1. **Define** - User fills guided chat statement
2. **Build** - Architecture + all agents (shows N/M progress)
   - Includes: designing, design-review, crafting, craft-review
   - Progress: "Build (0/4)" → "Build (1/4)" → ... → "Build (4/4)"
3. **Complete** - Blueprint created

---

## Implementation Details

### Suggestion Agent

**Backend**: `api/routes/builder.py`

```python
@router.post("/suggest")
async def get_suggestions(request: SuggestRequest) -> SuggestResponse:
    """Generate 8 revision suggestions based on current agent spec."""

    agent = SuggestionAgent(
        model="gpt-4o-mini",  # Fast
        temperature=0.7,      # Creative
        response_format="json_object"
    )

    prompt = f"""
    Given this agent specification, generate exactly 8 short revision suggestions.

    Agent: {request.agent_name}
    Role: {request.role}
    Goal: {request.goal}
    Instructions preview: {request.instructions[:500]}

    Return JSON: {{"suggestions": ["label1", "label2", ...]}}

    Make suggestions:
    - Short (2-5 words each)
    - Actionable
    - Context-aware
    - Diverse (cover different aspects)
    """

    return await agent.generate(prompt)
```

**Frontend**: Reuse existing components

```tsx
// In review-screen.tsx when revision mode is active
<div className="grid grid-cols-3 gap-3">
  {suggestions.map((label) => (
    <OptionCard
      key={label}
      label={label}
      selected={selectedSuggestion === label}
      onClick={() => handleSuggestionClick(label)}
    />
  ))}
</div>
```

---

### Loader Agent

**Backend**: `api/routes/builder.py`

```python
@router.get("/loader-stream")
async def stream_loader(stage: str, context: str):
    """Stream entertaining loading messages."""

    agent = LoaderAgent(
        model="gpt-4o-mini",
        temperature=0.9,  # Very creative
        stream=True
    )

    prompt = f"""
    Generate a witty, fun one-liner about: {context}
    Stage: {stage}

    Be clever, use relevant emojis, keep it under 100 chars.
    """

    async def generate():
        while True:
            line = await agent.generate(prompt)
            yield f"data: {json.dumps({'text': line})}\n\n"
            await asyncio.sleep(4)  # New line every 4 seconds

    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Frontend**: `src/components/builder/streaming-loader.tsx`

```tsx
export function StreamingLoader({ stage, context }: Props) {
  const [text, setText] = useState("");

  useEffect(() => {
    const eventSource = new EventSource(
      `/api/builder/loader-stream?stage=${stage}&context=${encodeURIComponent(context)}`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setText(data.text);
    };

    return () => eventSource.close();
  }, [stage, context]);

  return (
    <div className="text-center py-12">
      <Spinner className="mx-auto mb-4" />
      <p className="text-muted-foreground animate-pulse">{text}</p>
    </div>
  );
}
```

---

### Unified Progress

**Update**: `src/components/builder/step-indicator.tsx`

```tsx
type UnifiedStage = "define" | "build" | "complete";

interface Props {
  stage: UnifiedStage;
  buildProgress?: { current: number; total: number };
}

export function StepIndicator({ stage, buildProgress }: Props) {
  return (
    <div className="flex items-center justify-center gap-4">
      <StepDot
        label="Define"
        status={stage === "define" ? "current" : "complete"}
      />

      <StepConnector completed={stage !== "define"} />

      <StepDot
        label={buildProgress ? `Build (${buildProgress.current}/${buildProgress.total})` : "Build"}
        status={
          stage === "define" ? "upcoming" :
          stage === "build" ? "current" : "complete"
        }
      />

      <StepConnector completed={stage === "complete"} />

      <StepDot
        label="Complete"
        status={stage === "complete" ? "current" : "upcoming"}
      />
    </div>
  );
}
```

**Hook update**: `src/lib/hooks/use-builder.ts`

```typescript
// Compute unified stage
const unifiedStage: UnifiedStage = useMemo(() => {
  if (builderStage === "define") return "define";
  if (builderStage === "complete") return "complete";
  return "build";  // designing, design-review, crafting, craft-review, creating
}, [builderStage]);

// Compute build progress
const buildProgress = useMemo(() => {
  if (unifiedStage !== "build") return undefined;

  // Total = 1 (architecture) + N (agents)
  const total = 1 + totalAgents;

  // Current progress
  let current = 0;
  if (builderStage === "design-review") current = 1;  // Architecture done
  if (builderStage === "crafting" || builderStage === "craft-review") {
    current = 1 + currentAgentIndex + (builderStage === "craft-review" ? 1 : 0);
  }
  if (builderStage === "creating") current = total;

  return { current, total };
}, [unifiedStage, builderStage, totalAgents, currentAgentIndex]);
```

---

## Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `api/routes/builder.py` | Add `/suggest` and `/loader-stream` endpoints |
| `src/components/builder/streaming-loader.tsx` | Streaming loader component |
| `src/components/builder/revision-suggestions.tsx` | Suggestions UI using OptionCard |

### Modified Files

| File | Changes |
|------|---------|
| `src/components/builder/step-indicator.tsx` | Unified 3-stage progress |
| `src/lib/hooks/use-builder.ts` | Add `unifiedStage`, `buildProgress`, suggestion state |
| `src/components/screens/review-screen.tsx` | Integrate loader + suggestions |
| `ui/src/app/api/builder/suggest/route.ts` | Next.js API route proxy |
| `ui/src/app/api/builder/loader-stream/route.ts` | Next.js SSE proxy |

---

## Priority Order

| # | Enhancement | Effort | Impact |
|---|-------------|--------|--------|
| 1 | Unified stage progress | 2h | Medium |
| 2 | Streaming loader agent | 4h | High (delight) |
| 3 | Suggestion agent | 4h | High (UX) |

**Total estimated effort**: ~10 hours

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Wait time perception | Reduced (entertaining loaders) |
| Revision quality | Higher (contextual suggestions) |
| Progress clarity | Improved (unified N/M view) |
