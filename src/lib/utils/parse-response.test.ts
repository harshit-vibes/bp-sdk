import { describe, it, expect } from "vitest";
import { repairJson, parseStructuredResponse } from "./parse-response";

describe("repairJson", () => {
  it("should return valid JSON unchanged", () => {
    const input = '{"action": "continue", "message": "Hello"}';
    expect(repairJson(input)).toBe(input);
  });

  it("should escape newlines inside string values", () => {
    const input = '{"action": "continue", "message": "Hello\nWorld"}';
    const expected = '{"action": "continue", "message": "Hello\\nWorld"}';
    expect(repairJson(input)).toBe(expected);
  });

  it("should preserve escaped newlines", () => {
    const input = '{"action": "continue", "message": "Hello\\nWorld"}';
    expect(repairJson(input)).toBe(input);
  });

  it("should handle multiple newlines", () => {
    const input = '{"message": "Line1\nLine2\nLine3"}';
    const expected = '{"message": "Line1\\nLine2\\nLine3"}';
    expect(repairJson(input)).toBe(expected);
  });

  it("should escape carriage returns", () => {
    const input = '{"message": "Hello\rWorld"}';
    const expected = '{"message": "Hello\\rWorld"}';
    expect(repairJson(input)).toBe(expected);
  });

  it("should escape tabs", () => {
    const input = '{"message": "Hello\tWorld"}';
    const expected = '{"message": "Hello\\tWorld"}';
    expect(repairJson(input)).toBe(expected);
  });

  it("should not escape newlines outside strings", () => {
    const input = '{\n  "action": "continue",\n  "message": "Hello"\n}';
    expect(repairJson(input)).toBe(input);
  });

  it("should handle complex nested JSON with newlines in strings", () => {
    const input = `{
  "action": "hitl",
  "message": "Review the architecture:
1. Manager
2. Workers",
  "hitl": {"type": "confirm_architecture"}
}`;
    const result = repairJson(input);
    // Should be valid JSON after repair
    expect(() => JSON.parse(result)).not.toThrow();
    const parsed = JSON.parse(result);
    expect(parsed.action).toBe("hitl");
    expect(parsed.message).toContain("1. Manager");
  });

  it("should handle escaped quotes inside strings", () => {
    const input = '{"message": "He said \\"hello\\" to me"}';
    expect(repairJson(input)).toBe(input);
  });
});

