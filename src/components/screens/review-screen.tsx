"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";
import { Sparkles, AlertCircle, AlertTriangle, Edit2, Download, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { BlueprintResult } from "@/lib/schemas/review";
import type { InfoItem, AgentYAMLSpec } from "@/lib/types";
import { exportAndDownload } from "@/lib/yaml";
import type { ValidationResult } from "@/lib/validation";
import { InfoItemsForm, AgentStepper, YAMLViewer, type AgentStep } from "@/components/builder";
import { ManagerChat } from "@/components/chat";

export interface ReviewScreenProps {
  /** Markdown content to display */
  content: string;
  /** Whether this is the final "complete" state */
  isComplete?: boolean;
  /** Blueprint result for complete state */
  blueprint?: BlueprintResult;
  /** Info items from HITL suggestion */
  infoItems?: InfoItem[];
  /** Current answers to info items */
  infoAnswers?: Record<string, string>;
  /** Handler for info item changes */
  onInfoChange?: (id: string, value: string) => void;
  /** Whether info items form is disabled */
  infoDisabled?: boolean;
  /** Agent steps for Build stage progress indicator */
  agentSteps?: AgentStep[];
  /** Handler when an agent step is clicked (for navigation) */
  onAgentStepClick?: (index: number) => void;
  /** Validation result for current agent spec */
  validationResult?: ValidationResult | null;
  /** Whether currently in edit mode */
  isEditMode?: boolean;
  /** Edit form items (when in edit mode) */
  editItems?: InfoItem[];
  /** Current edit form answers */
  editAnswers?: Record<string, string>;
  /** Handler for edit form changes */
  onEditChange?: (id: string, value: string) => void;
  /** Agent specs for YAML export (available at completion) */
  agentSpecs?: AgentYAMLSpec[];
  /** Additional class names */
  className?: string;
}

/**
 * ReviewScreen - Markdown display for review stages
 *
 * Shows AI-generated content in markdown format.
 * Action buttons are handled by the parent via ActionGroup in footer.
 *
 * @example
 * ```tsx
 * <ReviewScreen
 *   content={markdownContent}
 *   isComplete={false}
 *   blueprint={blueprintResult}
 * />
 * ```
 */
export function ReviewScreen({
  content,
  isComplete = false,
  blueprint,
  infoItems = [],
  infoAnswers = {},
  onInfoChange,
  infoDisabled = false,
  agentSteps = [],
  onAgentStepClick,
  validationResult,
  isEditMode = false,
  editItems = [],
  editAnswers = {},
  onEditChange,
  agentSpecs = [],
  className,
}: ReviewScreenProps) {
  const hasErrors = validationResult?.errors && validationResult.errors.length > 0;
  const hasWarnings = validationResult?.warnings && validationResult.warnings.length > 0;

  // Export state
  const [isExporting, setIsExporting] = useState(false);

  // Handle YAML export
  const handleExport = async () => {
    if (!blueprint || agentSpecs.length === 0) return;

    setIsExporting(true);
    try {
      await exportAndDownload(blueprint.name, agentSpecs, {
        visibility: blueprint.share_type || "private",
        includeReadme: true,
      });
    } catch (error) {
      console.error("Export failed:", error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Agent stepper for Build stage */}
      {agentSteps.length > 0 && (
        <div className="px-4 py-2 border-b bg-orange-50/50 dark:bg-orange-950/20">
          <AgentStepper
            agents={agentSteps}
            onAgentClick={onAgentStepClick}
          />
        </div>
      )}

      {/* Content area */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Validation alerts - only show errors/warnings, not success */}
        {validationResult && (hasErrors || hasWarnings) && (
          <div className="mb-4 space-y-2">
            {/* Errors */}
            {hasErrors && validationResult.errors.map((err, i) => (
              <div
                key={`error-${i}`}
                className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-300"
              >
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-medium capitalize">{err.field}:</span>{" "}
                  {err.message}
                </div>
              </div>
            ))}
            {/* Warnings */}
            {hasWarnings && validationResult.warnings.map((warn, i) => (
              <div
                key={`warning-${i}`}
                className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg text-sm text-amber-700 dark:text-amber-300"
              >
                <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-medium capitalize">{warn.field}:</span>{" "}
                  {warn.message}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Session YAML files viewer */}
        <YAMLViewer className="mb-4" />

        {/* Edit mode: Show form instead of markdown */}
        {isEditMode && editItems.length > 0 && onEditChange ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground border-b pb-3">
              <Edit2 className="h-4 w-4" />
              <span>Editing Agent Configuration</span>
            </div>
            <InfoItemsForm
              items={editItems}
              answers={editAnswers}
              onChange={onEditChange}
              disabled={false}
            />
          </div>
        ) : (
          /* Normal mode: Show markdown content */
          <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ children }) => (
                <h1 className="text-xl font-bold mb-4 text-foreground">{children}</h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-lg font-semibold mb-3 mt-6 text-foreground">{children}</h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-base font-semibold mb-2 mt-4 text-foreground">{children}</h3>
              ),
              p: ({ children }) => (
                <p className="mb-3 text-sm leading-relaxed text-foreground/90">{children}</p>
              ),
              ul: ({ children }) => (
                <ul className="mb-4 space-y-1 text-sm">{children}</ul>
              ),
              ol: ({ children }) => (
                <ol className="mb-4 space-y-1 text-sm list-decimal list-inside">{children}</ol>
              ),
              li: ({ children }) => (
                <li className="text-foreground/90">{children}</li>
              ),
              code: ({ className, children, ...props }) => {
                const isInline = !className;
                return isInline ? (
                  <code className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono" {...props}>
                    {children}
                  </code>
                ) : (
                  <code
                    className={cn(
                      "block p-3 rounded-lg bg-muted text-xs font-mono overflow-x-auto",
                      className
                    )}
                    {...props}
                  >
                    {children}
                  </code>
                );
              },
              pre: ({ children }) => (
                <pre className="mb-4 rounded-lg overflow-hidden">{children}</pre>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-orange-500 pl-4 my-4 italic text-muted-foreground">
                  {children}
                </blockquote>
              ),
              table: ({ children }) => (
                <div className="overflow-x-auto mb-4">
                  <table className="min-w-full text-sm border-collapse">{children}</table>
                </div>
              ),
              th: ({ children }) => (
                <th className="border border-border px-3 py-2 bg-muted text-left font-semibold">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="border border-border px-3 py-2">{children}</td>
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
        )}

        {/* Info items form for HITL */}
        {infoItems.length > 0 && onInfoChange && (
          <InfoItemsForm
            items={infoItems}
            answers={infoAnswers}
            onChange={onInfoChange}
            disabled={infoDisabled}
            className="mt-6"
          />
        )}

        {/* Blueprint info card for complete state */}
        {isComplete && blueprint && (
          <div className="mt-6 p-6 rounded-xl bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-950/40 dark:to-amber-950/40 border-2 border-orange-200 dark:border-orange-800">
            <div className="flex items-center gap-3 mb-4">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-orange-500 text-white">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">{blueprint.name}</h3>
                <p className="text-xs text-muted-foreground">Blueprint Created Successfully</p>
              </div>
            </div>

            {/* Blueprint Metadata */}
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="p-2 rounded-lg bg-white/50 dark:bg-black/20">
                <span className="text-xs text-muted-foreground block">Blueprint ID</span>
                <code className="text-xs font-mono">{blueprint.id}</code>
              </div>
              {blueprint.manager_id && (
                <div className="p-2 rounded-lg bg-white/50 dark:bg-black/20">
                  <span className="text-xs text-muted-foreground block">Manager ID</span>
                  <code className="text-xs font-mono">{blueprint.manager_id}</code>
                </div>
              )}
              {blueprint.organization_id && (
                <div className="p-2 rounded-lg bg-white/50 dark:bg-black/20">
                  <span className="text-xs text-muted-foreground block">Organization ID</span>
                  <code className="text-xs font-mono">{blueprint.organization_id}</code>
                </div>
              )}
              {blueprint.share_type && (
                <div className="p-2 rounded-lg bg-white/50 dark:bg-black/20">
                  <span className="text-xs text-muted-foreground block">Visibility</span>
                  <span className="text-xs capitalize">{blueprint.share_type}</span>
                </div>
              )}
              {blueprint.created_at && (
                <div className="p-2 rounded-lg bg-white/50 dark:bg-black/20 col-span-2">
                  <span className="text-xs text-muted-foreground block">Created At</span>
                  <span className="text-xs">{new Date(blueprint.created_at).toLocaleString()}</span>
                </div>
              )}
            </div>

            {/* Export to YAML button */}
            {agentSpecs.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleExport}
                disabled={isExporting}
                className="mt-4 w-full border-orange-300 hover:bg-orange-100 dark:border-orange-700 dark:hover:bg-orange-900/30"
              >
                {isExporting ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                {isExporting ? "Exporting..." : "Export to YAML"}
              </Button>
            )}

            {/* Manager Chat */}
            {blueprint.manager_id && (
              <ManagerChat
                managerId={blueprint.manager_id}
                className="mt-4"
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
