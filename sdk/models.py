"""Pydantic Models for bp-sdk

Configuration and response models for blueprints and agents.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator, model_validator

if TYPE_CHECKING:
    pass  # For type hints only


class Visibility(str, Enum):
    """Blueprint visibility/sharing type."""

    PRIVATE = "private"
    ORGANIZATION = "organization"
    PUBLIC = "public"
    SPECIFIC_USERS = "specific_users"


class AgentConfig(BaseModel):
    """Configuration for creating an agent.

    Used when defining agents for a new blueprint.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    description: str = Field(..., min_length=1, description="Agent description")
    instructions: str = Field(..., min_length=1, description="Agent instructions/prompt")

    # Optional persona fields (stored in native API fields)
    role: str | None = Field(
        None,
        min_length=15,
        max_length=80,
        description="Agent role (15-80 chars, avoid generic terms)",
    )
    goal: str | None = Field(
        None,
        min_length=50,
        max_length=300,
        description="Agent goal (50-300 chars)",
    )
    context: str | None = Field(
        None,
        description="Background context, domain knowledge, operating environment",
    )
    output_format: str | None = Field(
        None,
        description="Output format specifications and structure requirements",
    )
    examples: str | None = Field(
        None,
        description="Few-shot conversation examples (multiline string, not array)",
    )

    # LLM configuration
    model: str = Field(default="gpt-4o", description="LLM model name")
    temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="LLM temperature")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="LLM top_p")
    response_format: str = Field(
        default="text",
        description="LLM response format: 'text' or 'json_object'",
    )
    store_messages: bool = Field(
        default=True,
        description="Whether to store conversation messages for session history",
    )
    file_output: bool = Field(
        default=False,
        description="Enable file output generation (docx, pdf, csv, ppt)",
    )

    # Features (LLM card configurations only - no tools/RAGs)
    features: list[str] = Field(
        default_factory=list,
        description="""List of LLM features to enable:
        - 'memory': Conversation history (2-50 messages)
        - 'voice': Voice synthesis for voice agents
        - 'context': Global context attachment
        - 'file_output': Generate downloadable files (docx, pdf, csv, ppt)
        - 'image_output': Generate images
        - 'reflection': Self-critique for accuracy
        - 'groundedness': Fact verification against context
        - 'fairness': Bias detection and reduction
        - 'rai': Responsible AI policy (toxicity, PII, prompt injection)
        - 'llm_judge': LLM-based response quality assessment
        """,
    )

    # Worker-specific (used when this agent is a worker)
    usage_description: str | None = Field(
        None,
        description="How the manager should use this worker (required for workers)",
    )

    # Nested agents (for hierarchical orchestration)
    sub_agents: list[AgentConfig] | None = Field(
        None,
        description="Nested sub-agents managed by this agent (for deep hierarchies)",
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is None:
            return v
        generic_terms = ["worker", "helper", "bot", "agent", "assistant"]
        lower_v = v.lower()
        for term in generic_terms:
            if term in lower_v:
                raise ValueError(f"Role should not contain generic term '{term}'")
        return v

    @field_validator("response_format")
    @classmethod
    def validate_response_format(cls, v: str) -> str:
        valid_formats = {"text", "json_object"}
        if v not in valid_formats:
            raise ValueError(f"response_format must be 'text' or 'json_object', got '{v}'")
        return v

    @field_validator("features")
    @classmethod
    def validate_features(cls, v: list[str]) -> list[str]:
        valid_features = {
            # LLM card configurations only
            "memory",
            "voice",
            "context",
            "file_output",
            "image_output",
            "reflection",
            "groundedness",
            "fairness",
            "rai",
            "llm_judge",
        }
        for feature in v:
            if feature not in valid_features:
                raise ValueError(f"Unknown feature '{feature}'. Valid: {valid_features}")
        return v


# Rebuild model to resolve forward reference for sub_agents
AgentConfig.model_rebuild()


class AgentUpdate(BaseModel):
    """Update configuration for an existing agent.

    All fields are optional - only provided fields are updated.
    """

    id: str = Field(..., description="Agent API ID to update")

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1)
    instructions: str | None = Field(None, min_length=1)
    role: str | None = Field(None, min_length=15, max_length=80)
    goal: str | None = Field(None, min_length=50, max_length=300)
    context: str | None = None
    output_format: str | None = None
    examples: str | None = None
    model: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=1.0)
    top_p: float | None = Field(None, ge=0.0, le=1.0)
    response_format: str | None = Field(None, description="'text' or 'json_object'")
    store_messages: bool | None = Field(None, description="Store conversation messages")
    file_output: bool | None = Field(None, description="Enable file output generation")
    features: list[str] | None = None
    usage_description: str | None = None