describe("parseStructuredResponse", () => {
  describe("JSON mode (pure JSON)", () => {
    it("should parse valid JSON continue response", () => {
      const input = '{"action": "continue", "message": "What problem are you solving?"}';
      const result = parseStructuredResponse(input);
      expect(result.message).toBe("What problem are you solving?");
      expect(result.hitl).toBeNull();
      expect(result.blueprint_yaml).toBeNull();
    });

    it("should parse JSON hitl response", () => {
      const input = JSON.stringify({
        action: "hitl",
        message: "Review the architecture",
        hitl: {
          type: "confirm_architecture",
          title: "Review Blueprint Architecture",
          preview: { pattern: "manager_workers" },
        },
      });
      const result = parseStructuredResponse(input);
      expect(result.message).toBe("Review the architecture");
      expect(result.hitl).not.toBeNull();
      expect(result.hitl?.type).toBe("confirm_architecture");
    });

    it("should parse JSON create_blueprint response", () => {
      const input = JSON.stringify({
        action: "create_blueprint",
        message: "Creating your blueprint!",
        blueprint_yaml: {
          name: "Test Blueprint",
          description: "A test",
        },
      });
      const result = parseStructuredResponse(input);
      expect(result.message).toBe("Creating your blueprint!");
      expect(result.blueprint_yaml).toEqual({
        name: "Test Blueprint",
        description: "A test",
      });
    });

    it("should repair and parse JSON with newlines in message", () => {
      // This simulates what happens when LLM streams JSON with actual newlines
      const input = `{"action": "continue", "message": "To design the best blueprint, I need:

1. **Problem**: What are you solving?
2. **Users**: Who will use it?
3. **Output**: What should it produce?"}`;

      const result = parseStructuredResponse(input);
      expect(result.message).toContain("To design the best blueprint");
      expect(result.message).toContain("1. **Problem**");
      expect(result.hitl).toBeNull();
    });

    it("should parse HITL with markdown in message", () => {
      const input = `{
  "action": "hitl",
  "message": "## Architecture Designed

I've designed a **customer support** blueprint with:
- 1 Manager
- 2 Workers",
  "hitl": {
    "type": "confirm_architecture",
    "title": "Review Architecture",
    "preview": {"pattern": "manager_workers"}
  }
}`;
      const result = parseStructuredResponse(input);
      expect(result.message).toContain("## Architecture Designed");
      expect(result.hitl?.type).toBe("confirm_architecture");
    });
  });

  describe("Legacy markdown mode", () => {
    it("should extract HITL from markdown code block", () => {
      const input = `Here's the architecture I designed:

\`\`\`json
{"action": "hitl", "hitl": {"type": "confirm_architecture", "title": "Review"}}
\`\`\`

Please review above.`;

      const result = parseStructuredResponse(input);
      expect(result.hitl?.type).toBe("confirm_architecture");
      // Message should have the code block removed
      expect(result.message).not.toContain("```json");
    });

    it("should handle escaped characters in legacy markdown", () => {
      const input = `Check this:

\`\`\`json
{\\"action\\": \\"hitl\\", \\"hitl\\": {\\"type\\": \\"review_agent\\"}}
\`\`\``;

      // Note: This format uses double-escaped which won't parse correctly
      // The legacy mode expects single-escaped
      const result = parseStructuredResponse(input);
      // This case may not parse correctly, but shouldn't crash
      expect(result.message).toBeDefined();
    });
  });

  describe("Fallback behavior", () => {
    it("should return original text when no structured response found", () => {
      const input = "This is just plain text with no JSON";
      const result = parseStructuredResponse(input);
      expect(result.message).toBe(input);
      expect(result.hitl).toBeNull();
      expect(result.blueprint_yaml).toBeNull();
    });

    it("should handle empty string", () => {
      const result = parseStructuredResponse("");
      expect(result.message).toBe("");
      expect(result.hitl).toBeNull();
    });

    it("should handle invalid JSON gracefully", () => {
      const input = '{"action": "continue", "message": broken}';
      const result = parseStructuredResponse(input);
      // Should fall through to returning original text
      expect(result.message).toBe(input);
    });
  });

  describe("Real-world scenarios", () => {
    it("should handle typical first response from agent", () => {
      const input = `{
  "action": "continue",
  "message": "Great! To design the best blueprint for you, I need to understand:

1. **What specific problem** are you trying to solve?
2. **Who will use** this blueprint?
3. **What inputs** will it receive and **what outputs** should it produce?

Please provide these details so I can design an effective solution."
}`;

      const result = parseStructuredResponse(input);
      expect(result.message).toContain("To design the best blueprint");
      expect(result.message).toContain("1. **What specific problem**");
      expect(result.hitl).toBeNull();
    });

    it("should handle architecture HITL response", () => {
      const input = `{
  "action": "hitl",
  "message": "## Architecture Designed

I've designed a **customer support automation** blueprint with:

- 1 Manager (Ticket Orchestrator)
- 2 Workers (Classifier, Responder)

Review the details below.",
  "hitl": {
    "type": "confirm_architecture",
    "title": "Review Blueprint Architecture",
    "work_summary": "Designed multi-agent architecture for customer support.",
    "info_items": [],
    "preview": {
      "pattern": "manager_workers",
      "manager": {"name": "Ticket Orchestrator", "purpose": "Routes tickets"},
      "workers": [
        {"name": "Classifier", "purpose": "Classifies by type"},
        {"name": "Responder", "purpose": "Generates responses"}
      ]
    }
  }
}`;

      const result = parseStructuredResponse(input);
      // Message is now the work_summary (prioritized over message field)
      // Markdown with h2 headings is generated by getReviewContent() from preview data
      expect(result.message).toBe("Designed multi-agent architecture for customer support.");
      expect(result.hitl?.type).toBe("confirm_architecture");
      expect(result.hitl?.preview?.manager?.name).toBe("Ticket Orchestrator");
    });

    it("should handle review_agent HITL with full agent_yaml in preview", () => {
      const input = JSON.stringify({
        action: "hitl",
        message: "Here's the manager agent specification.",
        hitl: {
          type: "review_agent",
          title: "Review Agent: Support Manager",
          work_summary: "Created Support Manager specification (manager, 1/3 agents).",
          info_items: [],
          preview: {
            agent_yaml: {
              filename: "support-manager.yaml",
              is_manager: true,
              agent_index: 0,
              name: "Support Manager",
              description: "Orchestrates customer support workflow",
              model: "gpt-4o-mini",
              temperature: 0.3,
              role: "Customer Support Orchestrator",
              goal: "Route and manage support tickets efficiently",
              instructions: "You are the support manager...",
              features: ["memory"],
              sub_agents: ["classifier.yaml", "responder.yaml"],
            },
          },
        },
      });

      const result = parseStructuredResponse(input);
      expect(result.hitl?.type).toBe("review_agent");
      expect(result.hitl?.preview?.agent_yaml?.name).toBe("Support Manager");
      expect(result.hitl?.preview?.agent_yaml?.is_manager).toBe(true);
      expect(result.hitl?.preview?.agent_yaml?.sub_agents).toEqual([
        "classifier.yaml",
        "responder.yaml",
      ]);
    });

    it("should handle final create_blueprint action", () => {
      const input = JSON.stringify({
        action: "create_blueprint",
        message: "All agents approved! Creating your blueprint now.",
        blueprint_yaml: {
          name: "Customer Support Automation",
          description: "Automates customer support ticket handling",
          category: "customer",
          tags: ["support", "automation"],
          visibility: "private",
          root_agents: ["support-manager.yaml"],
        },
      });

      const result = parseStructuredResponse(input);
      expect(result.message).toBe("All agents approved! Creating your blueprint now.");
      expect(result.hitl).toBeNull();
      expect(result.blueprint_yaml).not.toBeNull();
      expect((result.blueprint_yaml as Record<string, unknown>).name).toBe(
        "Customer Support Automation"
      );
      expect((result.blueprint_yaml as Record<string, unknown>).category).toBe("customer");
    });
  });

  describe("Legacy markdown mode - create_blueprint", () => {
    it("should extract create_blueprint from markdown code block", () => {
      const input = `Creating your blueprint now!

\`\`\`json
{"action": "create_blueprint", "message": "Done!", "blueprint_yaml": {"name": "Test BP", "description": "A test"}}
\`\`\``;

      const result = parseStructuredResponse(input);
      expect(result.blueprint_yaml).toEqual({
        name: "Test BP",
        description: "A test",
      });
      expect(result.message).toBe("Creating your blueprint now!");
    });
  });
});
