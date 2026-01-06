"use client";

import { Check, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DEFAULT_STAGES } from "@/lib/schemas/stage";
import { cn } from "@/lib/utils";

export interface StageFooterProps {
  /** Current stage number (1-5) */
  currentStage: number;
  /** The furthest stage reached in the journey */
  maxReachedStage: number;
  /** Handler to go to previous stage */
  onPrevious?: () => void;
  /** Handler to go to next stage */
  onNext?: () => void;
  /** Whether navigation is enabled */
  canNavigate?: boolean;
  /** Additional class names */
  className?: string;
}

/**
 * StageFooter - Footer with stage progress and navigation
 *
 * Shows the journey progress with Previous/Next navigation buttons.
 * Users can navigate back to completed stages to review or restart.
 *
 * @example
 * ```tsx
 * <StageFooter
 *   currentStage={2}
 *   maxReachedStage={3}
 *   onPrevious={handlePrevious}
 *   onNext={handleNext}
 * />
 * ```
 */
export function StageFooter({
  currentStage,
  maxReachedStage,
  onPrevious,
  onNext,
  canNavigate = true,
  className,
}: StageFooterProps) {
  const canGoPrevious = canNavigate && currentStage > 1;
  const canGoNext = canNavigate && currentStage < 5;

  return (
    <footer
      className={cn(
        "flex-shrink-0 px-5 py-4 border-t bg-orange-50 dark:bg-orange-950/30",
        className
      )}
    >
      <div className="flex items-center gap-2">
        {/* Previous button - left side */}
        <div className="w-20">
          <Button
            variant="ghost"
            size="sm"
            onClick={onPrevious}
            disabled={!canGoPrevious}
            className="h-7 text-xs"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Back
          </Button>
        </div>

        {/* Progress indicator - center */}
        <div className="flex-1 flex items-center justify-center">
          {DEFAULT_STAGES.map((stage, index) => {
            const isCompleted = stage.id < maxReachedStage;
            const isCurrent = stage.id === currentStage;
            const isReached = stage.id <= maxReachedStage;
            const isLast = index === DEFAULT_STAGES.length - 1;

            return (
              <div key={stage.id} className="flex items-center flex-1 max-w-[4.5rem]">
                {/* Stage indicator */}
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      "w-6 h-6 rounded-full flex items-center justify-center",
                      "text-[10px] font-semibold transition-all",
                      "border-2",
                      isCompleted && "bg-orange-500 border-orange-500 text-white",
                      isCurrent && !isCompleted && "bg-orange-100 dark:bg-orange-950 border-orange-500 text-orange-600",
                      !isReached && "bg-muted border-muted-foreground/20 text-muted-foreground/50"
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-3 w-3" />
                    ) : (
                      stage.id
                    )}
                  </div>
                  <span
                    className={cn(
                      "mt-1 text-[9px] font-medium whitespace-nowrap",
                      isCurrent && "text-orange-600",
                      isCompleted && "text-foreground",
                      !isReached && "text-muted-foreground/50"
                    )}
                  >
                    {stage.name}
                  </span>
                </div>

                {/* Connector line */}
                {!isLast && (
                  <div
                    className={cn(
                      "flex-1 h-0.5 mx-1 mt-[-0.75rem] min-w-2",
                      stage.id < maxReachedStage
                        ? "bg-orange-500"
                        : "bg-muted-foreground/20"
                    )}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Next button - right side */}
        <div className="w-20 flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={onNext}
            disabled={!canGoNext}
            className="h-7 text-xs"
          >
            Next
            <ChevronRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </footer>
  );
}
