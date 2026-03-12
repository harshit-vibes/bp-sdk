"""HITL (Human-In-The-Loop) models.

The HITL system enables structured checkpoints where:
1. Agent completes work and presents it (work_summary + preview)
2. Agent asks for specific info-items needed for next step
3. User either:
   - Proceeds: Approves + provides answers to info_items
   - Revises: Requests redo with specific feedback
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class HITLType(str, Enum):
    """Types of HITL checkpoints in the blueprint creation flow."""

    CONFIRM_ARCHITECTURE = "confirm_architecture"
    REVIEW_AGENT = "review_agent"  # NEW: Review individual agent YAML
    REVIEW_BLUEPRINT = "review_blueprint"  # NEW: Final review before creation
    CONFIRM_CREATE = "confirm_create"


class InfoItemType(str, Enum):
    """Types of info items the agent can request."""

    TEXT = "text"  # Free-form text input
    CHOICE = "choice"  # Single choice from options
    MULTI_CHOICE = "multi_choice"  # Multiple choices from options
    CONFIRMATION = "confirmation"  # Yes/No confirmation


class InfoItem(BaseModel):
    """An info item the agent needs from the user for the next step.

    Examples:
        - {"id": "model_preference", "question": "Any model preference?", "type": "choice", "choices": ["gpt-4o", "claude-3-5-sonnet"], "required": False}
        - {"id": "constraints", "question": "Any specific constraints?", "type": "text", "required": False}
        - {"id": "confirm_proceed", "question": "Ready to create the blueprint?", "type": "confirmation", "required": True}
    """

    id: str = Field(..., description="Unique identifier for this info item")
    question: str = Field(..., description="The question to ask the user")
    type: InfoItemType = Field(default=InfoItemType.TEXT, description="Type of input expected")
    choices: Optional[list[str]] = Field(default=None, description="Options for choice/multi_choice types")
    required: bool = Field(default=True, description="Whether this info is required to proceed")
    default: Optional[str] = Field(default=None, description="Default value if not provided")


class HITLSuggestion(BaseModel):
    """A HITL suggestion from the agent.

    The agent outputs this at the end of a step to:
    1. Present the work done (work_summary + preview)
    2. Ask for info needed for the next step (info_items)
    """

    type: HITLType = Field(..., description="The type of HITL checkpoint")
    title: str = Field(..., description="Title for the HITL prompt")
    work_summary: str = Field(
        ...,
        description="Summary of what the agent accomplished in this step",
    )
    info_items: list[InfoItem] = Field(
        default_factory=list,
        description="List of info items needed for the next step",
    )
    preview: Optional[dict[str, Any]] = Field(
        default=None,
        description="Structured preview of the work (architecture, specs, etc.)",
    )


class HITLResponseAction(str, Enum):
    """Actions the user can take in response to HITL."""

    PROCEED = "proceed"  # Approve and continue to next step
    REVISE = "revise"  # Request redo with specific feedback


class HITLResponse(BaseModel):
    """User's response to a HITL checkpoint.

    Examples:
        Proceed: {"action": "proceed", "info_answers": {"model_preference": "gpt-4o", "constraints": "keep it simple"}}
        Revise: {"action": "revise", "feedback": "Focus more on cost efficiency and use gpt-4o-mini for workers"}
    """

    action: HITLResponseAction = Field(..., description="Whether to proceed or revise")
    info_answers: Optional[dict[str, str]] = Field(
        default=None,
        description="Answers to info_items (required if action=proceed and info_items exist)",
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Specific feedback for what to focus on in the redo (required if action=revise)",
    )


class AgentAction(str, Enum):
    """Actions the agent can request via structured output."""

    HITL = "hitl"  # Request human input (includes review_agent with embedded spec)
    CREATE_BLUEPRINT = "create_blueprint"  # Create from saved YAMLs
    CONTINUE = "continue"  # Continue conversation (no action needed)


class AgentYAMLSpec(BaseModel):
    """Agent YAML specification for saving to session.

    This represents a single agent's YAML configuration.
    """

    filename: str = Field(..., description="Filename for the YAML (e.g., 'manager.yaml')")
    is_manager: bool = Field(default=False, description="Whether this is the manager agent")
    agent_index: int = Field(default=0, description="Index in the crafting sequence (0 for manager)")

    # Agent metadata
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")

    # Agent spec
    model: str = Field(default="gpt-4o-mini", description="Model to use")
    temperature: float = Field(default=0.3, description="Temperature setting")
    role: str = Field(..., description="Agent role (15-80 chars)")
    goal: str = Field(..., description="Agent goal (50-300 chars)")
    instructions: str = Field(..., description="Full agent instructions")

    # Worker-specific
    usage_description: Optional[str] = Field(
        default=None,
        description="When to delegate to this worker (required for workers)"
    )

    # Features
    features: list[str] = Field(default_factory=list, description="Agent features like 'memory'")

    # Sub-agents (for manager only)
    sub_agents: list[str] = Field(
        default_factory=list,
        description="List of worker filenames (for manager only)"
    )


class BlueprintYAMLSpec(BaseModel):
    """Blueprint YAML specification for the final blueprint.yaml file."""

    name: str = Field(..., description="Blueprint name")
    description: str = Field(..., description="Blueprint description")
    category: str = Field(default="general", description="Blueprint category")
    tags: list[str] = Field(default_factory=list, description="Blueprint tags")
    visibility: str = Field(default="private", description="Visibility: private, organization, public")

    # Readme content
    readme: Optional[str] = Field(default=None, description="README content for the blueprint")

    # Root agents (manager filename)
    root_agents: list[str] = Field(
        default_factory=list,
        description="List of root agent filenames (typically just the manager)"
    )


class ArchitectureSpec(BaseModel):
    """Architecture specification from the Architect Agent.

    Defines the structure of the blueprint with agent names and roles.
    """

    pattern: str = Field(
        default="manager_workers",
        description="Orchestration pattern: 'single_agent' or 'manager_workers'"
    )

    reasoning: str = Field(..., description="Why this architecture was chosen")

    # Manager info as nested object
    manager: dict[str, str] = Field(
        ...,
        description="Manager agent with 'name' and 'purpose' keys"
    )

    # Workers info (empty if single_agent pattern)
    workers: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of workers with 'name' and 'purpose' keys"
    )

    @property
    def manager_name(self) -> str:
        """Get manager name for backwards compatibility."""
        return self.manager.get("name", "Manager")

    @property
    def manager_purpose(self) -> str:
        """Get manager purpose for backwards compatibility."""
        return self.manager.get("purpose", "")


class BlueprintSpec(BaseModel):
    """Blueprint specification from the agent for creation.

    This is the full configuration needed to create a blueprint via the SDK.
    Used when creating directly without YAML files.
    """

    name: str
    description: str
    category: str = "general"
    tags: list[str] = Field(default_factory=list)

    # Manager config
    manager_name: str
    manager_role: str
    manager_goal: str
    manager_instructions: str
    manager_model: str = "gpt-4o"
    manager_temperature: float = 0.7

    # Workers (list of worker specs)
    workers: list[dict[str, Any]] = Field(default_factory=list)


class StructuredOutput(BaseModel):
    """Structured output from the agent.

    The agent emits this as a JSON block at the end of its response
    when it needs user input or wants to perform an action.

    Schema-guardrailed: The agent MUST follow this exact structure.
    """

    action: AgentAction = Field(..., description="The action the agent wants to take")

    # For HITL action
    hitl: Optional[HITLSuggestion] = Field(
        default=None,
        description="HITL suggestion (required if action=hitl)",
    )

    # For create_blueprint action (using saved YAMLs)
    blueprint_yaml: Optional[BlueprintYAMLSpec] = Field(
        default=None,
        description="Blueprint YAML spec (required if action=create_blueprint)",
    )

    # Legacy: direct blueprint creation without YAMLs
    blueprint: Optional[BlueprintSpec] = Field(
        default=None,
        description="Blueprint spec for direct creation (legacy)",
    )
