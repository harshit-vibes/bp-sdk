"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Check,
  MessageSquare,
  ExternalLink,
  Sparkles,
  X,
  Loader2,
  Edit2,
  Save,
  RefreshCw,
  Copy,
  Shuffle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { SelectorDialog, type SelectorOption } from "./selector-dialog";

export interface ActionGroupProps {
  /** Mode determines which buttons to show */
  mode: "submit" | "hitl" | "conversational" | "complete" | "preview";
  /** Whether actions are loading */
  isLoading?: boolean;
  /** Whether the primary action is disabled */
  isDisabled?: boolean;
  /** Primary button label */
  primaryLabel?: string;
  /** Secondary button label (for revise/reply) */
  secondaryLabel?: string;
  /** Handler for primary action (submit/approve) */
  onPrimary?: () => void;
  /** Handler for secondary action with text (revise/reply) */
  onSecondary?: (text: string) => void;
  /** Handler for "create another" action (complete mode) */
  onCreateAnother?: () => void;
  /** Blueprint URL for complete mode */
  blueprintUrl?: string;
  /** Blueprint name for complete mode */
  blueprintName?: string;
  /** Whether currently in edit mode */
  isEditMode?: boolean;
  /** Handler for entering edit mode */
  onEdit?: () => void;
  /** Handler for canceling edit mode */
  onCancelEdit?: () => void;
  /** Handler for saving edits */
  onSaveEdit?: () => void;
  /** Revision context for suggestions */
  revisionContext?: {
    sessionId: string;
    type: "architecture" | "agent";
    agentName?: string;
    role?: string;
    goal?: string;
    instructions?: string;
  };
  /** Blueprint context for "Create Another" suggestions */
  blueprintContext?: {
    sessionId?: string;
    blueprintName: string;
    blueprintDescription?: string;
    agentTypes?: string[];
  };
  /** Additional class names */
  className?: string;
}

/**
 * ActionGroup - Shared action buttons for screens
 *
 * Used by both GuidedChat and ReviewScreen for consistent action handling.
 *
 * Modes:
 * - submit: Single primary button (GuidedChat)
 * - hitl: Approve & Request Changes buttons (Design/Build)
 * - conversational: Reply button (Explore)
 * - complete: Create Another & View Blueprint (Launch)
 * - preview: Placeholder for unreached stages
 */
// Fallback suggestions (8 options each)
const FALLBACK_SUGGESTIONS: Record<string, string[]> = {
  architecture: [
    "Add more worker agents",
    "Simplify the structure",
    "Add specialized roles",
    "Improve task delegation",
    "Add error handling",
    "Enhance coordination",
    "Split responsibilities",
    "Change the pattern",
  ],
  agent: [
    "Add detailed steps",
    "Clarify the goal",
    "Improve instructions",
    "Add edge cases",
    "Enhance output format",
    "Add constraints",
    "Simplify the role",
    "Change the tone",
  ],
};

