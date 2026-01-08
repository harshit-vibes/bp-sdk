"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Edit2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { BlueprintResult } from "@/lib/schemas/review";
import type { InfoItem } from "@/lib/types";
import { InfoItemsForm, StreamingLoader } from "@/components/builder";
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
  /** Whether currently in edit mode */
  isEditMode?: boolean;
  /** Edit form items (when in edit mode) */
  editItems?: InfoItem[];
  /** Current edit form answers */
  editAnswers?: Record<string, string>;
  /** Handler for edit form changes */
  onEditChange?: (id: string, value: string) => void;
  /** Whether currently loading (show streaming loader) */
  isLoading?: boolean;
  /** Current builder stage for loader context */
  builderStage?: string;
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
  isEditMode = false,
  editItems = [],
  editAnswers = {},
  onEditChange,
  isLoading = false,
  builderStage = "",
  className,
}: ReviewScreenProps) {
  // Note: validationResult removed from props - quality issues handled in background

  // In complete mode with chat, use flex layout to fill space
  const isCompleteWithChat = isComplete && blueprint && blueprint.manager_id;

  return (
    <div className={cn("flex flex-col flex-1 min-h-0", className)}>
      {/* Content area - flex layout when showing chat playground */}
      <div className={cn(
        "flex-1 min-h-0 p-4 sm:p-6",
        isCompleteWithChat ? "flex flex-col" : "overflow-y-auto"
      )}>
        {/* Loading state: Show streaming loader */}
        {isLoading ? (
          <StreamingLoader
            stage={builderStage}
            isActive={isLoading}
          />
        ) : isEditMode && editItems.length > 0 && onEditChange ? (
          /* Edit mode: Show form instead of markdown */
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground border-b pb-3">
              <Edit2 className="h-4 w-4" />
              <span>Edit Details</span>
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
          <div className={cn(
            "prose prose-sm dark:prose-invert max-w-none prose-headings:text-foreground prose-p:text-foreground/90",
            isCompleteWithChat && "flex-shrink-0"
          )}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ children }) => (
                <h1 className="text-xl sm:text-2xl font-bold mb-3 mt-2 text-foreground">{children}</h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-base sm:text-lg font-semibold mb-2 mt-6 text-orange-600 dark:text-orange-400 uppercase tracking-wide">
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-base sm:text-lg font-semibold mb-1 mt-3 text-foreground">{children}</h3>
              ),
              h4: ({ children }) => (
                <h4 className="text-sm sm:text-base font-semibold mb-1 mt-3 text-foreground/90">{children}</h4>
              ),
              p: ({ children }) => (
                <p className="mb-3 text-sm leading-relaxed text-foreground/80">{children}</p>
              ),
              ul: ({ children }) => (
                <ul className="mb-3 ml-1 space-y-1.5 text-sm list-none">{children}</ul>
              ),
              ol: ({ children }) => (
                <ol className="mb-3 ml-1 space-y-1.5 text-sm list-decimal list-inside">{children}</ol>
              ),
              li: ({ children }) => (
                <li className="text-foreground/80 flex items-start gap-2">
                  <span className="text-orange-500 mt-1 flex-shrink-0 text-xs">●</span>
                  <span>{children}</span>
                </li>
              ),
              strong: ({ children }) => (
                <strong className="font-semibold text-foreground">{children}</strong>
              ),
              em: ({ children }) => (
                <em className="italic text-foreground/70">{children}</em>
              ),
              code: ({ className, children, ...props }) => {
                const isInline = !className;
                return isInline ? (
                  <code
                    className="px-1.5 py-0.5 rounded bg-muted text-foreground text-xs font-mono"
                    {...props}
                  >
                    {children}
                  </code>
                ) : (
                  <code
                    className={cn(
                      "block p-3 rounded-lg bg-muted text-foreground text-xs font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed",
                      className
                    )}
                    {...props}
                  >
                    {children}
                  </code>
                );
              },
              pre: ({ children }) => (
                <pre className="mb-3 rounded-lg overflow-hidden bg-muted">{children}</pre>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-2 border-orange-400 pl-3 py-1 my-3 text-sm italic text-foreground/70">
                  {children}
                </blockquote>
              ),
              hr: () => (
                <hr className="my-4 border-t border-border/50" />
              ),
              table: ({ children }) => (
                <div className="overflow-x-auto mb-3 rounded-lg border border-border">
                  <table className="min-w-full text-sm border-collapse">{children}</table>
                </div>
              ),
              th: ({ children }) => (
                <th className="border-b border-border px-3 py-2 bg-muted text-left font-semibold text-foreground text-xs">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="border-b border-border px-3 py-2 text-foreground/80 text-sm">{children}</td>
              ),
              a: ({ children, href }) => (
                <a href={href} className="text-orange-600 dark:text-orange-400 underline underline-offset-2 hover:text-orange-700 dark:hover:text-orange-300" target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
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

        {/* Blueprint complete state - Chat-focused UI (fills remaining space) */}
        {isCompleteWithChat && blueprint.manager_id && (
          <ManagerChat
            managerId={blueprint.manager_id}
            blueprintId={blueprint.id}
            className="flex-1 min-h-0"
          />
        )}
      </div>
    </div>
  );
}
