# Schema Gates Proposal: Robust Blueprint Creation Flow

## Problem Statement

The current UI flow sends a flat array of `agent_specs[]` to the Create API without:
1. Explicit manager-worker relationships (`sub_agents`)
2. Orchestration pattern type
3. Client-side tree validation
4. Schema validation between stages

The SDK CLI approach is more robust because it:
- Uses Pydantic schemas with strict validation
- Builds explicit hierarchy (`sub_agents` references)
- Creates workers FIRST, then manager with `managed_agents`
- Constructs ReactFlow tree before API call
- Validates at multiple stages

## Proposed Solution: Zod Schema Gates

### 1. Stage-Based Schemas

Each stage has its own Zod schema that validates input/output:

```typescript
// src/lib/schemas/architecture.ts
import { z } from "zod";

export const AgentInfoSchema = z.object({
  name: z.string().min(1).max(100),
  purpose: z.string().min(1),
  type: z.enum(["manager", "worker"]),
});

export const ArchitectureOutputSchema = z.object({
  pattern: z.enum(["hierarchical", "sequential", "parallel", "hybrid"]),
  manager: AgentInfoSchema.extend({ type: z.literal("manager") }),
  workers: z.array(AgentInfoSchema.extend({ type: z.literal("worker") })).min(1),
  delegation_strategy: z.string().optional(),
});

export type ArchitectureOutput = z.infer<typeof ArchitectureOutputSchema>;
```

```typescript
// src/lib/schemas/agent-spec.ts
import { z } from "zod";

export const AgentSpecSchema = z.object({
  // Identity
  name: z.string().min(1).max(100),
  description: z.string().min(1),
  filename: z.string().regex(/^[a-z0-9-]+\.yaml$/),

  // Hierarchy
  is_manager: z.boolean(),
  sub_agents: z.array(z.string()).optional(), // Filenames of workers

  // Persona
  role: z.string().min(15).max(80),
  goal: z.string().min(50).max(300),
  context: z.string().optional(),
  output_format: z.string().optional(),
  examples: z.string().optional(),

  // Instructions
  instructions: z.string().min(100),
  usage_description: z.string().optional(), // Required for workers

  // LLM Config
  model: z.string().default("gpt-4o"),
  temperature: z.number().min(0).max(1).default(0.3),
  top_p: z.number().min(0).max(1).default(1.0),
  response_format: z.enum(["text", "json_object"]).default("text"),

  // Features
  features: z.array(z.string()).default([]),
});

export const ManagerSpecSchema = AgentSpecSchema.extend({
  is_manager: z.literal(true),
  sub_agents: z.array(z.string()).min(1), // Must have at least 1 worker
});

export const WorkerSpecSchema = AgentSpecSchema.extend({
  is_manager: z.literal(false),
  usage_description: z.string().min(1), // Required for workers
});

export type AgentSpec = z.infer<typeof AgentSpecSchema>;
export type ManagerSpec = z.infer<typeof ManagerSpecSchema>;
export type WorkerSpec = z.infer<typeof WorkerSpecSchema>;
```

```typescript
// src/lib/schemas/blueprint.ts
import { z } from "zod";
import { ManagerSpecSchema, WorkerSpecSchema } from "./agent-spec";

export const BlueprintRequestSchema = z.object({
  session_id: z.string().uuid(),

  // Explicit hierarchy
  manager: ManagerSpecSchema,
  workers: z.array(WorkerSpecSchema).min(1),

  // Orchestration metadata
  pattern: z.enum(["hierarchical", "sequential", "parallel", "hybrid"]),
  delegation_strategy: z.string().optional(),
});

export type BlueprintRequest = z.infer<typeof BlueprintRequestSchema>;
```

### 2. Stage Transition Gates

```typescript
// src/lib/validation/gates.ts
import { SafeParseReturnType } from "zod";
import { ArchitectureOutputSchema } from "../schemas/architecture";
import { ManagerSpecSchema, WorkerSpecSchema } from "../schemas/agent-spec";
import { BlueprintRequestSchema } from "../schemas/blueprint";

/**
 * Gate 1: Architecture → Build
 * Validates architecture output before starting agent crafting
 */
export function validateArchitectureGate(data: unknown): Gate<ArchitectureOutput> {
  const result = ArchitectureOutputSchema.safeParse(data);
  return {
    valid: result.success,
    data: result.success ? result.data : undefined,
    errors: result.success ? [] : formatZodErrors(result.error),
  };
}

/**
 * Gate 2: Agent Craft → Approval
 * Validates each agent spec before showing to user for approval
 */
export function validateAgentGate(
  data: unknown,
  isManager: boolean
): Gate<AgentSpec> {
  const schema = isManager ? ManagerSpecSchema : WorkerSpecSchema;
  const result = schema.safeParse(data);
  return {
    valid: result.success,
    data: result.success ? result.data : undefined,
    errors: result.success ? [] : formatZodErrors(result.error),
  };
}

/**
 * Gate 3: All Agents → Create Blueprint
 * Validates complete blueprint request before API call
 */
export function validateBlueprintGate(data: unknown): Gate<BlueprintRequest> {
  const result = BlueprintRequestSchema.safeParse(data);
  return {
    valid: result.success,
    data: result.success ? result.data : undefined,
    errors: result.success ? [] : formatZodErrors(result.error),
  };
}

interface Gate<T> {
  valid: boolean;
  data?: T;
  errors: string[];
}

function formatZodErrors(error: z.ZodError): string[] {
  return error.issues.map(issue =>
    `${issue.path.join(".")}: ${issue.message}`
  );
}
```

