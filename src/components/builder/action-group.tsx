"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Check,
  MessageSquare,
  ExternalLink,
  Sparkles,
  X,
  Loader2,
  AlertTriangle,
  Edit2,
  Save,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ValidationResult } from "@/lib/validation";

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
  /** Validation result for showing warning indicators */
  validationResult?: ValidationResult | null;
  /** Whether currently in edit mode */
  isEditMode?: boolean;
  /** Handler for entering edit mode */
  onEdit?: () => void;
  /** Handler for canceling edit mode */
  onCancelEdit?: () => void;
  /** Handler for saving edits */
  onSaveEdit?: () => void;
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
  validationResult,
  isEditMode = false,
  onEdit,
  onCancelEdit,
  onSaveEdit,
  className,
}: ActionGroupProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [inputText, setInputText] = useState("");

  // Validation state derived from result
  const hasErrors = validationResult?.errors && validationResult.errors.length > 0;
  const hasWarnings = validationResult?.warnings && validationResult.warnings.length > 0;
  const warningCount = validationResult?.warnings?.length || 0;

  // Reset editing state when mode changes (e.g., from conversational to hitl)
  useEffect(() => {
    setIsEditing(false);
    setInputText("");
  }, [mode]);

  const handleSubmitText = () => {
    if (!inputText.trim() || !onSecondary) return;
    onSecondary(inputText.trim());
    setInputText("");
    setIsEditing(false);
  };

  // Preview mode - placeholder for unreached stages
  if (mode === "preview") {
    return (
      <div className={cn("px-6 py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
        <div className="flex justify-center items-center h-11">
          <p className="text-sm text-muted-foreground">
            Complete earlier stages to unlock this step
          </p>
        </div>
      </div>
    );
  }

  // Submit mode - single centered button
  if (mode === "submit") {
    return (
      <div className={cn("px-6 py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
        <div className="flex justify-center items-center h-11">
          <Button
            onClick={onPrimary}
            disabled={isDisabled || isLoading}
            size="lg"
            className="gap-2 px-8 bg-orange-500 hover:bg-orange-600"
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
    );
  }

  // Complete mode - Create Another & View Blueprint
  if (mode === "complete") {
    return (
      <div className={cn("px-6 py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
        <div className="flex gap-3 items-center h-11 max-w-md mx-auto">
          <Button
            variant="outline"
            onClick={onCreateAnother}
            className="flex-1"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Create Another
          </Button>
          {blueprintUrl && (
            <Button asChild className="flex-1 bg-orange-500 hover:bg-orange-600">
              <a href={blueprintUrl} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-2" />
                View Blueprint
              </a>
            </Button>
          )}
        </div>
      </div>
    );
  }

  // Text input mode (for revise/reply)
  if (isEditing) {
    return (
      <div className={cn("px-6 py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
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
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
            <Button
              onClick={handleSubmitText}
              disabled={!inputText.trim() || isLoading}
              className="flex-1 bg-orange-500 hover:bg-orange-600"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <MessageSquare className="h-4 w-4 mr-2" />
              )}
              {mode === "conversational" ? "Send" : "Submit Feedback"}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // HITL mode - Approve & Request Changes (or Save/Cancel when editing)
  if (mode === "hitl") {
    // Edit mode: Cancel & Save buttons
    if (isEditMode) {
      return (
        <div className={cn("px-6 py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
          <div className="flex gap-3 items-center h-11 max-w-md mx-auto">
            <Button
              variant="outline"
              onClick={onCancelEdit}
              disabled={isLoading}
              className="flex-1"
            >
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
            <Button
              onClick={onSaveEdit}
              disabled={isDisabled || isLoading || hasErrors}
              className={cn(
                "flex-1",
                hasWarnings && !hasErrors
                  ? "bg-amber-500 hover:bg-amber-600"
                  : "bg-orange-500 hover:bg-orange-600"
              )}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : hasWarnings && !hasErrors ? (
                <AlertTriangle className="h-4 w-4 mr-2" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Save Changes
              {hasWarnings && !hasErrors && ` (${warningCount})`}
            </Button>
          </div>
        </div>
      );
    }

    // Normal HITL mode: Edit, Request Changes, Approve
    return (
      <div className={cn("px-6 py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
        <div className="flex gap-3 items-center h-11 max-w-lg mx-auto">
          {/* Edit button - only show if onEdit is provided */}
          {onEdit && (
            <Button
              variant="outline"
              onClick={onEdit}
              disabled={isLoading}
              className="flex-shrink-0"
            >
              <Edit2 className="h-4 w-4 mr-2" />
              Edit
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() => setIsEditing(true)}
            disabled={isLoading}
            className="flex-1"
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            {secondaryLabel || "Request Changes"}
          </Button>
          <Button
            onClick={onPrimary}
            disabled={isDisabled || isLoading || hasErrors}
            className={cn(
              "flex-1",
              hasWarnings && !hasErrors
                ? "bg-amber-500 hover:bg-amber-600"
                : "bg-orange-500 hover:bg-orange-600"
            )}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : hasWarnings && !hasErrors ? (
              <AlertTriangle className="h-4 w-4 mr-2" />
            ) : (
              <Check className="h-4 w-4 mr-2" />
            )}
            {primaryLabel || "Approve & Continue"}
            {hasWarnings && !hasErrors && ` (${warningCount})`}
          </Button>
        </div>
      </div>
    );
  }

  // Conversational mode - Reply button
  return (
    <div className={cn("px-6 py-4 border-t bg-orange-50 dark:bg-orange-950/30", className)}>
      <div className="flex justify-center items-center h-11">
        <Button
          onClick={() => setIsEditing(true)}
          disabled={isLoading}
          size="lg"
          className="gap-2 px-8 bg-orange-500 hover:bg-orange-600"
        >
          <MessageSquare className="h-4 w-4" />
          {primaryLabel || "Reply"}
        </Button>
      </div>
    </div>
  );
}