export function ActionGroup({
  mode,
  isLoading = false,
  isDisabled = false,
  primaryLabel,
  secondaryLabel,
  onPrimary,
  onSecondary,
  onCreateAnother,
  blueprintUrl,
  blueprintName,
  isEditMode = false,
  onEdit,
  onCancelEdit,
  onSaveEdit,
  revisionContext,
  blueprintContext,
  className,
}: ActionGroupProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [inputText, setInputText] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<"revision" | "createAnother">("revision");
  const [suggestions, setSuggestions] = useState<SelectorOption[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [createSuggestions, setCreateSuggestions] = useState<SelectorOption[]>([]);
  const [isLoadingCreateSuggestions, setIsLoadingCreateSuggestions] = useState(false);

  // Options for "Create Another" dialog (8 options like other dialogs)
  const createAnotherOptions: SelectorOption[] = [
    {
      label: "Start Fresh",
      value: "fresh",
      description: "New blueprint from scratch",
    },
    {
      label: "Similar Pattern",
      value: "similar",
      description: "Same structure, new purpose",
    },
    {
      label: "Different Domain",
      value: "different_domain",
      description: "New business area",
    },
    {
      label: "More Workers",
      value: "more_workers",
      description: "Larger team structure",
    },
    {
      label: "Simpler Design",
      value: "simpler",
      description: "Single agent approach",
    },
    {
      label: "Automation Focus",
      value: "automation",
      description: "Task automation blueprint",
    },
    {
      label: "Customer Facing",
      value: "customer",
      description: "Support or sales agents",
    },
    {
      label: "Internal Tools",
      value: "internal",
      description: "Back-office automation",
    },
  ];

  // Reset editing state when mode changes (e.g., from conversational to hitl)
  useEffect(() => {
    setIsEditing(false);
    setInputText("");
    setDialogOpen(false);
    setDialogMode("revision");
  }, [mode]);

  // Handle dialog selection based on mode
  const handleDialogSelect = useCallback((value: string) => {
    if (dialogMode === "createAnother") {
      onCreateAnother?.();
    } else {
      onSecondary?.(value);
    }
    setDialogOpen(false);
  }, [dialogMode, onCreateAnother, onSecondary]);

  // Open dialog for "Create Another"
  const handleOpenCreateAnotherDialog = useCallback(() => {
    setDialogMode("createAnother");
    setCreateSuggestions([]); // Clear to trigger fresh fetch
    setDialogOpen(true);
  }, []);

  // Fetch suggestions when dialog opens (only for revision mode)
  const fetchSuggestions = useCallback(async () => {
    // Skip if in createAnother mode (options are static)
    if (dialogMode === "createAnother") {
      return;
    }

    if (!revisionContext) {
      // Use fallback suggestions (default to agent type)
      const fallback = FALLBACK_SUGGESTIONS["agent"];
      setSuggestions(fallback.map(s => ({ label: s, value: s })));
      return;
    }

    setIsLoadingSuggestions(true);
    try {
      const response = await fetch("/api/builder/suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: revisionContext.sessionId,
          type: revisionContext.type,
          agent_name: revisionContext.agentName,
          role: revisionContext.role,
          goal: revisionContext.goal,
          instructions: revisionContext.instructions?.substring(0, 500),
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const opts = (data.suggestions || [])
          .map((s: string) => ({ label: s, value: s }));
        setSuggestions(opts);
      } else {
        // Use fallback
        const fallback = FALLBACK_SUGGESTIONS[revisionContext.type];
        setSuggestions(fallback.map(s => ({ label: s, value: s })));
      }
    } catch {
      // Use fallback
      const fallback = FALLBACK_SUGGESTIONS[revisionContext?.type || "agent"];
      setSuggestions(fallback.map(s => ({ label: s, value: s })));
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, [dialogMode, revisionContext]);

  // Fetch suggestions when dialog opens (only for revision mode)
  useEffect(() => {
    if (dialogOpen && dialogMode === "revision" && suggestions.length === 0) {
      fetchSuggestions();
    }
  }, [dialogOpen, dialogMode, suggestions.length, fetchSuggestions]);

  // Fetch suggestions for "Create Another" dialog
  const fetchCreateSuggestions = useCallback(async () => {
    if (!blueprintContext) {
      // Use fallback options if no context
      setCreateSuggestions(createAnotherOptions);
      return;
    }

    setIsLoadingCreateSuggestions(true);
    try {
      const response = await fetch("/api/builder/create-suggestions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: blueprintContext.sessionId,
          blueprint_name: blueprintContext.blueprintName,
          blueprint_description: blueprintContext.blueprintDescription,
          agent_types: blueprintContext.agentTypes,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const opts = (data.suggestions || []).map((s: { label: string; value: string; description?: string }) => ({
          label: s.label,
          value: s.value,
          description: s.description,
        }));
        if (opts.length > 0) {
          setCreateSuggestions(opts);
        } else {
          setCreateSuggestions(createAnotherOptions);
        }
      } else {
        setCreateSuggestions(createAnotherOptions);
      }
    } catch {
      setCreateSuggestions(createAnotherOptions);
    } finally {
      setIsLoadingCreateSuggestions(false);
    }
  }, [blueprintContext, createAnotherOptions]);

  // Fetch suggestions when dialog opens (only for createAnother mode)
  useEffect(() => {
    if (dialogOpen && dialogMode === "createAnother" && createSuggestions.length === 0) {
      fetchCreateSuggestions();
    }
  }, [dialogOpen, dialogMode, createSuggestions.length, fetchCreateSuggestions]);

  // Handle opening the revision dialog
  const handleOpenRevisionDialog = useCallback(() => {
    setDialogMode("revision");
    setSuggestions([]); // Clear old suggestions to trigger fresh fetch
    setDialogOpen(true);
  }, []);

  const handleSubmitText = () => {
    if (!inputText.trim() || !onSecondary) return;
    onSecondary(inputText.trim());
    setInputText("");
    setIsEditing(false);
  };

  // Shared dialog for both revision suggestions and create another options
  const isDialogLoading = dialogMode === "createAnother" ? isLoadingCreateSuggestions : isLoadingSuggestions;
  const dialogOptions = dialogMode === "createAnother" ? createSuggestions : suggestions;

  const dialogConfig = dialogMode === "createAnother" ? {
    title: "Create Another Blueprint",
    description: "What type of blueprint would you like to create?",
    options: isDialogLoading ? [] : dialogOptions,
    allowCustom: true,
    columns: 2 as const,
  } : {
    title: "What would you like to change?",
    description: revisionContext?.type === "architecture"
      ? "Select a suggestion or describe your changes"
      : `Feedback for ${revisionContext?.agentName || "this agent"}`,
    options: isDialogLoading ? [] : dialogOptions,
    allowCustom: true,
    columns: 2 as const,
  };

  const sharedDialog = (
    <SelectorDialog
      open={dialogOpen}
      onOpenChange={setDialogOpen}
      title={dialogConfig.title}
      description={dialogConfig.description}
      options={dialogConfig.options}
      value={null}
      onSelect={handleDialogSelect}
      allowCustom={dialogConfig.allowCustom}
      customLabel={dialogMode === "revision" ? "Or describe your changes" : "Or describe what you want to build"}
      customPlaceholder={dialogMode === "revision" ? "Please add more detail about..." : "I want to create a blueprint that..."}
      customMultiline
      columns={dialogConfig.columns}
      preview={
        isDialogLoading ? (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="h-6 w-6 animate-spin text-orange-500" />
            <span className="ml-2 text-sm text-muted-foreground">
              {dialogMode === "createAnother" ? "Generating ideas..." : "Loading suggestions..."}
            </span>
          </div>
        ) : undefined
      }
    />
  );

  // Preview mode - placeholder for unreached stages
  if (mode === "preview") {
    return (
      <>
        {sharedDialog}
        <div className={cn("px-3 sm:px-6 py-3 sm:py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
          <div className="flex justify-center items-center h-11">
            <p className="text-sm text-muted-foreground text-center">
              Complete earlier stages to unlock this step
            </p>
          </div>
        </div>
      </>
    );
  }

  // Submit mode - single centered button
  if (mode === "submit") {
    return (
      <>
        {sharedDialog}
        <div className={cn("px-3 sm:px-6 py-3 sm:py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
          <div className="flex justify-center items-center h-11">
            <Button
              onClick={onPrimary}
              disabled={isDisabled || isLoading}
              size="lg"
              className="gap-2 px-6 sm:px-8 bg-orange-500 hover:bg-orange-600"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              {primaryLabel || "Continue"}
            </Button>
          </div>
        </div>
      </>
    );
  }

  // Complete mode - Create Another & View Blueprint
  if (mode === "complete") {
    return (
      <>
        {sharedDialog}
        <div className={cn("px-3 sm:px-6 py-3 sm:py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
          <div className="flex gap-2 sm:gap-3 items-center h-11 max-w-md mx-auto">
            <Button
              variant="outline"
              onClick={handleOpenCreateAnotherDialog}
              className="flex-1 text-xs sm:text-sm"
            >
              <Sparkles className="h-4 w-4 mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Create Another</span>
              <span className="sm:hidden">New</span>
            </Button>
            {blueprintUrl && (
              <Button asChild className="flex-1 bg-orange-500 hover:bg-orange-600 text-xs sm:text-sm">
                <a href={blueprintUrl} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 mr-1 sm:mr-2" />
                  <span className="hidden sm:inline">View Blueprint</span>
                  <span className="sm:hidden">View</span>
                </a>
              </Button>
            )}
          </div>
        </div>
      </>
    );
  }

  // Text input mode (for conversational reply only)
  if (isEditing) {
    return (
      <>
        {sharedDialog}
        <div className={cn("px-3 sm:px-6 py-3 sm:py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
          <div className="space-y-3 max-w-2xl mx-auto">
            <Textarea
              placeholder={
                mode === "conversational"
                  ? "Type your response..."
                  : "Describe what you'd like to change..."
              }
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="min-h-[80px] border-orange-200 dark:border-orange-800 focus-visible:ring-orange-500"
              autoFocus
            />
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setIsEditing(false);
                  setInputText("");
                }}
                disabled={isLoading}
                className="flex-1"
              >
                <X className="h-4 w-4 mr-1 sm:mr-2" />
                <span className="hidden sm:inline">Cancel</span>
              </Button>
              <Button
                onClick={handleSubmitText}
                disabled={!inputText.trim() || isLoading}
                className="flex-1 bg-orange-500 hover:bg-orange-600"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 mr-1 sm:mr-2 animate-spin" />
                ) : (
                  <MessageSquare className="h-4 w-4 mr-1 sm:mr-2" />
                )}
                {mode === "conversational" ? "Send" : "Submit"}
              </Button>
            </div>
          </div>
        </div>
      </>
    );
  }

  // HITL mode - Approve & Request Changes (or Save/Cancel when editing)
  if (mode === "hitl") {
    // Edit mode: Cancel & Save buttons
    if (isEditMode) {
      return (
        <>
          {sharedDialog}
          <div className={cn("px-3 sm:px-6 py-3 sm:py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
            <div className="flex gap-2 sm:gap-3 items-center h-11 max-w-md mx-auto">
              <Button
                variant="outline"
                onClick={onCancelEdit}
                disabled={isLoading}
                className="flex-1"
              >
                <X className="h-4 w-4 mr-1 sm:mr-2" />
                <span className="hidden sm:inline">Cancel</span>
              </Button>
              <Button
                onClick={onSaveEdit}
                disabled={isDisabled || isLoading}
                className="flex-1 bg-orange-500 hover:bg-orange-600 text-xs sm:text-sm"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 mr-1 sm:mr-2 animate-spin" />
                ) : (
                  <Save className="h-4 w-4 mr-1 sm:mr-2" />
                )}
                <span className="hidden sm:inline">Save Changes</span>
                <span className="sm:hidden">Save</span>
              </Button>
            </div>
          </div>
        </>
      );
    }

    // Normal HITL mode: Edit, Request Changes, Approve
    return (
      <>
        {sharedDialog}
        <div className={cn("px-3 sm:px-6 py-3 sm:py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
          <div className="flex gap-2 sm:gap-3 items-center h-11 max-w-lg mx-auto">
            {/* Edit button - only show if onEdit is provided */}
            {onEdit && (
              <Button
                variant="outline"
                onClick={onEdit}
                disabled={isLoading}
                className="flex-shrink-0 px-2 sm:px-4"
              >
                <Edit2 className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">Edit</span>
              </Button>
            )}
            <Button
              variant="outline"
              onClick={handleOpenRevisionDialog}
              disabled={isLoading}
              className="flex-1 text-xs sm:text-sm"
            >
              <MessageSquare className="h-4 w-4 mr-1 sm:mr-2" />
              <span className="hidden sm:inline">{secondaryLabel || "Request Changes"}</span>
              <span className="sm:hidden">Revise</span>
            </Button>
            <Button
              onClick={onPrimary}
              disabled={isDisabled || isLoading}
              className="flex-1 bg-orange-500 hover:bg-orange-600 text-xs sm:text-sm"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 mr-1 sm:mr-2 animate-spin" />
              ) : (
                <Check className="h-4 w-4 mr-1 sm:mr-2" />
              )}
              <span className="hidden sm:inline">{primaryLabel || "Approve & Continue"}</span>
              <span className="sm:hidden">Approve</span>
            </Button>
          </div>
        </div>
      </>
    );
  }

  // Conversational mode - Reply button
  return (
    <>
      {sharedDialog}
      <div className={cn("px-3 sm:px-6 py-3 sm:py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
        <div className="flex justify-center items-center h-11">
          <Button
            onClick={() => setIsEditing(true)}
            disabled={isLoading}
            size="lg"
            className="gap-2 px-6 sm:px-8 bg-orange-500 hover:bg-orange-600"
          >
            <MessageSquare className="h-4 w-4" />
            {primaryLabel || "Reply"}
          </Button>
        </div>
      </div>
    </>
  );
}
