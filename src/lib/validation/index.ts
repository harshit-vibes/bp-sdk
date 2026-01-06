/**
 * Validation Module
 *
 * Exports validation schemas and quality detection utilities.
 */

// Agent validation schema and types
export {
  validateAgentSpec,
  GENERIC_TERMS,
  VALID_FEATURES,
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
