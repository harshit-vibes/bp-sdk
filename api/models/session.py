"""Session models for blueprint building workflow."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from .hitl import AgentYAMLSpec, ArchitectureSpec, BlueprintYAMLSpec, HITLSuggestion


class Message(BaseModel):
    """A chat message."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BuilderStep(str, Enum):
    """Current step in the blueprint building process."""

    UNDERSTAND = "understand"  # Step 1: Gathering requirements
    DESIGN = "design"  # Step 2: Architecture design
    CRAFT = "craft"  # Step 3: Iterative agent crafting
    CREATE = "create"  # Step 4: Blueprint creation
    VALIDATE = "validate"  # Step 5: Validation
    DONE = "done"  # Completed


class CraftingState(BaseModel):
    """State for the iterative crafting process in Step 3."""

    # List of agents to craft (from architecture)
    # First one is always the manager, rest are workers
    agents_to_craft: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of agents with 'name' and 'purpose' keys"
    )

    # Current index (0 = manager, 1+ = workers)
    current_index: int = Field(
        default=0,
        description="Which agent we're currently crafting"
    )

    # Saved agent YAMLs
    manager_yaml: Optional[AgentYAMLSpec] = Field(
        default=None,
        description="Saved manager agent YAML"
    )

    worker_yamls: list[AgentYAMLSpec] = Field(
        default_factory=list,
        description="Saved worker agent YAMLs"
    )

    @property
    def total_agents(self) -> int:
        """Total number of agents to craft."""
        return len(self.agents_to_craft)

    @property
    def current_agent(self) -> Optional[dict[str, str]]:
        """Get the current agent being crafted."""
        if 0 <= self.current_index < len(self.agents_to_craft):
            return self.agents_to_craft[self.current_index]
        return None

    @property
    def is_crafting_manager(self) -> bool:
        """Check if we're crafting the manager (first agent)."""
        return self.current_index == 0

    @property
    def is_complete(self) -> bool:
        """Check if all agents have been crafted."""
        return self.current_index >= len(self.agents_to_craft)

    @property
    def all_agents_saved(self) -> bool:
        """Check if all agent YAMLs have been saved."""
        if not self.manager_yaml:
            return False
        expected_workers = len(self.agents_to_craft) - 1  # Minus manager
        return len(self.worker_yamls) >= expected_workers

    def get_all_yamls(self) -> list[AgentYAMLSpec]:
        """Get all saved YAMLs in order (manager first, then workers)."""
        result = []
        if self.manager_yaml:
            result.append(self.manager_yaml)
        result.extend(self.worker_yamls)
        return result


class Session(BaseModel):
    """Chat session state for blueprint building."""

    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    messages: list[Message] = Field(default_factory=list)

    # Current step in the flow
    current_step: BuilderStep = Field(
        default=BuilderStep.UNDERSTAND,
        description="Current step in the 5-step blueprint building process"
    )

    # Step 1: Requirements gathered from UNDERSTAND
    requirements_summary: Optional[str] = Field(
        default=None,
        description="Summary of user requirements from Step 1"
    )

    # Step 2: Architecture from DESIGN
    architecture: Optional[ArchitectureSpec] = Field(
        default=None,
        description="Approved architecture from Step 2"
    )

    # Step 3: Crafting state
    crafting: CraftingState = Field(
        default_factory=CraftingState,
        description="State for iterative agent crafting in Step 3"
    )

    # Step 4: Blueprint metadata
    blueprint_yaml: Optional[BlueprintYAMLSpec] = Field(
        default=None,
        description="Blueprint YAML specification for creation"
    )

    # Created blueprint (after Step 4)
    blueprint_id: Optional[str] = Field(
        default=None,
        description="Created blueprint ID"
    )
    studio_url: Optional[str] = Field(
        default=None,
        description="Studio URL for the created blueprint"
    )

    # HITL state
    pending_hitl: Optional[HITLSuggestion] = Field(
        default=None,
        description="Pending HITL suggestion waiting for user response"
    )

    # Legacy: Direct blueprint draft (for backwards compatibility)
    blueprint_draft: Optional[dict] = None

    def save_agent_yaml(self, agent_yaml: AgentYAMLSpec) -> None:
        """Save an agent YAML to the session.

        Automatically determines if it's the manager or a worker.
        """
        if agent_yaml.is_manager:
            self.crafting.manager_yaml = agent_yaml
        else:
            # Check if we already have this worker (by filename)
            existing_idx = None
            for i, w in enumerate(self.crafting.worker_yamls):
                if w.filename == agent_yaml.filename:
                    existing_idx = i
                    break

            if existing_idx is not None:
                # Replace existing
                self.crafting.worker_yamls[existing_idx] = agent_yaml
            else:
                # Add new
                self.crafting.worker_yamls.append(agent_yaml)

    def advance_crafting(self) -> None:
        """Move to the next agent in the crafting sequence."""
        self.crafting.current_index += 1

    def setup_crafting_from_architecture(self, architecture: ArchitectureSpec) -> None:
        """Initialize crafting state from approved architecture."""
        self.architecture = architecture

        # Build the list of agents to craft (manager first, then workers)
        agents_to_craft = [
            {
                "name": architecture.manager.get("name", "Manager"),
                "purpose": architecture.manager.get("purpose", ""),
            }
        ]
        for worker in architecture.workers:
            agents_to_craft.append({
                "name": worker.get("name", "Worker"),
                "purpose": worker.get("purpose", "")
            })

        self.crafting = CraftingState(agents_to_craft=agents_to_craft)
        self.current_step = BuilderStep.CRAFT


class SessionResponse(BaseModel):
    """Response for session creation."""

    session_id: str
    created_at: datetime
    message: str


class SessionStatus(BaseModel):
    """Detailed session status for debugging/monitoring."""

    session_id: str
    current_step: BuilderStep
    crafting_progress: str  # e.g., "2/4 agents crafted"
    has_architecture: bool
    has_blueprint: bool
    pending_hitl_type: Optional[str]
