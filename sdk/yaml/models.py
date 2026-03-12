"""YAML Pydantic Models for Blueprint Definitions.

These models represent the YAML file format for defining blueprints and agents.
They are separate from the SDK's internal models to provide a clean YAML schema.

Example blueprint YAML:
```yaml
apiVersion: lyzr.ai/v1
kind: Blueprint

metadata:
  name: "Daily News Agent"
  description: "Curates daily news"
  category: "marketing"
  tags: ["news", "automation"]
  visibility: private

root_agents:
  - "agents/news-coordinator.yaml"

ids:
  blueprint: "11938e83-5b25-41a8-ab89-0481ecfe3669"
  agents:
    "agents/news-coordinator.yaml": "69538cfd6363be71980ec157"
```

Example agent YAML:
```yaml
apiVersion: lyzr.ai/v1
kind: Agent

metadata:
  name: "News Coordinator"
  description: "Orchestrates the news curation pipeline"

spec:
  model: "gpt-4o"
  temperature: 0.3
  role: "News Pipeline Orchestrator"
  goal: "Coordinate agents to deliver accurate daily news updates"
  instructions: |
    You are the News Coordinator managing a news curation pipeline.
    ...

sub_agents:
  - "query-generator.yaml"
  - "research-analyst.yaml"
```
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BlueprintMetadata(BaseModel):
    """Blueprint metadata section."""

    name: str = Field(..., min_length=1, max_length=100, description="Blueprint name")
    description: str = Field(..., min_length=1, description="Blueprint description")
    category: str | None = Field(None, description="Blueprint category")
    tags: list[str] = Field(default_factory=list, description="Blueprint tags")
    visibility: Literal["private", "organization", "public"] = Field(
        default="private",
        description="Blueprint visibility",
    )
    is_template: bool = Field(default=False, description="Whether this is a template")
    shared_with_users: list[str] = Field(
        default_factory=list,
        description="User IDs to share with",
    )
    shared_with_organizations: list[str] = Field(
        default_factory=list,
        description="Organization IDs to share with",
    )
    readme: str | None = Field(None, description="README markdown content")


class BlueprintIDs(BaseModel):
    """Platform-provided IDs (written after creation)."""

    blueprint: str | None = Field(None, description="Blueprint API ID")
    agents: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of agent file path to API ID",
    )


class BlueprintYAML(BaseModel):
    """Blueprint YAML definition.

    This represents the full structure of a blueprint.yaml file.
    """

    apiVersion: str = Field(
        default="lyzr.ai/v1",
        description="API version for schema evolution",
    )
    kind: Literal["Blueprint"] = Field(
        default="Blueprint",
        description="Resource type identifier",
    )
    metadata: BlueprintMetadata = Field(..., description="Blueprint metadata")
    root_agents: list[str] = Field(
        ...,
        min_length=1,
        description="List of root agent file paths (relative to blueprint file)",
    )
    ids: BlueprintIDs | None = Field(
        None,
        description="Platform-provided IDs (auto-populated after creation)",
    )

    model_config = ConfigDict(extra="forbid")


class AgentMetadata(BaseModel):
    """Agent metadata section."""

    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    description: str = Field(..., min_length=1, description="Agent description")


class AgentSpec(BaseModel):
    """Agent specification (LLM config and behavior)."""

    # LLM configuration
    model: str = Field(default="gpt-4o", description="LLM model name")
    temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="Temperature")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Top-p sampling")
    response_format: Literal["text", "json_object"] = Field(
        default="text",
        description="Response format",
    )
    store_messages: bool = Field(
        default=True,
        description="Store conversation history",
    )
    file_output: bool = Field(
        default=False,
        description="Enable file output generation",
    )

    # Persona fields
    role: str | None = Field(
        None,
        min_length=15,
        max_length=80,
        description="Agent role (15-80 chars)",
    )
    goal: str | None = Field(
        None,
        min_length=50,
        max_length=300,
        description="Agent goal (50-300 chars)",
    )
    context: str | None = Field(
        None,
        description="Background context and domain knowledge",
    )
    output: str | None = Field(
        None,
        description="Output format specifications",
    )
    examples: str | None = Field(
        None,
        description="Few-shot examples (multiline string)",
    )

    # Instructions (required)
    instructions: str = Field(..., min_length=1, description="Agent instructions/prompt")

    # Worker-specific
    usage: str | None = Field(
        None,
        description="How parent agent should use this agent (for sub-agents)",
    )

    # Features
    features: list[str] = Field(
        default_factory=list,
        description="List of features to enable",
    )


class AgentYAML(BaseModel):
    """Agent YAML definition.

    This represents the full structure of an agent.yaml file.
    """

    apiVersion: str = Field(
        default="lyzr.ai/v1",
        description="API version for schema evolution",
    )
    kind: Literal["Agent"] = Field(
        default="Agent",
        description="Resource type identifier",
    )
    metadata: AgentMetadata = Field(..., description="Agent metadata")
    spec: AgentSpec = Field(..., description="Agent specification")
    sub_agents: list[str] = Field(
        default_factory=list,
        description="List of sub-agent file paths (relative to this agent file)",
    )

    model_config = ConfigDict(extra="forbid")

    @property
    def is_manager(self) -> bool:
        """Check if this agent has sub-agents (making it a manager)."""
        return len(self.sub_agents) > 0

    @property
    def is_worker(self) -> bool:
        """Check if this agent has no sub-agents (making it a worker)."""
        return len(self.sub_agents) == 0