### 3. Enhanced Builder Flow

```typescript
// src/lib/hooks/use-builder.ts (enhanced)

// After architecture is approved
const approveArchitecture = useCallback(async () => {
  // Gate 1: Validate architecture output
  const gate = validateArchitectureGate(architecture);
  if (!gate.valid) {
    setError(`Architecture validation failed: ${gate.errors.join(", ")}`);
    return;
  }

  // Store validated architecture with pattern type
  setValidatedArchitecture(gate.data);
  setBuilderStage("crafting");
  craftNextAgent();
}, [architecture]);

// After each agent is crafted
const craftNextAgent = useCallback(async () => {
  const result = await callCrafter(...);

  // Gate 2: Validate agent spec
  const isManager = currentAgentIndex === 0;
  const gate = validateAgentGate(result.agent_yaml, isManager);

  if (!gate.valid) {
    // Auto-retry with validation errors as context
    if (retryCount < MAX_RETRIES) {
      return craftNextAgent(retryCount + 1, gate.errors);
    }
    setError(`Agent validation failed: ${gate.errors.join(", ")}`);
    return;
  }

  // Add validated agent to specs
  setAgentSpecs(prev => [...prev, gate.data]);
  setBuilderStage("craft-review");
}, []);

// When creating blueprint
const createBlueprint = useCallback(async () => {
  // Build explicit request with hierarchy
  const manager = agentSpecs.find(a => a.is_manager);
  const workers = agentSpecs.filter(a => !a.is_manager);

  // Ensure manager has sub_agents
  const managerWithWorkers = {
    ...manager,
    sub_agents: workers.map(w => w.filename),
  };

  const request = {
    session_id: sessionId,
    manager: managerWithWorkers,
    workers: workers,
    pattern: validatedArchitecture.pattern,
    delegation_strategy: validatedArchitecture.delegation_strategy,
  };

  // Gate 3: Validate complete blueprint request
  const gate = validateBlueprintGate(request);
  if (!gate.valid) {
    setError(`Blueprint validation failed: ${gate.errors.join(", ")}`);
    return;
  }

  // Send validated request
  const response = await fetch("/api/builder/create", {
    method: "POST",
    body: JSON.stringify(gate.data),
  });

  // ...
}, [agentSpecs, validatedArchitecture]);
```

### 4. API Changes

The Create API should accept the new explicit structure:

```typescript
// Current (flat array)
{
  session_id: "xxx",
  agent_specs: [
    { name: "Manager", is_manager: true, ... },
    { name: "Worker1", is_manager: false, ... },
    { name: "Worker2", is_manager: false, ... },
  ]
}

// Proposed (explicit hierarchy)
{
  session_id: "xxx",
  manager: {
    name: "Manager",
    is_manager: true,
    sub_agents: ["worker-1.yaml", "worker-2.yaml"],
    ...
  },
  workers: [
    { name: "Worker1", is_manager: false, filename: "worker-1.yaml", ... },
    { name: "Worker2", is_manager: false, filename: "worker-2.yaml", ... },
  ],
  pattern: "hierarchical",
  delegation_strategy: "Task-based delegation with worker specialization"
}
```

### 5. Benefits

| Benefit | Description |
|---------|-------------|
| **Type Safety** | Zod schemas provide runtime type validation |
| **Clear Hierarchy** | `sub_agents` explicitly links manager to workers |
| **Pattern Preserved** | Orchestration pattern sent to Create API |
| **Early Failure** | Invalid data caught at gate, not API |
| **Auto-Retry Context** | Validation errors fed back to crafter for retry |
| **Consistent with SDK** | Mirrors CLI's Pydantic-based approach |

### 6. Implementation Order

1. **Phase 1: Schemas** (Day 1)
   - Create Zod schemas in `src/lib/schemas/`
   - Add validation utilities in `src/lib/validation/`

2. **Phase 2: Gates** (Day 2)
   - Add gate validation to `use-builder.ts`
   - Update auto-retry to use validation context

3. **Phase 3: API Changes** (Day 3)
   - Update Create API to accept new structure
   - Backend builds tree from explicit hierarchy

4. **Phase 4: Testing** (Day 4)
   - Update E2E tests for new flow
   - Add unit tests for schemas

---

## Comparison: Before vs After

### Before (Current)

```
Define → Architect → Craft → Approve → Create
           ↓                    ↓
       Pattern               Flat array
       (lost)              [is_manager flag only]
```

### After (Proposed)

```
Define → Architect → Craft → Approve → Create
           ↓            ↓               ↓
     Gate 1:        Gate 2:         Gate 3:
     Pattern       Agent spec     Blueprint request
     validated     validated      validated
           ↓            ↓               ↓
     Pattern       sub_agents      Complete
     preserved     linked          hierarchy
```

---

## Summary

The SDK CLI approach is more robust because it:
1. Uses Pydantic schemas with strict validation
2. Maintains explicit hierarchy via `sub_agents`
3. Creates workers first, then manager with `managed_agents`
4. Validates at multiple stages

By adding Zod schema gates to the UI flow, we can achieve the same level of robustness while providing:
- Type-safe validation at each stage
- Explicit manager-worker relationships
- Pattern preservation through the entire flow
- Better auto-retry with validation context
