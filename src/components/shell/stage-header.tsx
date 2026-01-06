"use client";

import { Check } from "lucide-react";
import { getStageById, DEFAULT_STAGES, type Stage } from "@/lib/schemas/stage";
import { cn } from "@/lib/utils";

export interface StageHeaderProps {
  /** Current stage number (1-5) */
  stage: number;
  /** The furthest stage reached in the journey */
  maxReachedStage: number;
  /** Custom stage override */
  stageData?: Stage;
  /** Handler when a stage is clicked */
  onStageClick?: (stageId: number) => void;
  /** Additional class names */
  className?: string;
}

/**
 * StageHeader - Header with title, instruction, and clickable stage progress
 *
 * Displays the stage title, instruction, and progress indicator.
 * Stages are clickable for direct navigation.
 *
 * @example
 * ```tsx
 * <StageHeader
 *   stage={2}
 *   maxReachedStage={3}
 *   onStageClick={(id) => goToStage(id)}
 * />
 * ```
 */
export function StageHeader({
  stage,
  maxReachedStage,
  stageData,
  onStageClick,
  className,
}: StageHeaderProps) {
  // Get stage from schema, with fallback
  const currentStage = stageData || (() => {
    try {
      return getStageById(DEFAULT_STAGES, stage);
    } catch {
      return DEFAULT_STAGES[0];
    }
  })();

  return (
    <header
      className={cn(
        "flex-shrink-0 px-6 py-4 border-b bg-orange-50 dark:bg-orange-950/30",
        className
      )}
    >
      {/* Title and instruction */}
      <div className="text-center space-y-1 mb-4">
        <h1 className="text-lg font-semibold tracking-tight">
          {currentStage.title}
        </h1>
        <p className="text-sm text-muted-foreground">
          {currentStage.instruction}
        </p>
      </div>

      {/* Clickable stage progress - two rows: circles/connectors, then labels */}
      <div className="flex flex-col items-center gap-1">
        {/* Top row: circles and connectors */}
        <div className="flex items-center justify-center">
          {DEFAULT_STAGES.map((stageItem, index) => {
            const isCompleted = stageItem.id < maxReachedStage;
            const isCurrent = stageItem.id === stage;
            const isReached = stageItem.id <= maxReachedStage;
            const isLast = index === DEFAULT_STAGES.length - 1;
            const isClickable = stageItem.id !== stage;

            return (
              <div key={stageItem.id} className="flex items-center">
                {/* Stage circle - clickable */}
                <button
                  type="button"
                  onClick={() => isClickable && onStageClick?.(stageItem.id)}
                  disabled={!isClickable}
                  className={cn(
                    "w-7 h-7 rounded-full flex items-center justify-center",
                    "text-[11px] font-semibold transition-all",
                    "border-2",
                    isCompleted && "bg-orange-500 border-orange-500 text-white",
                    isCurrent && !isCompleted && "bg-orange-100 dark:bg-orange-950 border-orange-500 text-orange-600",
                    !isReached && "bg-muted border-muted-foreground/20 text-muted-foreground/50",
                    isClickable && "cursor-pointer hover:scale-110 hover:ring-2 hover:ring-orange-300 hover:ring-offset-1",
                    !isClickable && "cursor-default"
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-3.5 w-3.5" />
                  ) : (
                    stageItem.id
                  )}
                </button>

                {/* Connector line */}
                {!isLast && (
                  <div
                    className={cn(
                      "w-8 h-0.5",
                      stageItem.id < maxReachedStage
                        ? "bg-orange-500"
                        : "bg-muted-foreground/20"
                    )}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom row: labels */}
        <div className="flex items-center justify-center">
          {DEFAULT_STAGES.map((stageItem, index) => {
            const isCompleted = stageItem.id < maxReachedStage;
            const isCurrent = stageItem.id === stage;
            const isReached = stageItem.id <= maxReachedStage;
            const isLast = index === DEFAULT_STAGES.length - 1;

            return (
              <div key={stageItem.id} className="flex items-center">
                {/* Label - fixed width to match circle + connector */}
                <span
                  className={cn(
                    "w-7 text-center text-[9px] font-medium whitespace-nowrap",
                    isCurrent && "text-orange-600",
                    isCompleted && "text-foreground",
                    !isReached && "text-muted-foreground/50"
                  )}
                >
                  {stageItem.name}
                </span>

                {/* Spacer matching connector width */}
                {!isLast && <div className="w-8" />}
              </div>
            );
          })}
        </div>
      </div>
    </header>
  );
}
