"use client";

import { type ReactNode } from "react";
import { type LucideIcon } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { OptionCard } from "./option-card";
import { CustomInput } from "./custom-input";
import { cn } from "@/lib/utils";

export interface SelectorOption {
  /** Display label for the option */
  label: string;
  /** Value to be submitted when selected */
  value: string;
  /** Optional description text */
  description?: string;
  /** Optional icon component */
  icon?: LucideIcon;
  /** Whether the option is disabled (e.g., for headers/dividers) */
  disabled?: boolean;
}

export interface SelectorDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Handler when dialog open state changes */
  onOpenChange: (open: boolean) => void;
  /** Dialog title */
  title: string;
  /** Optional dialog description */
  description?: string;
  /** Available options to select from */
  options: SelectorOption[];
  /** Currently selected value */
  value: string | null;
  /** Handler when a value is selected */
  onSelect: (value: string) => void;
  /** Whether to show custom input section */
  allowCustom?: boolean;
  /** Placeholder for custom input */
  customPlaceholder?: string;
  /** Label for custom input section */
  customLabel?: string;
  /** Whether custom input should be multiline */
  customMultiline?: boolean;
  /** Number of columns for options grid */
  columns?: 1 | 2 | 3;
  /** Optional preview content to show above options */
  preview?: ReactNode;
  /** Additional class names for dialog content */
  className?: string;
}

const columnClasses = {
  1: "grid-cols-1",
  2: "grid-cols-2",
  3: "grid-cols-3",
};

/**
 * SelectorDialog - Modal dialog for selecting from options or custom input
 *
 * A reusable dialog component for the blueprint builder journey.
 * Used for statement building, HITL interactions, and any selection flow.
 *
 * @example
 * ```tsx
 * // Statement slot selection
 * <SelectorDialog
 *   open={open}
 *   onOpenChange={setOpen}
 *   title="What problem are you solving?"
 *   options={problemOptions}
 *   value={selectedProblem}
 *   onSelect={handleSelect}
 *   allowCustom
 *   customPlaceholder="Describe your problem..."
 * />
 *
 * // HITL architecture confirmation
 * <SelectorDialog
 *   open={open}
 *   onOpenChange={setOpen}
 *   title="Review Proposed Architecture"
 *   description="Based on your requirements, we suggest this structure"
 *   options={[
 *     { value: "approve", label: "Looks good", icon: Check },
 *     { value: "revise", label: "I have feedback", icon: MessageSquare },
 *   ]}
 *   preview={<ArchitecturePreview />}
 *   allowCustom
 *   customMultiline
 *   customLabel="What would you like to change?"
 * />
 * ```
 */
export function SelectorDialog({
  open,
  onOpenChange,
  title,
  description,
  options,
  value,
  onSelect,
  allowCustom = true,
  customPlaceholder,
  customLabel = "Or type your own",
  customMultiline = false,
  columns = 2,
  preview,
  className,
}: SelectorDialogProps) {
  const handleSelect = (selectedValue: string) => {
    onSelect(selectedValue);
    onOpenChange(false);
  };

  // Generate default placeholder from first option
  const defaultPlaceholder = options[0]
    ? `e.g., ${options[0].value}`
    : "Type your own...";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={cn(
          "sm:max-w-md border-0 shadow-2xl",
          "bg-gradient-to-br from-orange-50 to-amber-50",
          "dark:from-orange-950/40 dark:to-amber-950/40",
          className
        )}
      >
        <DialogHeader>
          <DialogTitle className="text-xl font-medium text-center">
            {title}
          </DialogTitle>
          {description && (
            <DialogDescription className="text-center">
              {description}
            </DialogDescription>
          )}
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Optional preview content */}
          {preview && (
            <div className="mb-4 pb-4 border-b border-orange-200 dark:border-orange-800">
              {preview}
            </div>
          )}

          {/* Options grid */}
          {options.length > 0 && (
            <div className={cn("grid gap-2", columnClasses[columns])}>
              {options.map((option) => (
                <OptionCard
                  key={option.value}
                  label={option.label}
                  value={option.value}
                  description={option.description}
                  icon={option.icon}
                  isSelected={value === option.value}
                  onClick={() => handleSelect(option.value)}
                />
              ))}
            </div>
          )}

          {/* Custom input section */}
          {allowCustom && (
            <CustomInput
              label={customLabel}
              placeholder={customPlaceholder || defaultPlaceholder}
              onSubmit={handleSelect}
              multiline={customMultiline}
              buttonText="Use"
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
