"use client";

import { useMemo, useState, useCallback, useEffect } from "react";
import { useBuilder } from "@/lib/hooks/use-builder";
import { DEFAULT_STATEMENT_TEMPLATE } from "@/lib/schemas/selector";
import { StageHeader } from "./stage-header";
import { ActionGroup } from "@/components/builder";
import { GuidedChat } from "@/components/screens/guided-chat";
import { ReviewScreen } from "@/components/screens/review-screen";
import { SetupScreen, getStoredCredentials, type ApiCredentials } from "@/components/screens";
import { cn } from "@/lib/utils";
import { buildAgentInfoItems, agentSpecToAnswers, answersToAgentSpec } from "@/lib/agent-fields";

export interface AppShellProps {
  /** Additional class names */
  className?: string;
}

/**
 * AppShell - Main container for the Blueprint Builder journey
 *
 * Uses stage-based API calls instead of streaming:
 * 0. Setup: User enters API credentials
 * 1. Define: User fills GuidedChat statement
 * 2. Design: POST /api/builder/architect → architecture review
 * 3. Build: POST /api/builder/craft → agent review (per agent)
 * 4. Launch: POST /api/builder/create → success
 */
export function AppShell({ className }: AppShellProps) {
  const builder = useBuilder();

  // Setup state - track if credentials are configured
  const [isSetupComplete, setIsSetupComplete] = useState<boolean | null>(null);
  const [credentials, setCredentials] = useState<ApiCredentials | null>(null);

  // Check for stored credentials on mount
  useEffect(() => {
    const stored = getStoredCredentials();
    if (stored) {
      setCredentials(stored);
      setIsSetupComplete(true);
    } else {
      setIsSetupComplete(false);
    }
  }, []);

  // Handle setup completion
  const handleSetupComplete = useCallback((creds: ApiCredentials) => {
    setCredentials(creds);
    setIsSetupComplete(true);
  }, []);

  // State for GuidedChat statement
  const [statementReady, setStatementReady] = useState(false);
  const [currentStatement, setCurrentStatement] = useState<string | null>(null);
  // State for GuidedChat slot selections (persisted across navigation)
  const [slotSelections, setSlotSelections] = useState<Record<string, string | null>>({});

  // Reset local state when builder goes back to "define" (after reset)
  useEffect(() => {
    if (builder.builderStage === "define" && !builder.sessionId) {
      // Reset all local state when starting fresh (no session = new journey)
      setStatementReady(false);
      setCurrentStatement(null);
      setSlotSelections({});
    }
  }, [builder.builderStage, builder.sessionId]);

  // Handle statement changes from GuidedChat
  const handleStatementChange = useCallback((canSubmit: boolean, statement: string | null) => {
    setStatementReady(canSubmit);
    setCurrentStatement(statement);
  }, []);

  // Handle slot selection changes from GuidedChat (for persistence)
  const handleSelectionsChange = useCallback((selections: Record<string, string | null>) => {
    setSlotSelections(selections);
  }, []);

  // Handle submit for GuidedChat
  const handleSubmitStatement = useCallback(() => {
    if (currentStatement) {
      builder.submitStatement(currentStatement);
    }
  }, [currentStatement, builder]);

  // Handle primary action based on stage
  const handlePrimary = useCallback(() => {
    if (builder.actionMode === "submit") {
      // If in read-only mode, enter edit mode first
      if (builder.isDefineReadOnly) {
        builder.enterDefineEditMode();
      } else {
        handleSubmitStatement();
      }
    } else if (builder.builderStage === "design-review") {
      builder.approveArchitecture();
    } else if (builder.builderStage === "craft-review") {
      builder.approveAgent();
    }
  }, [builder, handleSubmitStatement]);

  // Handle revise action based on stage
  const handleSecondary = useCallback((feedback: string) => {
    if (builder.builderStage === "design-review") {
      builder.reviseArchitecture(feedback);
    } else if (builder.builderStage === "craft-review") {
      builder.reviseAgent(feedback);
    }
  }, [builder]);

  // Determine if primary button should be disabled
  const isPrimaryDisabled = useMemo(() => {
    if (builder.isLoading) return true;
    if (builder.actionMode === "submit") {
      // In read-only mode, Edit button is always enabled
      if (builder.isDefineReadOnly) return false;
      // In edit mode, only enable when statement is ready
      return !statementReady;
    }
    return false;
  }, [builder.actionMode, builder.isLoading, builder.isDefineReadOnly, statementReady]);

  // Convert blueprintResult to the format expected by ReviewScreen
  const blueprintInfo = builder.blueprintResult ? {
    id: builder.blueprintResult.blueprint_id,
    name: builder.blueprintResult.blueprint_name || builder.blueprintResult.blueprint_id,
    studio_url: builder.blueprintResult.studio_url,
    manager_id: builder.blueprintResult.manager_id,
    organization_id: builder.blueprintResult.organization_id,
    created_at: builder.blueprintResult.created_at,
    share_type: builder.blueprintResult.share_type,
  } : undefined;

  // Edit mode: Build form items for current agent spec
  const editItems = useMemo(() => {
    // Use editedSpec if in edit mode, otherwise currentAgentSpec
    const spec = builder.isEditMode && builder.editedSpec
      ? builder.editedSpec
      : builder.currentAgentSpec;

    if (!spec || builder.builderStage !== "craft-review") {
      return [];
    }

    const isManager = builder.currentAgentIndex === 0;
    return buildAgentInfoItems(spec, isManager);
  }, [builder.isEditMode, builder.editedSpec, builder.currentAgentSpec, builder.builderStage, builder.currentAgentIndex]);

  // Edit mode: Convert current spec to form answers
  const editAnswers = useMemo(() => {
    const spec = builder.isEditMode && builder.editedSpec
      ? builder.editedSpec
      : builder.currentAgentSpec;

    if (!spec) {
      return {};
    }

    return agentSpecToAnswers(spec);
  }, [builder.isEditMode, builder.editedSpec, builder.currentAgentSpec]);

  // Handle edit form changes
  const handleEditChange = useCallback((id: string, value: string) => {
    if (!builder.editedSpec) return;

    // Convert the single field change to a spec update
    const updates = answersToAgentSpec(builder.editedSpec, { [id]: value });
    builder.updateAgentSpec(updates);
  }, [builder]);

  // Build revision context for suggestions
  const revisionContext = useMemo(() => {
    if (!builder.sessionId) return undefined;

    // For architecture review
    if (builder.builderStage === "design-review") {
      return {
        sessionId: builder.sessionId,
        type: "architecture" as const,
      };
    }

    // For agent review
    if (builder.builderStage === "craft-review" && builder.currentAgentSpec) {
      return {
        sessionId: builder.sessionId,
        type: "agent" as const,
        agentName: builder.currentAgentSpec.name,
        role: builder.currentAgentSpec.role,
        goal: builder.currentAgentSpec.goal,
        instructions: builder.currentAgentSpec.instructions,
      };
    }

    return undefined;
  }, [builder.sessionId, builder.builderStage, builder.currentAgentSpec]);

  // Show loading state while checking for stored credentials
  if (isSetupComplete === null) {
    return (
      <div className={cn("flex flex-col h-full bg-background items-center justify-center", className)}>
        <div className="text-muted-foreground text-sm">Loading...</div>
      </div>
    );
  }

  // Show setup screen if credentials not configured
  if (!isSetupComplete) {
    return (
      <div className={cn("flex flex-col h-full bg-background", className)}>
        <SetupScreen onComplete={handleSetupComplete} />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-background",
        className
      )}
    >
      {/* Header - title, instruction, and unified stage progress */}
      <StageHeader
        unifiedStage={builder.unifiedStage}
        buildProgress={builder.buildProgress}
        buildSubSteps={builder.buildSubSteps}
        // -1 during architecture review (no agent selected), otherwise current agent index
        currentSubStep={builder.builderStage === "design-review" ? -1 : builder.currentAgentIndex}
        maxCompletedSubStep={builder.agentSpecs.length - 1}
        hasBuildProgress={builder.architecture !== null}
        onStageClick={(stage) => {
          if (stage === "define") {
            builder.navigateToDefine();
          } else if (stage === "build") {
            builder.navigateToBuild();
          }
        }}
        onSubStepClick={builder.navigateToSubStep}
        isArchitectureReview={builder.builderStage === "design-review"}
        currentAgentName={builder.currentAgentSpec?.name}
      />

      {/* Main Content - takes remaining space */}
      <main className="flex-1 min-h-0 overflow-hidden flex flex-col">
        {builder.screenType === "guided-chat" ? (
          <GuidedChat
            template={DEFAULT_STATEMENT_TEMPLATE}
            initialSelections={slotSelections}
            onStatementChange={handleStatementChange}
            onSelectionsChange={handleSelectionsChange}
            disabled={builder.isDefineReadOnly}
          />
        ) : (
          <ReviewScreen
            content={builder.reviewContent}
            isComplete={builder.actionMode === "complete"}
            blueprint={blueprintInfo}
            infoItems={[]}
            infoAnswers={{}}
            onInfoChange={() => {}}
            infoDisabled={builder.isLoading}
            isEditMode={builder.isEditMode}
            editItems={editItems}
            editAnswers={editAnswers}
            onEditChange={handleEditChange}
            isLoading={builder.isLoading}
            builderStage={builder.builderStage}
          />
        )}
      </main>

      {/* Error display */}
      {builder.error && (
        <div className="px-4 py-2 bg-destructive/10 text-destructive text-sm">
          {builder.error}
        </div>
      )}

      {/* Footer - action buttons */}
      <ActionGroup
        key={builder.actionMode}
        mode={builder.actionMode === "loading" ? "hitl" : builder.actionMode}
        isLoading={builder.isLoading}
        isDisabled={isPrimaryDisabled}
        primaryLabel={
          builder.actionMode === "submit"
            ? builder.isDefineReadOnly
              ? "Edit"
              : "Start Building"
            : builder.builderStage === "design-review"
              ? "Approve Design"
              : builder.builderStage === "craft-review"
                ? `Approve (${builder.currentAgentIndex + 1} of ${builder.totalAgents})`
                : undefined
        }
        onPrimary={handlePrimary}
        onSecondary={handleSecondary}
        onCreateAnother={builder.reset}
        blueprintUrl={builder.blueprintResult?.studio_url}
        blueprintName={builder.blueprintResult?.blueprint_name}
        isEditMode={builder.isEditMode}
        onCancelEdit={builder.exitEditMode}
        onSaveEdit={builder.saveEditedAgent}
        revisionContext={revisionContext}
        blueprintContext={builder.blueprintResult ? {
          sessionId: builder.blueprintResult.session_id,
          blueprintName: builder.blueprintResult.blueprint_name,
          agentTypes: [
            "manager",
            ...builder.blueprintResult.worker_ids.map(() => "worker")
          ],
        } : undefined}
      />
    </div>
  );
}
