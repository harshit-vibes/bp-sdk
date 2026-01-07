"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { UnifiedStage, BuildProgress } from "@/lib/schemas/stage";

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

/**
 * Sub-step for the Build stage
 */
export interface BuildSubStep {
  id: string;
  label: string;
  /** 0 = Architecture, 1+ = Agent index */
  index: number;
}

export interface UnifiedStepIndicatorProps {
  stage: UnifiedStage;
  buildProgress?: BuildProgress;
  className?: string;
  /** Sub-steps for Build stage (Architecture + Agents) */
  buildSubSteps?: BuildSubStep[];
  /** Current sub-step index (0 = Architecture, 1+ = Agent index) */
  currentSubStep?: number;
  /** Maximum completed sub-step (for forward navigation) */
  maxCompletedSubStep?: number;
  /** Whether Build stage has existing progress (allows clicking when on Define) */
  hasBuildProgress?: boolean;
  /** Called when a main stage is clicked */
  onStageClick?: (stage: UnifiedStage) => void;
  /** Called when a sub-step is clicked */
  onSubStepClick?: (index: number) => void;
}

const DEFAULT_STEPS: Step[] = [
  { id: 1, label: "Problem", description: "Describe your needs" },
  { id: 2, label: "Design", description: "Review architecture" },
  { id: 3, label: "Refine", description: "Review agents" },
  { id: 4, label: "Create", description: "Build blueprint" },
  { id: 5, label: "Done", description: "Ready to use" },
];

/**
 * UnifiedStepIndicator - Simple breadcrumb-style navigation
 *
 * Shows: Define / Architect / Build as simple text links
 * Sub-steps shown as small dots below current stage
 */
export function UnifiedStepIndicator({
  stage,
  buildProgress,
  className,
  buildSubSteps,
  currentSubStep = 0,
  maxCompletedSubStep = -1,
  hasBuildProgress = false,
  onStageClick,
  onSubStepClick,
}: UnifiedStepIndicatorProps) {
  const stages: { id: UnifiedStage; label: string }[] = [
    { id: "define", label: "Describe" },
    { id: "build", label: "Design" },
    { id: "complete", label: "Create" },
  ];

  const stageOrder: UnifiedStage[] = ["define", "build", "complete"];
  const currentIndex = stageOrder.indexOf(stage);

  // Determine if we should show sub-steps
  const showSubSteps = stage === "build" && buildSubSteps && buildSubSteps.length > 0;

  return (
    <div className={cn("flex flex-col items-center gap-3 w-full", className)}>
      {/* Simple breadcrumb navigation */}
      <nav className="flex items-center justify-center gap-1 text-sm">
        {stages.map((s, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = s.id === stage;
          const isLast = index === stages.length - 1;

          // Clickable if completed, or if it's Architect with progress
          const canClick = s.id === "build"
            ? (isCompleted || hasBuildProgress || (stage === "build" && buildProgress && buildProgress.current > 0))
            : isCompleted;
          const isClickable = canClick && onStageClick;

          const handleClick = () => {
            if (isClickable) {
              onStageClick(s.id);
            }
          };

          // Show progress count for Architect stage
          let label = s.label;
          if (s.id === "build" && buildProgress && buildProgress.total > 0) {
            label = `${s.label} (${buildProgress.current}/${buildProgress.total})`;
          }

          return (
            <span key={s.id} className="flex items-center">
              <button
                type="button"
                onClick={handleClick}
                disabled={!isClickable}
                className={cn(
                  "px-1 py-0.5 rounded transition-colors",
                  isCurrent && "text-orange-600 dark:text-orange-400 font-semibold",
                  isCompleted && !isCurrent && "text-orange-600/70 dark:text-orange-400/70",
                  !isCompleted && !isCurrent && "text-muted-foreground/50",
                  isClickable && "hover:text-orange-500 hover:underline cursor-pointer",
                  !isClickable && "cursor-default"
                )}
              >
                {label}
              </button>
              {!isLast && (
                <span className="text-muted-foreground/30 mx-1">/</span>
              )}
            </span>
          );
        })}
      </nav>

      {/* Sub-step breadcrumb navigation */}
      {showSubSteps && (
        <nav className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
          {buildSubSteps.map((subStep, index) => {
            const isSubCompleted = subStep.index <= maxCompletedSubStep;
            const isSubCurrent = subStep.index === currentSubStep;
            const isSubClickable = isSubCompleted && !isSubCurrent && onSubStepClick;
            const isSubLast = index === buildSubSteps.length - 1;

            const handleSubClick = () => {
              if (isSubClickable) {
                onSubStepClick(subStep.index);
              }
            };

            return (
              <span key={subStep.id} className="flex items-center">
                <button
                  type="button"
                  onClick={handleSubClick}
                  disabled={!isSubClickable}
                  className={cn(
                    "px-1 py-0.5 rounded transition-colors max-w-[120px] truncate",
                    isSubCurrent && "text-orange-600 dark:text-orange-400 font-medium",
                    isSubCompleted && !isSubCurrent && "text-orange-500/70 dark:text-orange-400/70",
                    !isSubCompleted && !isSubCurrent && "text-muted-foreground/40",
                    isSubClickable && "hover:text-orange-500 hover:underline cursor-pointer",
                    !isSubClickable && "cursor-default"
                  )}
                >
                  {subStep.label}
                </button>
                {!isSubLast && (
                  <span className="text-muted-foreground/20 mx-0.5">→</span>
                )}
              </span>
            );
          })}
        </nav>
      )}
    </div>
  );
}

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
