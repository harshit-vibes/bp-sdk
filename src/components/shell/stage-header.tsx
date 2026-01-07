"use client";

import { UNIFIED_STAGES, type UnifiedStage, type BuildProgress } from "@/lib/schemas/stage";
import { UnifiedStepIndicator, type BuildSubStep } from "@/components/builder";
import { cn } from "@/lib/utils";

export interface StageHeaderProps {
  /** Current unified stage */
  unifiedStage: UnifiedStage;
  /** Build progress (for Build stage) */
  buildProgress?: BuildProgress;
  /** Sub-steps for Build stage */
  buildSubSteps?: BuildSubStep[];
  /** Current sub-step index */
  currentSubStep?: number;
  /** Maximum completed sub-step (for forward navigation) */
  maxCompletedSubStep?: number;
  /** Whether Build stage has existing progress (allows clicking when on Define) */
  hasBuildProgress?: boolean;
  /** Called when a main stage is clicked */
  onStageClick?: (stage: UnifiedStage) => void;
  /** Called when a sub-step is clicked */
  onSubStepClick?: (index: number) => void;
  /** Whether currently showing architecture review (vs agent review) */
  isArchitectureReview?: boolean;
  /** Current agent name (for agent review title) */
  currentAgentName?: string;
  /** Additional class names */
  className?: string;
}

/**
 * StageHeader - Header with title, instruction, and unified stage progress
 *
 * Displays the stage title, instruction, and 3-step progress indicator.
 * Shows N/M progress during the Build stage.
 *
 * @example
 * ```tsx
 * <StageHeader
 *   unifiedStage="build"
 *   buildProgress={{ current: 2, total: 4 }}
 * />
 * ```
 */
export function StageHeader({
  unifiedStage,
  buildProgress,
  buildSubSteps,
  currentSubStep,
  maxCompletedSubStep,
  hasBuildProgress,
  onStageClick,
  onSubStepClick,
  isArchitectureReview,
  currentAgentName,
  className,
}: StageHeaderProps) {
  const stageData = UNIFIED_STAGES.find((s) => s.id === unifiedStage) || UNIFIED_STAGES[0];

  // Dynamic title based on current step/sub-step
  let title = stageData.title;
  if (unifiedStage === "build") {
    if (isArchitectureReview) {
      title = "Review Architecture";
    } else if (currentAgentName && buildProgress) {
      title = `Review ${currentAgentName}`;
    }
  }

  return (
    <header
      className={cn(
        "flex-shrink-0 px-3 sm:px-6 py-3 sm:py-4 border-b bg-orange-50 dark:bg-orange-950/30",
        className
      )}
    >
      {/* Title */}
      <h1 className="text-base sm:text-lg font-semibold tracking-tight text-center mb-2 sm:mb-4">
        {title}
      </h1>

      {/* Unified 3-stage progress with navigation */}
      <UnifiedStepIndicator
        stage={unifiedStage}
        buildProgress={buildProgress}
        buildSubSteps={buildSubSteps}
        currentSubStep={currentSubStep}
        maxCompletedSubStep={maxCompletedSubStep}
        hasBuildProgress={hasBuildProgress}
        onStageClick={onStageClick}
        onSubStepClick={onSubStepClick}
      />
    </header>
  );
}
