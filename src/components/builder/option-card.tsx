"use client";

import { type LucideIcon, Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface OptionCardProps {
  /** Display label for the option */
  label: string;
  /** Value to be submitted when selected */
  value: string;
  /** Optional description text */
  description?: string;
  /** Optional icon component */
  icon?: LucideIcon;
  /** Whether this option is currently selected */
  isSelected: boolean;
  /** Click handler */
  onClick: () => void;
  /** Additional class names */
  className?: string;
  /** Whether the card is disabled */
  disabled?: boolean;
}

/**
 * OptionCard - Selectable option card for selector dialogs
 *
 * Used within SelectorDialog to display individual options.
 * Shows a checkmark when selected, supports icons and descriptions.
 *
 * @example
 * ```tsx
 * <OptionCard
 *   label="Customer Support"
 *   value="customer support system"
 *   description="Handle inquiries and tickets"
 *   icon={Headphones}
 *   isSelected={selected === "customer support system"}
 *   onClick={() => onSelect("customer support system")}
 * />
 * ```
 */
export function OptionCard({
  label,
  value,
  description,
  icon: Icon,
  isSelected,
  onClick,
  className,
  disabled = false,
}: OptionCardProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "relative px-4 py-3 rounded-xl text-left transition-all",
        "border-2",
        isSelected
          ? "border-orange-500 bg-orange-500 text-white shadow-lg"
          : "border-orange-200 dark:border-orange-800 bg-white/80 dark:bg-black/20",
        !isSelected &&
          !disabled &&
          "hover:border-orange-400 hover:bg-orange-50 dark:hover:bg-orange-950/30",
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
    >
      <div className="flex items-start gap-3">
        {Icon && (
          <Icon
            className={cn(
              "h-5 w-5 shrink-0 mt-0.5",
              isSelected ? "text-white" : "text-orange-500"
            )}
          />
        )}
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium">{label}</div>
          {description && (
            <div
              className={cn(
                "text-xs mt-0.5",
                isSelected ? "text-white/80" : "text-muted-foreground"
              )}
            >
              {description}
            </div>
          )}
        </div>
      </div>
      {isSelected && (
        <Check className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4" />
      )}
    </button>
  );
}
