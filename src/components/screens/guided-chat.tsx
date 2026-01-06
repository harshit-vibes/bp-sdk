"use client";

import { useState, useMemo, useEffect } from "react";
import { SlotTrigger, SelectorDialog, type SelectorOption } from "@/components/builder";
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

export interface GuidedChatProps {
  /** Statement template configuration */
  template?: StatementTemplate;
  /** Callback when statement changes (reports canSubmit and statement) */
  onStatementChange?: (canSubmit: boolean, statement: string | null) => void;
  /** Additional class names */
  className?: string;
}

/**
 * SlotSelector - Individual slot with dialog
 */
function SlotSelector({
  slot,
  value,
  onChange,
}: {
  slot: StatementSlot;
  value: string | null;
  onChange: (value: string) => void;
}) {
  const [open, setOpen] = useState(false);

  // Convert schema options to dialog-compatible options
  const dialogOptions = useMemo(() => toDialogOptions(slot.options), [slot.options]);

  return (
    <>
      <SlotTrigger
        value={value}
        placeholder={slot.placeholder}
        onClick={() => setOpen(true)}
      />
      <SelectorDialog
        open={open}
        onOpenChange={setOpen}
        title={slot.title}
        description={slot.description}
        options={dialogOptions}
        value={value}
        onSelect={onChange}
        allowCustom={slot.allowCustom}
        customLabel={slot.customLabel || "Or describe in your own words"}
        customPlaceholder={slot.customPlaceholder || `Describe your ${slot.placeholder}...`}
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
  onStatementChange,
  className,
}: GuidedChatProps) {
  // Initialize selections with null for each slot
  const [selections, setSelections] = useState<Record<string, string | null>>(
    () => {
      const initial: Record<string, string | null> = {};
      template.slots.forEach((slot) => {
        initial[slot.id] = null;
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

        // Add the slot selector
        parts.push(
          <SlotSelector
            key={`slot-${slot.id}`}
            slot={slot}
            value={selections[slot.id]}
            onChange={(v) => handleSelect(slot.id, v)}
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
    <div className={cn("flex items-center justify-center h-full overflow-auto p-6", className)}>
      <div className="max-w-xl text-center">
        {/* Problem-focused statement */}
        <div className="text-xl md:text-2xl font-light leading-relaxed tracking-tight">
          {renderStatement()}
        </div>
      </div>
    </div>
  );
}
