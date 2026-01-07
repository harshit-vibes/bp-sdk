"use client";

import { useState, useEffect, useRef } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface StreamingLoaderProps {
  /** Current builder stage for context */
  stage: string;
  /** Additional context (e.g., agent name) */
  context?: string;
  /** Whether to show the loader */
  isActive: boolean;
  /** Additional class names */
  className?: string;
}

/**
 * StreamingLoader - Entertaining loading component with streaming witty text
 *
 * Connects to the loader-stream SSE endpoint and displays
 * fun, contextual loading messages that update every few seconds.
 *
 * @example
 * ```tsx
 * <StreamingLoader
 *   stage="crafting"
 *   context="Sales Manager Agent"
 *   isActive={isLoading}
 * />
 * ```
 */
export function StreamingLoader({
  stage,
  context = "",
  isActive,
  className,
}: StreamingLoaderProps) {
  const [text, setText] = useState("Working on it...");
  const [isVisible, setIsVisible] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!isActive) {
      // Close connection when not active
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      setIsVisible(false);
      return;
    }

    // Show loader
    setIsVisible(true);
    setText("Working on it...");

    // Build URL with query params
    const url = new URL("/api/builder/loader-stream", window.location.origin);
    url.searchParams.set("stage", stage);
    if (context) {
      url.searchParams.set("context", context);
    }

    // Create EventSource for SSE
    const eventSource = new EventSource(url.toString());
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.text) {
          // Sanitize text - skip problematic responses
          let cleanText = data.text.replace(/\\n/g, " ").replace(/\\/g, "").trim();
          if (
            cleanText &&
            !cleanText.includes("[Request") &&
            !cleanText.includes("[Error") &&
            cleanText.length > 5 &&
            cleanText.length < 100
          ) {
            setText(cleanText);
          }
        }
      } catch {
        // Ignore parse errors
      }
    };

    eventSource.onerror = () => {
      // Connection error, close and use fallback
      eventSource.close();
      eventSourceRef.current = null;
    };

    // Cleanup on unmount or when isActive changes
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [isActive, stage, context]);

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 px-4",
        className
      )}
    >
      {/* Spinning loader */}
      <div className="relative mb-6">
        <Loader2 className="h-12 w-12 animate-spin text-orange-500" />
        <div className="absolute inset-0 blur-xl bg-orange-500/20 animate-pulse" />
      </div>

      {/* Streaming text with fade animation */}
      <p
        key={text}
        className="text-center text-muted-foreground text-sm max-w-md animate-in fade-in duration-500"
      >
        {text}
      </p>
    </div>
  );
}
