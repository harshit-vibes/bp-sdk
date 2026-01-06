"use client";

import { useState, useMemo } from "react";
import { HelpCircle } from "lucide-react";
import type { InfoItem } from "@/lib/types";
import { SlotTrigger, SelectorDialog, type SelectorOption } from "@/components/builder";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { getFieldGuidance } from "@/lib/guidance";

// Model presets for the model selector
const MODEL_PRESETS = [
  { value: "gpt-4o", label: "GPT-4o", provider: "OpenAI" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini", provider: "OpenAI" },
  { value: "gpt-4.1", label: "GPT-4.1", provider: "OpenAI" },
  { value: "gpt-4.1-mini", label: "GPT-4.1 Mini", provider: "OpenAI" },
  { value: "anthropic/claude-sonnet-4-20250514", label: "Claude Sonnet 4", provider: "Anthropic" },
  { value: "anthropic/claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet", provider: "Anthropic" },
  { value: "anthropic/claude-3-5-haiku-20241022", label: "Claude 3.5 Haiku", provider: "Anthropic" },
  { value: "gemini/gemini-2.0-flash", label: "Gemini 2.0 Flash", provider: "Google" },
  { value: "gemini/gemini-1.5-pro", label: "Gemini 1.5 Pro", provider: "Google" },
  { value: "groq/llama-3.3-70b-versatile", label: "Llama 3.3 70B", provider: "Groq" },
];

/**
 * FieldLabel - Label with optional tooltip guidance
 */
function FieldLabel({
  id,
  label,
  required,
  htmlFor,
  className,
}: {
  id: string;
  label: string;
  required?: boolean;
  htmlFor?: string;
  className?: string;
}) {
  const guidance = getFieldGuidance(id);

  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <Label htmlFor={htmlFor} className="text-sm font-medium">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </Label>
      {guidance && (
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              className="inline-flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
            >
              <HelpCircle className="h-3.5 w-3.5" />
              <span className="sr-only">Help</span>
            </button>
          </TooltipTrigger>
          <TooltipContent side="right" className="max-w-xs">
            <div className="space-y-1.5">
              <p>{guidance.tooltip}</p>
              {guidance.example && (
                <p className="text-xs opacity-80">
                  <span className="font-medium">Example:</span> {guidance.example}
                </p>
              )}
              {guidance.warning && (
                <p className="text-xs text-amber-200">
                  <span className="font-medium">Note:</span> {guidance.warning}
                </p>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      )}
    </div>
  );
}

export interface InfoItemsFormProps {
  /** Info items from HITL suggestion */
  items: InfoItem[];
  /** Current answers */
  answers: Record<string, string>;
  /** Called when an answer changes */
  onChange: (id: string, value: string) => void;
  /** Additional class names */
  className?: string;
  /** Whether the form is disabled (e.g., during loading) */
  disabled?: boolean;
}

/**
 * Single choice item using SelectorDialog
 */
function ChoiceItem({
  item,
  value,
  onChange,
  disabled,
}: {
  item: InfoItem;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);

  const options: SelectorOption[] = useMemo(
    () =>
      (item.choices || []).map((choice) => ({
        value: choice,
        label: choice,
      })),
    [item.choices]
  );

  return (
    <div className="space-y-2">
      <FieldLabel id={item.id} label={item.question} required={item.required} />
      <div>
        <SlotTrigger
          value={value || null}
          placeholder="Select an option"
          onClick={() => setOpen(true)}
          disabled={disabled}
          size="sm"
        />
        <SelectorDialog
          open={open}
          onOpenChange={setOpen}
          title={item.question}
          options={options}
          value={value || null}
          onSelect={onChange}
          allowCustom={false}
        />
      </div>
    </div>
  );
}

/**
 * Multi-choice item using checkboxes
 */
function MultiChoiceItem({
  item,
  value,
  onChange,
  disabled,
}: {
  item: InfoItem;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  // Value is stored as comma-separated string
  const selectedValues = useMemo(
    () => (value ? value.split(",").map((v) => v.trim()) : []),
    [value]
  );

  const handleToggle = (choice: string, checked: boolean) => {
    let newSelected: string[];
    if (checked) {
      newSelected = [...selectedValues, choice];
    } else {
      newSelected = selectedValues.filter((v) => v !== choice);
    }
    onChange(newSelected.join(", "));
  };

  return (
    <div className="space-y-2">
      <FieldLabel id={item.id} label={item.question} required={item.required} />
      <div className="space-y-2">
        {(item.choices || []).map((choice) => (
          <div key={choice} className="flex items-center space-x-2">
            <Checkbox
              id={`${item.id}-${choice}`}
              checked={selectedValues.includes(choice)}
              onCheckedChange={(checked) => handleToggle(choice, !!checked)}
              disabled={disabled}
            />
            <Label
              htmlFor={`${item.id}-${choice}`}
              className="text-sm font-normal cursor-pointer"
            >
              {choice}
            </Label>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Text input item
 */
function TextItem({
  item,
  value,
  onChange,
  disabled,
}: {
  item: InfoItem;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <div className="space-y-2">
      <FieldLabel id={item.id} label={item.question} required={item.required} htmlFor={item.id} />
      <Input
        id={item.id}
        value={value || item.default || ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={item.default || "Enter your response..."}
        disabled={disabled}
        className="border-orange-200 focus-visible:ring-orange-500"
      />
    </div>
  );
}

/**
 * Confirmation checkbox item
 */
function ConfirmationItem({
  item,
  value,
  onChange,
  disabled,
}: {
  item: InfoItem;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const isChecked = value === "yes" || value === "true";
  const guidance = getFieldGuidance(item.id);

  return (
    <div className="flex items-start space-x-3 py-2">
      <Checkbox
        id={item.id}
        checked={isChecked}
        onCheckedChange={(checked) => onChange(checked ? "yes" : "no")}
        disabled={disabled}
        className="mt-0.5"
      />
      <div className="flex items-center gap-1.5">
        <Label
          htmlFor={item.id}
          className="text-sm font-medium leading-relaxed cursor-pointer"
        >
          {item.question}
          {item.required && <span className="text-red-500 ml-1">*</span>}
        </Label>
        {guidance && (
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                className="inline-flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
              >
                <HelpCircle className="h-3.5 w-3.5" />
                <span className="sr-only">Help</span>
              </button>
            </TooltipTrigger>
            <TooltipContent side="right" className="max-w-xs">
              <p>{guidance.tooltip}</p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </div>
  );
}

/**
 * Textarea item with character counter
 */
function TextareaItem({
  item,
  value,
  onChange,
  disabled,
}: {
  item: InfoItem;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const charCount = value?.length || 0;
  const minLength = item.minLength || 0;
  const maxLength = item.maxLength;
  const rows = item.rows || 4;

  const isUnderMin = minLength > 0 && charCount < minLength;
  const isOverMax = maxLength && charCount > maxLength;

  return (
    <div className="space-y-2">
      <FieldLabel id={item.id} label={item.question} required={item.required} htmlFor={item.id} />
      <Textarea
        id={item.id}
        value={value || item.default || ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={item.placeholder || item.default || "Enter your response..."}
        disabled={disabled}
        rows={rows}
        className={cn(
          "border-orange-200 focus-visible:ring-orange-500 resize-none",
          isUnderMin && "border-amber-400",
          isOverMax && "border-red-400"
        )}
      />
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>
          {minLength > 0 && (
            <span className={isUnderMin ? "text-amber-600" : ""}>
              Min: {minLength} chars
            </span>
          )}
        </span>
        <span className={cn(isOverMax && "text-red-600")}>
          {charCount}
          {maxLength && ` / ${maxLength}`}
        </span>
      </div>
    </div>
  );
}

/**
 * Number item with slider for values like temperature
 */
function NumberItem({
  item,
  value,
  onChange,
  disabled,
}: {
  item: InfoItem;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const min = item.minValue ?? 0;
  const max = item.maxValue ?? 1;
  const step = item.step ?? 0.1;
  const numValue = parseFloat(value) || parseFloat(item.default || "0.7");

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <FieldLabel id={item.id} label={item.question} required={item.required} htmlFor={item.id} />
        <span className="text-sm font-mono bg-muted px-2 py-0.5 rounded">
          {numValue.toFixed(2)}
        </span>
      </div>
      <input
        type="range"
        id={item.id}
        min={min}
        max={max}
        step={step}
        value={numValue}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full h-2 bg-orange-200 rounded-lg appearance-none cursor-pointer accent-orange-500 disabled:opacity-50 disabled:cursor-not-allowed"
      />
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}

/**
 * Model selector item with presets
 */
function ModelItem({
  item,
  value,
  onChange,
  disabled,
}: {
  item: InfoItem;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);

  const options: SelectorOption[] = useMemo(() => {
    // Group by provider
    const grouped = MODEL_PRESETS.reduce((acc, model) => {
      if (!acc[model.provider]) {
        acc[model.provider] = [];
      }
      acc[model.provider].push(model);
      return acc;
    }, {} as Record<string, typeof MODEL_PRESETS>);

    // Flatten with provider labels
    const result: SelectorOption[] = [];
    Object.entries(grouped).forEach(([provider, models]) => {
      result.push({
        value: `__header_${provider}`,
        label: provider,
        disabled: true,
      });
      models.forEach((model) => {
        result.push({
          value: model.value,
          label: `  ${model.label}`,
        });
      });
    });
    return result;
  }, []);

  // Find display label for current value
  const displayLabel = useMemo(() => {
    const preset = MODEL_PRESETS.find((m) => m.value === value);
    return preset ? `${preset.label} (${preset.provider})` : value || "Select model";
  }, [value]);

  return (
    <div className="space-y-2">
      <FieldLabel id={item.id} label={item.question} required={item.required} />
      <div>
        <SlotTrigger
          value={value ? displayLabel : null}
          placeholder="Select a model"
          onClick={() => setOpen(true)}
          disabled={disabled}
          size="sm"
        />
        <SelectorDialog
          open={open}
          onOpenChange={setOpen}
          title="Select Model"
          options={options}
          value={value || null}
          onSelect={(v) => {
            // Don't select header items
            if (!v.startsWith("__header_")) {
              onChange(v);
            }
          }}
          allowCustom={true}
        />
      </div>
      {value && (
        <div className="text-xs text-muted-foreground font-mono">
          {value}
        </div>
      )}
    </div>
  );
}

/**
 * InfoItemsForm - Display and collect answers to HITL info items
 *
 * Reuses the slot-based pattern from GuidedChat to display info items
 * from the agent's HITL suggestion. Supports choice, multi_choice,
 * text, and confirmation types.
 *
 * @example
 * ```tsx
 * <InfoItemsForm
 *   items={hitl.info_items}
 *   answers={infoAnswers}
 *   onChange={(id, value) => setInfoAnswer(id, value)}
 * />
 * ```
 */
export function InfoItemsForm({
  items,
  answers,
  onChange,
  className,
  disabled = false,
}: InfoItemsFormProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div
        className={cn(
          "space-y-6 p-4 rounded-lg border border-orange-200 bg-orange-50/50 dark:bg-orange-950/20",
          className
        )}
      >
        <div className="text-sm font-medium text-muted-foreground">
          Please provide the following information:
        </div>
      {items.map((item) => {
        const value = answers[item.id] || "";

        switch (item.type) {
          case "choice":
            return (
              <ChoiceItem
                key={item.id}
                item={item}
                value={value}
                onChange={(v) => onChange(item.id, v)}
                disabled={disabled}
              />
            );

          case "multi_choice":
            return (
              <MultiChoiceItem
                key={item.id}
                item={item}
                value={value}
                onChange={(v) => onChange(item.id, v)}
                disabled={disabled}
              />
            );

          case "confirmation":
            return (
              <ConfirmationItem
                key={item.id}
                item={item}
                value={value}
                onChange={(v) => onChange(item.id, v)}
                disabled={disabled}
              />
            );

          case "textarea":
            return (
              <TextareaItem
                key={item.id}
                item={item}
                value={value}
                onChange={(v) => onChange(item.id, v)}
                disabled={disabled}
              />
            );

          case "number":
            return (
              <NumberItem
                key={item.id}
                item={item}
                value={value}
                onChange={(v) => onChange(item.id, v)}
                disabled={disabled}
              />
            );

          case "model":
            return (
              <ModelItem
                key={item.id}
                item={item}
                value={value}
                onChange={(v) => onChange(item.id, v)}
                disabled={disabled}
              />
            );

          case "text":
          default:
            return (
              <TextItem
                key={item.id}
                item={item}
                value={value}
                onChange={(v) => onChange(item.id, v)}
                disabled={disabled}
              />
            );
        }
      })}
      </div>
    </TooltipProvider>
  );
}
