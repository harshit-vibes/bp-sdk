/**
 * Validation Module
 *
 * Exports validation schemas, quality detection utilities, and gate validators.
 */

// Agent validation schema and types (quality checks)
export {
  validateAgentSpec,
  GENERIC_TERMS,
  VALID_FEATURES,
  VALID_MODELS,
  FIELD_CONSTRAINTS,
  type ValidationError,
  type ValidationWarning,
  type ValidationResult,
} from "./agent-schema";

// Quality detection utilities
export {
  detectPlaceholders,
  detectWeakInstructions,
  detectGenericTerms,
  isTooShort,
  hasTooFewWords,
  isMostlyUppercase,
  checkFieldQuality,
  ROLE_GENERIC_TERMS,
  type QualityIssue,
} from "./quality";

// Stage transition gates (Zod schema validators)
export {
  validateArchitectureGate,
  validateAgentGate,
  validateAgentSpecAuto,
  validateBlueprintGate,
  buildAndValidateBlueprintRequest,
  isValidArchitecture,
  isValidAgentSpec,
  isValidBlueprintRequest,
  validateAllAgentSpecs,
  type GateResult,
} from "./gates";
