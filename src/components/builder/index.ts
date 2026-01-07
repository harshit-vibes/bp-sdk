/**
 * Builder Components - GuidedChat sub-components
 *
 * Reusable primitives for the statement builder (GuidedChat screen).
 * These components handle selection dialogs, slot triggers, and custom input.
 *
 * Component Hierarchy:
 * - GuidedChat (screens/)
 *   ├── SlotTrigger (clickable slot in statement)
 *   └── SelectorDialog (modal with options)
 *       ├── OptionCard (individual option)
 *       └── CustomInput (type your own)
 *
 * @example
 * ```tsx
 * import { SlotTrigger, SelectorDialog } from "@/components/builder";
 *
 * <SlotTrigger
 *   value={selectedValue}
 *   placeholder="your role"
 *   onClick={() => setOpen(true)}
 * />
 * <SelectorDialog
 *   open={open}
 *   onOpenChange={setOpen}
 *   options={roleOptions}
 *   onSelect={handleSelect}
 * />
 * ```
 */

// Primary exports for GuidedChat
export { SlotTrigger, type SlotTriggerProps } from "./slot-trigger";
export {
  SelectorDialog,
  type SelectorDialogProps,
  type SelectorOption,
} from "./selector-dialog";

// Sub-components (used internally by SelectorDialog)
export { OptionCard, type OptionCardProps } from "./option-card";
export { CustomInput, type CustomInputProps } from "./custom-input";

// Step indicator (for alternative progress display)
export {
  StepIndicator,
  UnifiedStepIndicator,
  type StepIndicatorProps,
  type UnifiedStepIndicatorProps,
  type Step,
  type BuildSubStep,
} from "./step-indicator";

// Action group (shared between screens)
export { ActionGroup, type ActionGroupProps } from "./action-group";

// Info items form (for HITL info_items)
export { InfoItemsForm, type InfoItemsFormProps } from "./info-items-form";

// Agent stepper (for Build stage progress)
export {
  AgentStepper,
  buildAgentSteps,
  type AgentStepperProps,
  type AgentStep,
} from "./agent-stepper";

// Streaming loader (for entertaining loading states)
export {
  StreamingLoader,
  type StreamingLoaderProps,
} from "./streaming-loader";

// README builder (for generating blueprint documentation)
export {
  ReadmeBuilder,
  type ReadmeBuilderProps,
} from "./readme-builder";

// Re-export schema types for convenience
export type { SelectorOption as SchemaOption } from "@/lib/schemas/selector";
