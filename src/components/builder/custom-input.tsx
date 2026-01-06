"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export interface CustomInputProps {
  /** Placeholder text for the input */
  placeholder?: string;
  /** Label text above the input */
  label?: string;
  /** Handler when custom value is submitted */
  onSubmit: (value: string) => void;
  /** Button text */
  buttonText?: string;
  /** Whether to use textarea instead of input */
  multiline?: boolean;
  /** Additional class names for the container */
  className?: string;
  /** Whether the input is disabled */
  disabled?: boolean;
  /** Minimum length required */
  minLength?: number;
}

/**
 * CustomInput - Text input section for custom values in selector dialogs
 *
 * Allows users to type their own value instead of selecting from options.
 * Supports both single-line input and multiline textarea.
 *
 * @example
 * ```tsx
 * <CustomInput
 *   label="Or type your own"
 *   placeholder="e.g., customer support system"
 *   onSubmit={(value) => handleSelect(value)}
 *   buttonText="Use"
 * />
 * ```
 */
export function CustomInput({
  placeholder = "Type your own...",
  label = "Or type your own",
  onSubmit,
  buttonText = "Use",
  multiline = false,
  className,
  disabled = false,
  minLength = 1,
}: CustomInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (trimmed.length >= minLength) {
      onSubmit(trimmed);
      setValue("");
    }
  }, [value, minLength, onSubmit]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const isValid = value.trim().length >= minLength;

  const InputComponent = multiline ? Textarea : Input;

  return (
    <div
      className={cn(
        "pt-3 border-t border-orange-200 dark:border-orange-800",
        className
      )}
    >
      {label && (
        <p className="text-xs text-muted-foreground mb-2 text-center">{label}</p>
      )}
      <div className={cn("flex gap-2", multiline && "flex-col")}>
        <InputComponent
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          onKeyDown={handleKeyDown}
          className={cn(
            "flex-1 border-orange-200 dark:border-orange-800",
            "focus-visible:ring-orange-500",
            multiline && "min-h-[80px] resize-none"
          )}
        />
        <Button
          onClick={handleSubmit}
          disabled={disabled || !isValid}
          size={multiline ? "default" : "sm"}
          className={cn(
            "bg-orange-500 hover:bg-orange-600",
            multiline && "self-end"
          )}
        >
          {buttonText}
        </Button>
      </div>
    </div>
  );
}
