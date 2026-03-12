"""Validation Utilities (Doctor)

Functions to validate agent and blueprint configurations.
Includes schema validation for README-style content quality.
"""

import re

from ..models import AgentConfig, BlueprintConfig, ValidationReport

# Generic terms that should not appear in role
GENERIC_ROLE_TERMS = ["worker", "helper", "bot", "agent", "assistant"]

# Minimum quality thresholds
MIN_DESCRIPTION_LENGTH = 20
MIN_INSTRUCTIONS_LENGTH = 50
MIN_INSTRUCTIONS_WORDS = 10
RECOMMENDED_INSTRUCTIONS_LENGTH = 200

# Patterns for quality checks
PLACEHOLDER_PATTERNS = [
    r"TODO",
    r"FIXME",
    r"XXX",
    r"\[.*\]",  # [placeholder] style
    r"\{.*\}",  # {placeholder} style
    r"lorem ipsum",
    r"example\s+text",
    r"sample\s+text",
]

# Weak instruction patterns
WEAK_INSTRUCTION_PATTERNS = [
    r"^do\s+stuff",
    r"^help\s+user",
    r"^be\s+helpful",
    r"^you\s+are\s+an?\s+(ai|assistant|bot)",
]


def _has_placeholder(text: str) -> bool:
    """Check if text contains placeholder patterns."""
    if not text:
        return False
    lower_text = text.lower()
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, lower_text, re.IGNORECASE):
            return True
    return False


def _has_weak_instructions(text: str) -> bool:
    """Check if instructions are too generic/weak."""
    if not text:
        return False
    lower_text = text.lower().strip()
    for pattern in WEAK_INSTRUCTION_PATTERNS:
        if re.match(pattern, lower_text, re.IGNORECASE):
            return True
    return False


def _count_words(text: str) -> int:
    """Count words in text."""
    if not text:
        return 0
    return len(text.split())