class BlueprintConfig(BaseModel):
    """Configuration for creating a new blueprint.

    Defines the manager, workers, and metadata for a blueprint.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Blueprint name")
    description: str = Field(..., min_length=1, description="Blueprint description")

    # Agent definitions
    manager: AgentConfig = Field(..., description="Manager agent configuration")
    workers: list[AgentConfig] = Field(
        default_factory=list,
        description="Worker agent configurations (can be empty if manager.sub_agents is used)",
    )

    # Catalog metadata
    category: str | None = Field(None, description="Blueprint category")
    tags: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Blueprint tags (max 20)",
    )

    # Visibility
    visibility: Visibility = Field(
        default=Visibility.PRIVATE, description="Blueprint visibility"
    )

    # Documentation
    readme: str | None = Field(
        None,
        description="Blueprint README in markdown format (shown in blueprint detail page)",
    )

    # Template flag
    is_template: bool = Field(
        default=False,
        description="Whether this is a template blueprint",
    )

    # Sharing lists
    shared_with_users: list[str] = Field(
        default_factory=list,
        description="User IDs to share this blueprint with",
    )
    shared_with_organizations: list[str] = Field(
        default_factory=list,
        description="Organization IDs to share this blueprint with",
    )

    # Marketplace publishing (auto-publishes manager agent)
    publish_to_marketplace: bool = Field(
        default=True,
        description="Whether to publish manager agent to marketplace on creation",
    )
    marketplace_name: str | None = Field(
        None,
        description="App name in marketplace (defaults to blueprint name)",
    )
    marketplace_description: str | None = Field(
        None,
        description="App description in marketplace (defaults to blueprint description)",
    )
    welcome_message: str | None = Field(
        None,
        description="Welcome message shown when users open the marketplace app",
    )
    industry: str | None = Field(
        None,
        description="Industry tag for marketplace (e.g., 'Banking & Financial Services')",
    )
    function: str | None = Field(
        None,
        description="Function tag for marketplace (e.g., 'Marketing', 'Sales')",
    )
    marketplace_category: str | None = Field(
        None,
        description="Category tag for marketplace (e.g., 'Productivity & Cost Savings')",
    )

    # Note: Single-agent blueprints (no workers) are valid
    # The validate_has_workers_or_sub_agents validator was removed to support
    # single_agent pattern where only a manager is needed

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return v


class BlueprintUpdate(BaseModel):
    """Update configuration for an existing blueprint.

    All fields are optional - only provided fields are updated.
    """

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1)
    category: str | None = None
    tags: list[str] | None = None
    visibility: Visibility | None = None
    readme: str | None = Field(None, description="Blueprint README in markdown format")

    # Agent updates
    manager: AgentUpdate | None = Field(
        None, description="Manager update (id not required, uses blueprint's manager)"
    )
    workers: list[AgentUpdate] | None = Field(
        None, description="Worker updates (each must have id)"
    )

    # Marketplace publishing (publishes/updates manager agent in marketplace)
    publish_to_marketplace: bool = Field(
        default=True,
        description="Whether to publish/update manager agent in marketplace",
    )
    marketplace_name: str | None = Field(
        None,
        description="App name in marketplace (defaults to blueprint name)",
    )
    marketplace_description: str | None = Field(
        None,
        description="App description in marketplace (defaults to blueprint description)",
    )
    welcome_message: str | None = Field(
        None,
        description="Welcome message shown when users open the marketplace app",
    )
    industry: str | None = Field(
        None,
        description="Industry tag for marketplace",
    )
    function: str | None = Field(
        None,
        description="Function tag for marketplace",
    )
    marketplace_category: str | None = Field(
        None,
        description="Category tag for marketplace",
    )


class ListFilters(BaseModel):
    """Filters for listing blueprints."""

    # Pagination
    page_size: int = Field(default=50, ge=1, le=100)
    page: int = Field(default=1, ge=1)

    # Basic filters
    category: str | None = None
    search: str | None = None
    visibility: Visibility | None = None

    # Advanced filters (from production API)
    orchestration_type: str | None = Field(
        None, description="Filter by type: 'Manager Agent', 'Single Agent', etc."
    )
    tags: list[str] | None = Field(None, description="Filter by tags")
    owner_id: str | None = Field(None, description="Filter by owner ID")
    is_template: bool | None = Field(None, description="Filter by template status")
    sort_by: str | None = Field(
        None, description="Sort field: 'created_at', 'updated_at', 'name'"
    )

    # Legacy alias
    @property
    def limit(self) -> int:
        return self.page_size


class Blueprint(BaseModel):
    """Full blueprint returned from API.

    This is the response model, not used for creation.
    """

    id: str = Field(..., description="Blueprint API ID")
    name: str
    description: str

    # Agent IDs
    manager_id: str = Field(..., description="Manager agent API ID")
    worker_ids: list[str] = Field(..., description="Worker agent API IDs")

    # Status and metadata
    visibility: Visibility
    status: str
    version: str
    category: str | None = None
    tags: list[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Orchestration info (from production)
    orchestration_type: str = Field(default="Manager Agent")
    orchestration_name: str = Field(default="")

    # Ownership (from production)
    owner_id: str | None = None
    organization_id: str | None = None

    # Template and clone info (from production)
    is_template: bool = Field(default=False)
    parent_blueprint_id: str | None = Field(
        None, description="Source blueprint ID if this was cloned"
    )

    # Usage tracking (from production)
    usage_count: int = Field(default=0)
    last_used_at: datetime | None = None
    published_at: datetime | None = None

    # Permissions (computed by API)
    is_owner: bool = Field(default=False)
    can_edit: bool = Field(default=False)
    can_share: bool = Field(default=False)
    can_delete: bool = Field(default=False)

    # Sharing lists
    shared_with_users: list[str] = Field(default_factory=list)
    shared_with_organizations: list[str] = Field(default_factory=list)

    # Raw data access
    blueprint_data: dict | None = Field(None, description="Full ReactFlow tree data")
    blueprint_info: dict | None = Field(None, description="Additional metadata")

    # Marketplace info (populated when published)
    marketplace_app_id: str | None = Field(
        None, description="Marketplace app ID if published"
    )

    # Convenience properties
    @property
    def studio_url(self) -> str:
        """URL to view this blueprint in Lyzr Studio."""
        return f"https://studio.lyzr.ai/lyzr-manager?blueprint={self.id}"

    @property
    def marketplace_url(self) -> str | None:
        """URL to view this blueprint's manager agent in the marketplace."""
        if self.marketplace_app_id:
            return f"https://studio.lyzr.ai/agent/{self.marketplace_app_id}"
        return None

    @property
    def readme(self) -> str | None:
        """Get README markdown content from blueprint_info."""
        if not self.blueprint_info:
            return None
        doc_data = self.blueprint_info.get("documentation_data", {})
        return doc_data.get("markdown")

    @classmethod
    def from_api_response(
        cls,
        data: dict,
        manager_id: str,
        worker_ids: list[str],
        marketplace_app_id: str | None = None,
    ) -> "Blueprint":
        """Create Blueprint from API response data.

        Args:
            data: Raw API response dict
            manager_id: Manager agent ID
            worker_ids: List of worker agent IDs
            marketplace_app_id: Optional marketplace app ID if published
        """
        return cls(
            id=data.get("_id") or data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            manager_id=manager_id,
            worker_ids=worker_ids,
            visibility=Visibility(data.get("share_type", "private")),
            status=data.get("status", "draft"),
            version=str(data.get("version", "1.0.0")),
            category=data.get("category"),
            tags=data.get("tags", []),
            created_at=_parse_datetime(data.get("created_at"), default_to_now=True),
            updated_at=_parse_datetime(data.get("updated_at"), default_to_now=True),
            # Orchestration
            orchestration_type=data.get("orchestration_type", "Manager Agent"),
            orchestration_name=data.get("orchestration_name", ""),
            # Ownership
            owner_id=data.get("owner_id"),
            organization_id=data.get("organization_id"),
            # Template/clone
            is_template=data.get("is_template", False),
            parent_blueprint_id=data.get("parent_blueprint_id"),
            # Usage
            usage_count=data.get("usage_count", 0),
            last_used_at=_parse_datetime(data.get("last_used_at"), default_to_now=False),
            published_at=_parse_datetime(data.get("published_at"), default_to_now=False),
            # Permissions
            is_owner=data.get("is_owner", False),
            can_edit=data.get("can_edit", False),
            can_share=data.get("can_share", False),
            can_delete=data.get("can_delete", False),
            # Sharing
            shared_with_users=data.get("shared_with_users", []),
            shared_with_organizations=data.get("shared_with_organizations", []),
            # Raw data
            blueprint_data=data.get("blueprint_data"),
            blueprint_info=data.get("blueprint_info"),
            # Marketplace
            marketplace_app_id=marketplace_app_id,
        )


