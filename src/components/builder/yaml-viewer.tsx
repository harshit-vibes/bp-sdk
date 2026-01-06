"use client";

import { useState } from "react";
import { FileCode, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useYAMLSession } from "@/lib/stores";

export interface YAMLViewerProps {
  /** Additional class names */
  className?: string;
}

/**
 * YAMLViewer - Shows saved YAML files during the builder session
 *
 * Displays a flat list of agent and blueprint YAML files
 * stored in the session. Each file shows filename with a copy button.
 */
export function YAMLViewer({ className }: YAMLViewerProps) {
  const { files, agentPaths, blueprintPaths, fileCount } = useYAMLSession();
  const [copiedPath, setCopiedPath] = useState<string | null>(null);

  // Don't render if no files
  if (fileCount === 0) {
    return null;
  }

  const handleCopy = async (path: string, content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedPath(path);
      setTimeout(() => setCopiedPath(null), 2000);
    } catch {
      console.error("Failed to copy to clipboard");
    }
  };

  const getFilename = (path: string) => {
    return path.split("/").pop() || path;
  };

  return (
    <div className={cn("border rounded-lg bg-muted/30 p-3", className)}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <FileCode className="h-4 w-4 text-orange-500" />
        <span className="text-sm font-medium">Session Files ({fileCount})</span>
      </div>

      {/* Flat file list */}
      <div className="space-y-1">
        {agentPaths.map((path) => (
          <YAMLFileItem
            key={path}
            filename={getFilename(path)}
            isCopied={copiedPath === path}
            onCopy={() => handleCopy(path, files[path])}
          />
        ))}
        {blueprintPaths.map((path) => (
          <YAMLFileItem
            key={path}
            filename={getFilename(path)}
            isCopied={copiedPath === path}
            onCopy={() => handleCopy(path, files[path])}
          />
        ))}
      </div>
    </div>
  );
}

interface YAMLFileItemProps {
  filename: string;
  isCopied: boolean;
  onCopy: () => void;
}

function YAMLFileItem({
  filename,
  isCopied,
  onCopy,
}: YAMLFileItemProps) {
  return (
    <div className="flex items-center justify-between px-2 py-1.5 rounded border bg-background">
      <span className="text-xs font-mono truncate">{filename}</span>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 w-6 p-0 flex-shrink-0"
        onClick={onCopy}
        title="Copy YAML content"
      >
        {isCopied ? (
          <Check className="h-3 w-3 text-green-500" />
        ) : (
          <Copy className="h-3 w-3 text-muted-foreground" />
        )}
      </Button>
    </div>
  );
}
