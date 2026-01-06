"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Step {
  id: number;
  label: string;
  description?: string;
}

export interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
  className?: string;
  /** Compact mode for header display */
  compact?: boolean;
}

const DEFAULT_STEPS: Step[] = [
  { id: 1, label: "Problem", description: "Describe your needs" },
  { id: 2, label: "Design", description: "Review architecture" },
  { id: 3, label: "Refine", description: "Review agents" },
  { id: 4, label: "Create", description: "Build blueprint" },
  { id: 5, label: "Done", description: "Ready to use" },
];

/**
 * StepIndicator - Visual progress indicator for the blueprint journey
 *
 * Shows the current step in the multi-step process with visual
 * indicators for completed, current, and upcoming steps.
 *
 * @example
 * ```tsx
 * <StepIndicator currentStep={2} />
 * <StepIndicator currentStep={3} compact />
 * ```
 */
export function StepIndicator({
  steps = DEFAULT_STEPS,
  currentStep,
  className,
  compact = false,
}: StepIndicatorProps) {
  if (compact) {
    return (
      <div className={cn("flex items-center gap-1.5", className)}>
        {steps.map((step, index) => {
          const isCompleted = step.id < currentStep;
          const isCurrent = step.id === currentStep;

          return (
            <div
              key={step.id}
              className={cn(
                "h-1.5 rounded-full transition-all",
                index === 0 ? "w-6" : "w-4",
                isCompleted && "bg-orange-500",
                isCurrent && "bg-orange-500 w-6",
                !isCompleted && !isCurrent && "bg-muted-foreground/20"
              )}
              title={step.label}
            />
          );
        })}
      </div>
    );
  }

  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = step.id < currentStep;
          const isCurrent = step.id === currentStep;
          const isLast = index === steps.length - 1;

          return (
            <div key={step.id} className="flex items-center flex-1">
              {/* Step circle */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center",
                    "text-sm font-medium transition-all",
                    "border-2",
                    isCompleted &&
                      "bg-orange-500 border-orange-500 text-white",
                    isCurrent &&
                      "bg-orange-100 dark:bg-orange-950 border-orange-500 text-orange-600",
                    !isCompleted &&
                      !isCurrent &&
                      "bg-muted border-muted-foreground/20 text-muted-foreground"
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    step.id
                  )}
                </div>
                <div className="mt-2 text-center">
                  <p
                    className={cn(
                      "text-xs font-medium",
                      isCurrent ? "text-orange-600" : "text-muted-foreground"
                    )}
                  >
                    {step.label}
                  </p>
                  {step.description && (
                    <p className="text-xs text-muted-foreground/60 hidden sm:block">
                      {step.description}
                    </p>
                  )}
                </div>
              </div>

              {/* Connector line */}
              {!isLast && (
                <div
                  className={cn(
                    "flex-1 h-0.5 mx-2",
                    isCompleted ? "bg-orange-500" : "bg-muted-foreground/20"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