def _parse_datetime(value, default_to_now: bool = True) -> datetime | None:
    """Parse datetime from API response.

    Args:
        value: Datetime string or datetime object
        default_to_now: If True, return now() when value is None. If False, return None.

    Returns:
        Parsed datetime or None
    """
    if not value:
        return datetime.now() if default_to_now else None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now() if default_to_now else None


class ValidationReport(BaseModel):
    """Result of validation/doctor check."""

    valid: bool = Field(..., description="Whether validation passed")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")

    def __bool__(self) -> bool:
        """Allow using report in boolean context."""
        return self.valid

    def __str__(self) -> str:
        if self.valid and not self.warnings:
            return "Validation passed"
        lines = []
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"  - {e}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  - {w}")
        return "\n".join(lines)


# =============================================================================
# Marketplace Models
# =============================================================================


class AppTags(BaseModel):
    """Tags for marketplace apps."""

    industry: str | None = Field(None, description="Industry tag (e.g., 'Banking & Financial Services')")
    function: str | None = Field(None, description="Function tag (e.g., 'Marketing', 'Sales')")
    category: str | None = Field(None, description="Category tag (e.g., 'Productivity & Cost Savings')")


class AppConfig(BaseModel):
    """Configuration for publishing an agent to the marketplace.

    Used when publishing an agent as a marketplace app.
    """

    name: str = Field(..., min_length=1, max_length=100, description="App name (must be unique)")
    agent_id: str = Field(..., description="ID of the agent to publish")
    description: str | None = Field(None, description="App description")
    creator: str = Field(default="SDK", description="Creator name")
    public: bool = Field(default=True, description="Whether app is publicly visible")
    organization_id: str | None = Field(None, description="Organization ID for org-only visibility")
    welcome_message: str | None = Field(None, description="Welcome message shown to users")
    tags: AppTags | None = Field(None, description="Industry/function/category tags")


