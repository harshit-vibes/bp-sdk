"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface AgentStep {
  index: number;
  name: string;
  isManager: boolean;
  status: "pending" | "current" | "approved";
}

export interface AgentStepperProps {
  /** List of all agents in order (manager first, then workers) */
  agents: AgentStep[];
  /** Handler when an approved agent step is clicked (for navigation) */
  onAgentClick?: (index: number) => void;
  /** Additional class names */
  className?: string;
}

/**
 * AgentStepper - Compact horizontal progress indicator for agent crafting
 *
 * Shows: [checkmark] - name - [dot] - name - [2] - name
 */
export function AgentStepper({
  agents,
  onAgentClick,
  className,
}: AgentStepperProps) {
  if (agents.length === 0) return null;

  return (
    <div className={cn("w-full", className)}>
      {/* Scrollable container for mobile */}
      <div className="overflow-x-auto">
        <div className="flex items-center justify-center min-w-fit">
          {agents.map((agent, index) => {
            const isLast = index === agents.length - 1;
            const isClickable = agent.status === "approved" && onAgentClick;

            return (
              <div key={agent.index} className="flex items-center">
                {/* Agent step */}
                <button
                  type="button"
                  onClick={() => isClickable && onAgentClick?.(agent.index)}
                  disabled={!isClickable}
                  className={cn(
                    "flex items-center gap-1.5 px-1.5 py-1 rounded transition-all",
                    isClickable && "hover:bg-orange-100 dark:hover:bg-orange-950/50 cursor-pointer",
                    !isClickable && "cursor-default"
                  )}
                >
                  {/* Circle indicator */}
                  <div
                    className={cn(
                      "w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0",
                      "border transition-all text-[10px] font-medium",
                      // Approved
                      agent.status === "approved" && "bg-orange-500 border-orange-500 text-white",
                      // Current
                      agent.status === "current" && "bg-orange-100 dark:bg-orange-950 border-orange-500 border-2",
                      // Pending
                      agent.status === "pending" && "bg-muted border-muted-foreground/30 text-muted-foreground"
                    )}
                  >
                    {agent.status === "approved" ? (
                      <Check className="h-3 w-3" />
                    ) : agent.status === "current" ? (
                      <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                    ) : (
                      <span>{agent.index + 1}</span>
                    )}
                  </div>

                  {/* Agent name */}
                  <span
                    className={cn(
                      "text-[11px] max-w-[60px] truncate",
                      agent.status === "current" && "text-orange-600 font-medium",
                      agent.status === "approved" && "text-foreground/70",
                      agent.status === "pending" && "text-muted-foreground"
                    )}
                    title={agent.name}
                  >
                    {agent.name}
                  </span>
                </button>

                {/* Connector line */}
                {!isLast && (
                  <div
                    className={cn(
                      "w-4 h-px mx-0.5",
                      agent.status === "approved"
                        ? "bg-orange-500"
                        : "bg-muted-foreground/20"
                    )}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/**
 * Helper to build agent steps from architecture and current state
 */
export function buildAgentSteps(
  architecture: { manager: { name: string }; workers: Array<{ name: string }> } | null,
  currentAgentIndex: number,
  approvedCount: number
): AgentStep[] {
  if (!architecture) return [];

  const steps: AgentStep[] = [];

  // Manager (always index 0)
  steps.push({
    index: 0,
    name: architecture.manager.name,
    isManager: true,
    status:
      approvedCount > 0 || currentAgentIndex > 0
        ? "approved"
        : currentAgentIndex === 0
        ? "current"
        : "pending",
  });

  // Workers (index 1+)
  architecture.workers.forEach((worker, i) => {
    const workerIndex = i + 1;
    const isApproved = workerIndex < currentAgentIndex || approvedCount > workerIndex;
    const isCurrent = workerIndex === currentAgentIndex;

    steps.push({
      index: workerIndex,
      name: worker.name,
      isManager: false,
      status: isApproved ? "approved" : isCurrent ? "current" : "pending",
    });
  });

  return steps;
}
