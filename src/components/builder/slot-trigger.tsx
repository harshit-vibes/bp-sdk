"use client";

import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SlotTriggerProps {
  /** Current selected value */
  value: string | null;
  /** Placeholder text when no value selected */
  placeholder: string;
  /** Click handler to open selector */
  onClick: () => void;
  /** Additional class names */
  className?: string;
  /** Whether the trigger is disabled */
  disabled?: boolean;
  /** Size variant */
  size?: "sm" | "md" | "lg";
}

const sizeClasses = {
  sm: "text-base md:text-lg",
  md: "text-xl md:text-2xl",
  lg: "text-2xl md:text-3xl",
};

const iconSizeClasses = {
  sm: "h-3 w-3 md:h-4 md:w-4",
  md: "h-4 w-4 md:h-5 md:w-5",
  lg: "h-5 w-5 md:h-6 md:w-6",
};

/**
 * SlotTrigger - Inline clickable slot that triggers a selector dialog
 *
 * Used in statement builders and HITL interactions where users need to
 * select from options or provide custom input.
 *
 * @example
 * ```tsx
 * <SlotTrigger
 *   value={selectedType}
 *   placeholder="type of system"
 *   onClick={() => setDialogOpen(true)}
 * />
 * ```
 */
export function SlotTrigger({
  value,
  placeholder,
  onClick,
  className,
  disabled = false,
  size = "lg",
}: SlotTriggerProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "inline-flex items-baseline gap-1 transition-all",
        "border-b-2 border-dashed hover:border-solid",
        "font-semibold",
        sizeClasses[size],
        value
          ? "text-orange-500 border-orange-400"
          : "text-muted-foreground/70 border-muted-foreground/40 hover:border-orange-400 hover:text-orange-500",
        disabled && "opacity-50 cursor-not-allowed hover:border-muted-foreground/40 hover:text-muted-foreground/70",
        className
      )}
    >
      <span>{value || placeholder}</span>
      <ChevronDown className={cn("shrink-0 opacity-50", iconSizeClasses[size])} />
    </button>
  );
}
