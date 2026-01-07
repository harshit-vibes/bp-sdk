"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  FileText,
  Loader2,
  RefreshCw,
  Edit2,
  Check,
  X,
  Copy,
  Download,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export interface ReadmeBuilderProps {
  /** Generated README content */
  readme: string | null;
  /** Whether README is being generated */
  isLoading: boolean;
  /** Error message if generation failed */
  error: string | null;
  /** Blueprint name for display */
  blueprintName?: string;
  /** Callback to generate README */
  onGenerate: () => Promise<void>;
  /** Callback to update README content */
  onUpdate: (content: string) => void;
  /** Callback to clear README */
  onClear: () => void;
  /** Additional class names */
  className?: string;
}

/**
 * ReadmeBuilder - Generate and edit README for blueprints
 *
 * Features:
 * - One-click README generation using AI
 * - Markdown preview with syntax highlighting
 * - Edit mode for manual modifications
 * - Copy to clipboard
 * - Download as .md file
 */
export function ReadmeBuilder({
  readme,
  isLoading,
  error,
  blueprintName = "Blueprint",
  onGenerate,
  onUpdate,
  onClear,
  className,
}: ReadmeBuilderProps) {
  const [isEditMode, setIsEditMode] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [copySuccess, setCopySuccess] = useState(false);

  // Enter edit mode
  const handleEdit = () => {
    setEditContent(readme || "");
    setIsEditMode(true);
  };

  // Save edits
  const handleSave = () => {
    onUpdate(editContent);
    setIsEditMode(false);
  };

  // Cancel edits
  const handleCancel = () => {
    setEditContent("");
    setIsEditMode(false);
  };

  // Copy to clipboard
  const handleCopy = async () => {
    if (!readme) return;
    try {
      await navigator.clipboard.writeText(readme);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  // Download as file
  const handleDownload = () => {
    if (!readme) return;
    const blob = new Blob([readme], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${blueprintName.toLowerCase().replace(/\s+/g, "-")}-readme.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Regenerate README
  const handleRegenerate = () => {
    onClear();
    onGenerate();
  };

  return (
    <div className={cn("flex flex-col", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-orange-500" />
          <h3 className="font-semibold">README</h3>
        </div>

        {/* Actions */}
        {readme && !isEditMode && (
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-8 px-2"
            >
              {copySuccess ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDownload}
              className="h-8 px-2"
            >
              <Download className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEdit}
              className="h-8 px-2"
            >
              <Edit2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRegenerate}
              disabled={isLoading}
              className="h-8 px-2"
            >
              <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
            </Button>
          </div>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="flex items-center gap-2 p-3 mb-4 rounded-lg bg-destructive/10 text-destructive text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Content */}
      {!readme && !isLoading ? (
        /* No README - Show generate button */
        <div className="flex flex-col items-center justify-center py-8 px-4 rounded-lg border-2 border-dashed border-muted-foreground/25">
          <FileText className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <p className="text-sm text-muted-foreground text-center mb-4">
            Generate a professional README for your blueprint with AI
          </p>
          <Button
            onClick={onGenerate}
            disabled={isLoading}
            className="bg-orange-500 hover:bg-orange-600"
          >
            <FileText className="h-4 w-4 mr-2" />
            Generate README
          </Button>
          <p className="text-xs text-muted-foreground/70 mt-3 text-center">
            Follows Problem-Approach-Capabilities structure
          </p>
        </div>
      ) : isLoading ? (
        /* Loading state */
        <div className="flex flex-col items-center justify-center py-12 px-4">
          <Loader2 className="h-8 w-8 animate-spin text-orange-500 mb-4" />
          <p className="text-sm text-muted-foreground">Generating README...</p>
          <p className="text-xs text-muted-foreground/70 mt-1">
            This may take up to 60 seconds
          </p>
        </div>
      ) : isEditMode ? (
        /* Edit mode */
        <div className="flex flex-col gap-3">
          <Textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            placeholder="Write your README in markdown..."
            className="min-h-[300px] font-mono text-sm"
          />
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={handleCancel}>
              <X className="h-4 w-4 mr-1" />
              Cancel
            </Button>
            <Button size="sm" onClick={handleSave}>
              <Check className="h-4 w-4 mr-1" />
              Save
            </Button>
          </div>
        </div>
      ) : (
        /* Markdown preview */
        <div className="prose prose-sm dark:prose-invert max-w-none overflow-y-auto max-h-[400px] p-4 rounded-lg border bg-muted/30">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h2: ({ children }) => (
                <h2 className="text-base font-semibold mb-2 mt-6 first:mt-0 text-orange-600 dark:text-orange-400 uppercase tracking-wide border-b pb-1">
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-sm font-semibold mb-1 mt-3 text-foreground">
                  {children}
                </h3>
              ),
              p: ({ children }) => (
                <p className="mb-2 text-sm leading-relaxed text-foreground/80">
                  {children}
                </p>
              ),
              ul: ({ children }) => (
                <ul className="mb-2 ml-1 space-y-1 text-sm list-none">
                  {children}
                </ul>
              ),
              li: ({ children }) => (
                <li className="text-foreground/80 flex items-start gap-2">
                  <span className="text-orange-500 mt-0.5 flex-shrink-0 text-xs">
                    -
                  </span>
                  <span>{children}</span>
                </li>
              ),
              strong: ({ children }) => (
                <strong className="font-semibold text-foreground">
                  {children}
                </strong>
              ),
              hr: () => <hr className="my-4 border-t border-border/50" />,
              blockquote: ({ children }) => (
                <blockquote className="border-l-2 border-orange-400 pl-3 py-1 my-2 text-sm italic text-foreground/70">
                  {children}
                </blockquote>
              ),
              code: ({ children }) => (
                <code className="px-1 py-0.5 rounded bg-muted text-foreground text-xs font-mono">
                  {children}
                </code>
              ),
            }}
          >
            {readme}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}
