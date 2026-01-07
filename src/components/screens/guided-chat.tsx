"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { SlotTrigger, SelectorDialog, type SelectorOption } from "@/components/builder";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  type StatementSlot,
  type StatementTemplate,
  type SelectorOption as SchemaOption,
  DEFAULT_STATEMENT_TEMPLATE,
  buildStatement,
  isStatementComplete,
} from "@/lib/schemas/selector";

/**
 * Convert schema options to dialog-compatible options
 * (strips the icon field since schema uses string, dialog uses LucideIcon)
 */
function toDialogOptions(schemaOptions: SchemaOption[]): SelectorOption[] {
  return schemaOptions.map(({ icon, disabled, ...rest }) => rest);
}

/**
 * Fetch dynamic options from API
 */
async function fetchSlotOptions(
  slotType: string,
  context?: { role?: string; problem?: string }
): Promise<SelectorOption[]> {
  try {
    const response = await fetch("/api/builder/options", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slot_type: slotType, context }),
    });

    if (response.ok) {
      const data = await response.json();
      return data.options || [];
    }
  } catch {
    // Fall through to return empty
  }
  return [];
}

/**
 * Fetch witty loading text from API
 */
async function fetchWittyText(slotType: string, contextStr?: string): Promise<string> {
  try {
    const context = contextStr || `Selecting ${slotType}`;
    const response = await fetch(
      `/api/builder/loader-text?stage=options&context=${encodeURIComponent(context)}`
    );
    if (response.ok) {
      const data = await response.json();
      return data.text || "Finding the best options...";
    }
  } catch {
    // Fallback
  }
  return "Finding the best options...";
}

export interface GuidedChatProps {
  /** Statement template configuration */
  template?: StatementTemplate;
  /** Initial slot selections (for restoring state when navigating back) */
  initialSelections?: Record<string, string | null>;
  /** Callback when statement changes (reports canSubmit and statement) */
  onStatementChange?: (canSubmit: boolean, statement: string | null) => void;
  /** Callback when selections change (for persisting state) */
  onSelectionsChange?: (selections: Record<string, string | null>) => void;
  /** Whether the form is disabled (read-only mode) */
  disabled?: boolean;
  /** Additional class names */
  className?: string;
}

/**
 * SlotSelector - Individual slot with dialog and dynamic options
 *
 * Options are fetched dynamically based on context (previous selections).
 * When context changes, options are re-fetched to provide relevant choices.
 */
function SlotSelector({
  slot,
  value,
  onChange,
  context,
  disabled = false,
}: {
  slot: StatementSlot;
  value: string | null;
  onChange: (value: string) => void;
  context?: { role?: string; problem?: string; domain?: string };
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [dynamicOptions, setDynamicOptions] = useState<SelectorOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [wittyText, setWittyText] = useState("Finding the best options...");
  const wittyIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Track last context to detect changes
  const lastContextRef = useRef<string>("");
  const currentContextKey = JSON.stringify(context || {});

  // Start fetching witty text on interval while loading
  const startWittyTextUpdates = useCallback(() => {
    // Build context string for witty text
    const contextParts: string[] = [`Selecting ${slot.id}`];
    if (context?.role) contextParts.push(`for ${context.role}`);
    if (context?.problem) contextParts.push(`about ${context.problem}`);
    const contextStr = contextParts.join(" ");

    // Fetch initial text
    fetchWittyText(slot.id, contextStr).then(setWittyText);

    // Update every 2.5 seconds
    wittyIntervalRef.current = setInterval(() => {
      fetchWittyText(slot.id, contextStr).then(setWittyText);
    }, 2500);
  }, [slot.id, context]);

  // Stop witty text updates
  const stopWittyTextUpdates = useCallback(() => {
    if (wittyIntervalRef.current) {
      clearInterval(wittyIntervalRef.current);
      wittyIntervalRef.current = null;
    }
  }, []);

  // Fetch options - always re-fetch if context changed
  const fetchOptions = useCallback(async () => {
    setIsLoading(true);
    startWittyTextUpdates();

    try {
      const options = await fetchSlotOptions(slot.id, context);
      if (options.length > 0) {
        setDynamicOptions(options);
      } else {
        // Fallback to static options from template
        setDynamicOptions(toDialogOptions(slot.options));
      }
    } catch {
      // Use static fallback
      setDynamicOptions(toDialogOptions(slot.options));
    } finally {
      setIsLoading(false);
      stopWittyTextUpdates();
      lastContextRef.current = currentContextKey;
    }
  }, [slot.id, slot.options, context, currentContextKey, startWittyTextUpdates, stopWittyTextUpdates]);

  // Fetch options when dialog opens
  const handleOpen = useCallback(async () => {
    // Don't open if disabled
    if (disabled) return;

    setOpen(true);

    // Re-fetch if context changed or never fetched
    const contextChanged = lastContextRef.current !== currentContextKey;
    const neverFetched = dynamicOptions.length === 0;

    if (contextChanged || neverFetched) {
      await fetchOptions();
    }
  }, [disabled, currentContextKey, dynamicOptions.length, fetchOptions]);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopWittyTextUpdates();
  }, [stopWittyTextUpdates]);

  // Use dynamic options if available, otherwise static
  const dialogOptions = dynamicOptions.length > 0
    ? dynamicOptions
    : toDialogOptions(slot.options);

  return (
    <>
      <SlotTrigger
        value={value}
        placeholder={slot.placeholder}
        onClick={handleOpen}
        disabled={disabled}
      />
      <SelectorDialog
        open={open}
        onOpenChange={setOpen}
        title={slot.title}
        description={slot.description}
        options={isLoading ? [] : dialogOptions}
        value={value}
        onSelect={onChange}
        allowCustom={slot.allowCustom}
        customLabel={slot.customLabel || "Or describe in your own words"}
        customPlaceholder={slot.customPlaceholder || `Describe your ${slot.placeholder}...`}
        preview={
          isLoading ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-orange-500" />
              <span className="text-sm text-muted-foreground animate-pulse">
                {wittyText}
              </span>
            </div>
          ) : undefined
        }
      />
    </>
  );
}