def validate_content_quality(
    field_name: str,
    value: str,
    min_length: int = 0,
    min_words: int = 0,
    check_placeholders: bool = True,
) -> tuple[list[str], list[str]]:
    """Validate content quality for README-style fields.

    Args:
        field_name: Name of field for error messages
        value: Content to validate
        min_length: Minimum character length
        min_words: Minimum word count
        check_placeholders: Whether to check for placeholder text

    Returns:
        Tuple of (errors, warnings)
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not value or not value.strip():
        return errors, warnings  # Empty is handled elsewhere

    text = value.strip()

    # Length check
    if min_length > 0 and len(text) < min_length:
        errors.append(f"{field_name} should be ≥{min_length} chars, got {len(text)}")

    # Word count check
    if min_words > 0 and _count_words(text) < min_words:
        warnings.append(
            f"{field_name} should have ≥{min_words} words for quality, got {_count_words(text)}"
        )

    # Placeholder check
    if check_placeholders and _has_placeholder(text):
        errors.append(f"{field_name} contains placeholder text (TODO, [placeholder], etc.)")

    return errors, warnings


def validate_agent(agent: AgentConfig, is_worker: bool = False) -> ValidationReport:
    """Validate an agent configuration.

    Includes schema validation for README-style content quality:
    - Description: min 20 chars, no placeholders
    - Instructions: min 50 chars, min 10 words, no placeholders, no weak patterns
    - Context: no placeholders (if provided)
    - Goal: 50-300 chars (if provided)
    - Role: 15-80 chars, no generic terms (if provided)

    Args:
        agent: Agent configuration to validate
        is_worker: Whether this agent is a worker (requires usage_description)

    Returns:
        ValidationReport with errors and warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Name validation
    if not agent.name or not agent.name.strip():
        errors.append("Name is required")
    elif len(agent.name) > 100:
        errors.append(f"Name must be ≤100 chars, got {len(agent.name)}")
    elif _has_placeholder(agent.name):
        errors.append("Name contains placeholder text")

    # Description validation with content quality
    if not agent.description or not agent.description.strip():
        errors.append("Description is required")
    else:
        desc_errors, desc_warnings = validate_content_quality(
            "Description",
            agent.description,
            min_length=MIN_DESCRIPTION_LENGTH,
            check_placeholders=True,
        )
        errors.extend(desc_errors)
        warnings.extend(desc_warnings)

    # Instructions validation with content quality
    if not agent.instructions or not agent.instructions.strip():
        errors.append("Instructions are required")
    else:
        instr_errors, instr_warnings = validate_content_quality(
            "Instructions",
            agent.instructions,
            min_length=MIN_INSTRUCTIONS_LENGTH,
            min_words=MIN_INSTRUCTIONS_WORDS,
            check_placeholders=True,
        )
        errors.extend(instr_errors)
        warnings.extend(instr_warnings)

        # Check for weak instruction patterns
        if _has_weak_instructions(agent.instructions):
            warnings.append("Instructions appear too generic (avoid 'be helpful', 'you are an AI')")

        # Recommend longer instructions
        if len(agent.instructions) < RECOMMENDED_INSTRUCTIONS_LENGTH:
            warnings.append(
                f"Consider more detailed instructions (≥{RECOMMENDED_INSTRUCTIONS_LENGTH} chars recommended)"
            )

    # Role validation (if provided)
    if agent.role:
        if len(agent.role) < 15:
            errors.append(f"Role must be ≥15 chars, got {len(agent.role)}")
        elif len(agent.role) > 80:
            errors.append(f"Role must be ≤80 chars, got {len(agent.role)}")

        lower_role = agent.role.lower()
        for term in GENERIC_ROLE_TERMS:
            if term in lower_role:
                errors.append(f"Role should not contain generic term '{term}'")

        if _has_placeholder(agent.role):
            errors.append("Role contains placeholder text")

    # Goal validation (if provided)
    if agent.goal:
        if len(agent.goal) < 50:
            errors.append(f"Goal must be ≥50 chars, got {len(agent.goal)}")
        elif len(agent.goal) > 300:
            errors.append(f"Goal must be ≤300 chars, got {len(agent.goal)}")

        if _has_placeholder(agent.goal):
            errors.append("Goal contains placeholder text")

    # Context validation (if provided)
    if agent.context:
        if _has_placeholder(agent.context):
            errors.append("Context contains placeholder text")

    # Output format validation (if provided)
    if agent.output_format:
        if _has_placeholder(agent.output_format):
            errors.append("Output format contains placeholder text")

    # Examples validation (if provided)
    if agent.examples:
        if _has_placeholder(agent.examples):
            warnings.append("Examples may contain placeholder text")

    # Temperature validation
    if agent.temperature < 0.0 or agent.temperature > 1.0:
        errors.append(f"Temperature must be 0.0-1.0, got {agent.temperature}")

    # Top_p validation
    if agent.top_p < 0.0 or agent.top_p > 1.0:
        errors.append(f"Top_p must be 0.0-1.0, got {agent.top_p}")

    # Worker-specific validation
    if is_worker:
        if not agent.usage_description:
            warnings.append("Workers should have usage_description for better orchestration")
        elif _has_placeholder(agent.usage_description):
            errors.append("Usage description contains placeholder text")

    # Feature validation (handled by Pydantic, but double-check here)
    valid_features = {
        "memory", "voice", "context", "file_output", "image_output",
        "reflection", "groundedness", "fairness", "rai", "llm_judge"
    }
    for feature in agent.features:
        if feature not in valid_features:
            errors.append(f"Unknown feature '{feature}'. Valid: {valid_features}")

    return ValidationReport(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_blueprint(config: BlueprintConfig) -> ValidationReport:
    """Validate a blueprint configuration.

    Includes schema validation for README-style content quality:
    - Blueprint name: max 100 chars, no placeholders
    - Blueprint description: min 20 chars, no placeholders

    Args:
        config: Blueprint configuration to validate

    Returns:
        ValidationReport with all errors and warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Name validation with content quality
    if not config.name or not config.name.strip():
        errors.append("Blueprint name is required")
    elif len(config.name) > 100:
        errors.append(f"Blueprint name must be ≤100 chars, got {len(config.name)}")
    elif _has_placeholder(config.name):
        errors.append("Blueprint name contains placeholder text")

    # Description validation with content quality
    if not config.description or not config.description.strip():
        errors.append("Blueprint description is required")
    else:
        desc_errors, desc_warnings = validate_content_quality(
            "Blueprint description",
            config.description,
            min_length=MIN_DESCRIPTION_LENGTH,
            check_placeholders=True,
        )
        errors.extend(desc_errors)
        warnings.extend(desc_warnings)

    # README validation (mandatory)
    if not config.readme or not config.readme.strip():
        errors.append(
            "Blueprint README is required. "
            "Generate with blueprint-docs agent or add metadata.readme field."
        )
    else:
        # Check README quality - should have key sections
        readme_lower = config.readme.lower()
        required_sections = ["problem", "approach", "capabilities"]
        missing_sections = [
            s for s in required_sections
            if s not in readme_lower
        ]
        if missing_sections:
            warnings.append(
                f"README may be missing sections: {', '.join(missing_sections)}. "
                "Follow Problem-Approach-Capabilities structure."
            )
        if _has_placeholder(config.readme):
            errors.append("README contains placeholder text")

    # Tags validation
    if len(config.tags) > 20:
        errors.append(f"Maximum 20 tags allowed, got {len(config.tags)}")

    # Workers validation - single-agent blueprints are allowed (empty workers)
    # Only require workers if pattern is manager_workers or if sub_agents are used
    has_flat_workers = len(config.workers) > 0
    has_sub_agents = (
        config.manager.sub_agents is not None
        and len(config.manager.sub_agents) > 0
    )
    # Note: Single-agent blueprints (no workers, no sub_agents) are valid

    # Validate manager
    manager_report = validate_agent(config.manager, is_worker=False)
    for e in manager_report.errors:
        errors.append(f"Manager: {e}")
    for w in manager_report.warnings:
        warnings.append(f"Manager: {w}")

    # Validate workers
    for i, worker in enumerate(config.workers):
        worker_report = validate_agent(worker, is_worker=True)
        for e in worker_report.errors:
            errors.append(f"Worker[{i}] '{worker.name}': {e}")
        for w in worker_report.warnings:
            warnings.append(f"Worker[{i}] '{worker.name}': {w}")

    return ValidationReport(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def doctor(config: BlueprintConfig) -> ValidationReport:
    """Run comprehensive validation on a blueprint configuration.

    Alias for validate_blueprint with a friendlier name.

    Args:
        config: Blueprint configuration to validate

    Returns:
        ValidationReport with all errors and warnings
    """
    return validate_blueprint(config)


def validate_blueprint_data(blueprint_data: dict) -> list[str]:
    """Validate raw blueprint_data before deployment.

    This validates the internal structure, not the config.
    Used internally by the SDK before API calls.

    Args:
        blueprint_data: The blueprint_data dict for API

    Returns:
        List of error messages (empty if valid)
    """
    errors: list[str] = []

    if not blueprint_data:
        return ["blueprint_data is empty"]

    # 1. Check manager_agent_id
    manager_id = blueprint_data.get("manager_agent_id")
    if not manager_id:
        errors.append("Missing manager_agent_id")
    elif manager_id not in blueprint_data.get("agents", {}):
        errors.append(f"manager_agent_id '{manager_id}' not in agents dict")

    # 2. Check manager has managed_agents (for multi-agent blueprints)
    agents = blueprint_data.get("agents", {})
    if manager_id and manager_id in agents:
        manager = agents[manager_id]
        managed = manager.get("managed_agents") or []

        # Check all managed agents exist in agents dict
        for ma in managed:
            if ma.get("id") not in agents:
                errors.append(f"Managed agent '{ma.get('id')}' not in agents dict")

    # 4. Check ReactFlow required fields
    for node in blueprint_data.get("nodes", []):
        data = node.get("data", {})
        for field in ["label", "template_type", "tool"]:
            if field not in data:
                errors.append(f"Node '{node.get('id', 'unknown')}': missing {field}")

    # 5. Check tree_structure consistency
    tree = blueprint_data.get("tree_structure", {})
    if tree:
        if tree.get("nodes") != blueprint_data.get("nodes"):
            errors.append("tree_structure.nodes doesn't match nodes")
        if tree.get("edges") != blueprint_data.get("edges"):
            errors.append("tree_structure.edges doesn't match edges")

    return errors