class App(BaseModel):
    """Marketplace app returned from API.

    This is the response model, not used for creation.
    """

    id: str = Field(..., description="App ID")
    name: str
    description: str = ""
    creator: str
    user_id: str = Field(..., description="Owner user ID")
    agent_id: str | None = Field(None, description="Associated agent ID")
    organization_id: str | None = Field(None, description="Organization ID if org-scoped")
    public: bool = Field(default=False, description="Whether publicly visible")
    categories: list[str] = Field(default_factory=list, description="Legacy categories")
    tags: AppTags | None = Field(None, description="Industry/function/category tags")
    upvotes: int = Field(default=0, description="Number of upvotes")
    welcome_message: str | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    @property
    def marketplace_url(self) -> str:
        """URL to view this app in the marketplace."""
        return f"https://studio.lyzr.ai/agent/{self.id}"

    @classmethod
    def from_api_response(cls, data: dict) -> "App":
        """Create App from API response data."""
        # Parse tags if present
        tags = None
        if data.get("tags"):
            tags = AppTags(
                industry=data["tags"].get("industry"),
                function=data["tags"].get("function"),
                category=data["tags"].get("category"),
            )

        # Handle both "id" and "_id" from different API responses
        app_id = data.get("id") or data.get("_id") or ""

        return cls(
            id=app_id,
            name=data.get("name", ""),
            description=data.get("description", ""),
            creator=data.get("creator", ""),
            user_id=data.get("user_id", ""),
            agent_id=data.get("agent_id"),
            organization_id=data.get("organization_id"),
            public=data.get("public", False),
            categories=data.get("categories", []),
            tags=tags,
            upvotes=data.get("upvotes", 0),
            welcome_message=data.get("welcome_message"),
            created_at=_parse_datetime(data.get("created_at"), default_to_now=True),
            updated_at=_parse_datetime(data.get("updated_at"), default_to_now=True),
        )