/**
 * GuidedChat - Statement builder with dropdown selectors
 *
 * A guided statement builder where users can select options from dropdowns
 * OR type custom values. This is NOT a traditional chat - it's a mad-libs
 * style form that constructs a problem statement.
 *
 * After submission, the flow goes directly to ReviewScreen.
 *
 * @example
 * ```tsx
 * <GuidedChat
 *   template={DEFAULT_STATEMENT_TEMPLATE}
 *   isLoading={isLoading}
 *   onSubmit={handleStatementSubmit}
 * />
 * ```
 */
export function GuidedChat({
  template = DEFAULT_STATEMENT_TEMPLATE,
  initialSelections,
  onStatementChange,
  onSelectionsChange,
  disabled = false,
  className,
}: GuidedChatProps) {
  // Initialize selections - use initialSelections if provided, otherwise null for each slot
  const [selections, setSelections] = useState<Record<string, string | null>>(
    () => {
      const initial: Record<string, string | null> = {};
      template.slots.forEach((slot) => {
        initial[slot.id] = initialSelections?.[slot.id] ?? null;
      });
      return initial;
    }
  );

  const handleSelect = (slotId: string, value: string) => {
    setSelections((prev) => ({ ...prev, [slotId]: value }));
  };

  // Notify parent of statement changes (using effect to avoid setState during render)
  useEffect(() => {
    const canSubmit = isStatementComplete(template, selections);
    const statement = canSubmit ? buildStatement(template, selections) : null;
    onStatementChange?.(canSubmit, statement);
  }, [selections, template, onStatementChange]);

  // Notify parent of selections changes for state persistence
  useEffect(() => {
    onSelectionsChange?.(selections);
  }, [selections, onSelectionsChange]);

  // Build context from current selections for a given slot
  // Context includes all selections made BEFORE this slot in the sequence
  const getContextForSlot = (slotId: string): { role?: string; problem?: string; domain?: string } => {
    const context: { role?: string; problem?: string; domain?: string } = {};
    const slotOrder = template.slots.map(s => s.id);
    const currentIndex = slotOrder.indexOf(slotId);

    // Include all selections from previous slots
    for (let i = 0; i < currentIndex; i++) {
      const prevSlotId = slotOrder[i];
      const prevValue = selections[prevSlotId];
      if (prevValue) {
        context[prevSlotId as keyof typeof context] = prevValue;
      }
    }

    return context;
  };

  // Render the template with slot selectors
  const renderStatement = () => {
    // Parse template: "As a {role}, I need to {problem} in {domain}."
    const parts: React.ReactNode[] = [];
    let remaining = template.template;
    let key = 0;

    template.slots.forEach((slot) => {
      const placeholder = `{${slot.id}}`;
      const index = remaining.indexOf(placeholder);

      if (index !== -1) {
        // Add text before the placeholder
        if (index > 0) {
          parts.push(
            <span key={`text-${key++}`} className="text-foreground">
              {remaining.substring(0, index)}
            </span>
          );
        }

        // Build context from previous selections
        const context = getContextForSlot(slot.id);

        // Add the slot selector with context
        parts.push(
          <SlotSelector
            key={`slot-${slot.id}`}
            slot={slot}
            value={selections[slot.id]}
            onChange={(v) => handleSelect(slot.id, v)}
            context={context}
            disabled={disabled}
          />
        );

        remaining = remaining.substring(index + placeholder.length);
      }
    });

    // Add any remaining text
    if (remaining) {
      parts.push(
        <span key={`text-${key++}`} className="text-foreground">
          {remaining}
        </span>
      );
    }

    return parts;
  };

  return (
    <div className={cn("flex items-center justify-center h-full overflow-auto p-4 sm:p-6", className)}>
      <div className="max-w-xl text-center">
        {/* Problem-focused statement */}
        <div className="text-lg sm:text-xl md:text-2xl font-light leading-relaxed tracking-tight">
          {renderStatement()}
        </div>
      </div>
    </div>
  );
}
