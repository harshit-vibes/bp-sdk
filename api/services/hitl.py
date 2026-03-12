"""HITL (Human-In-The-Loop) service for parsing structured output.

This service handles:
1. Parsing agent responses for structured JSON output
2. Extracting HITL suggestions, agent YAMLs, and blueprint specs
3. Formatting user responses (proceed/revise) for the agent
"""

from __future__ import annotations

import json
import re
from typing import Optional

from pydantic import ValidationError

from ..models.hitl import (
    AgentAction,
    AgentYAMLSpec,
    BlueprintSpec,
    BlueprintYAMLSpec,
    HITLResponse,
    HITLResponseAction,
    HITLSuggestion,
    HITLType,
    InfoItem,
    StructuredOutput,
)


class HITLService:
    """Parse and handle structured output from agent responses."""

    # Patterns to find JSON blocks (in order of preference)
    # 1. Standard code block: ```json ... ```
    JSON_BLOCK_PATTERN = re.compile(
        r"```json\s*(.*?)\s*```",
        re.DOTALL,
    )
    # 2. Without backticks: json\n{...} at end of response
    JSON_NO_TICKS_PATTERN = re.compile(
        r"\njson\n(\{.*\})\s*$",
        re.DOTALL,
    )
    # 3. Bare JSON with "action" key at end of response
    BARE_JSON_PATTERN = re.compile(
        r'(\{"action":\s*"(?:hitl|create_blueprint)".*\})\s*$',
        re.DOTALL,
    )

    def parse_response(self, text: str) -> tuple[str, Optional[StructuredOutput]]:
        """Parse agent response for structured output.

        With JSON output mode, the entire response should be valid JSON.
        Falls back to regex patterns for legacy markdown mode.

        Args:
            text: Full agent response text

        Returns:
            Tuple of (clean_text, structured_output)
            - clean_text: Message from the structured output (or original text if no structured data)
            - structured_output: Parsed StructuredOutput if found
        """
        text = text.strip()

        # PRIMARY: Try direct JSON parsing (JSON output mode)
        # The agent should return pure JSON with action, message, hitl, etc.
        try:
            data = json.loads(text)
            # Validate it has the expected structure (action field)
            if isinstance(data, dict) and "action" in data:
                output = StructuredOutput.model_validate(data)
                # For JSON mode, the "message" field IS the clean text
                clean_text = output.message or ""
                return clean_text, output
        except (json.JSONDecodeError, ValidationError):
            # Not valid JSON, try legacy patterns
            pass

        # FALLBACK: Try regex patterns for legacy markdown mode
        patterns = [
            (self.JSON_BLOCK_PATTERN, "code_block"),
            (self.JSON_NO_TICKS_PATTERN, "no_ticks"),
            (self.BARE_JSON_PATTERN, "bare"),
        ]

        for pattern, pattern_type in patterns:
            match = pattern.search(text)
            if match:
                json_str = match.group(1).strip()
                try:
                    data = json.loads(json_str)
                    output = StructuredOutput.model_validate(data)

                    # Remove the JSON block from text
                    clean_text = text[: match.start()].rstrip()

                    return clean_text, output

                except (json.JSONDecodeError, ValidationError):
                    # Try next pattern
                    continue

        return text, None

    def extract_hitl(self, output: StructuredOutput) -> Optional[HITLSuggestion]:
        """Extract HITL suggestion from structured output."""
        if output.action == AgentAction.HITL and output.hitl:
            return output.hitl
        return None

    def extract_agent_from_hitl(self, hitl: HITLSuggestion) -> Optional[AgentYAMLSpec]:
        """Extract agent YAML spec from review_agent HITL preview.

        When user approves a review_agent HITL, the agent spec is embedded
        in the preview and should be saved to session.

        Args:
            hitl: The HITL suggestion containing the agent preview

        Returns:
            AgentYAMLSpec if found and valid, None otherwise
        """
        if hitl.type != HITLType.REVIEW_AGENT:
            return None

        if not hitl.preview:
            return None

        # The preview should contain agent_yaml with full spec
        agent_data = hitl.preview.get("agent_yaml")
        if not agent_data:
            return None

        try:
            return AgentYAMLSpec.model_validate(agent_data)
        except ValidationError:
            return None

    def extract_blueprint_yaml(self, output: StructuredOutput) -> Optional[BlueprintYAMLSpec]:
        """Extract blueprint YAML spec from structured output."""
        if output.action == AgentAction.CREATE_BLUEPRINT and output.blueprint_yaml:
            return output.blueprint_yaml
        return None

    def extract_blueprint(self, output: StructuredOutput) -> Optional[BlueprintSpec]:
        """Extract legacy blueprint spec from structured output."""
        if output.action == AgentAction.CREATE_BLUEPRINT and output.blueprint:
            return output.blueprint
        return None

    def format_response(self, hitl: HITLSuggestion, response: HITLResponse) -> str:
        """Format user HITL response for the agent.

        Converts the structured HITLResponse into a natural language message
        that the agent can understand and act upon.

        Args:
            hitl: The HITL suggestion that was shown
            response: User's structured response (proceed/revise)

        Returns:
            Formatted message to send to the agent
        """
        if response.action == HITLResponseAction.PROCEED:
            # User approved - give specific next step based on HITL type
            next_step = self._get_next_step_instruction(hitl.type)
            parts = [next_step]

            if response.info_answers:
                parts.append("\nHere is the information you requested:")
                for item_id, answer in response.info_answers.items():
                    # Find the original question for context
                    question = self._find_question(hitl.info_items, item_id)
                    if question:
                        parts.append(f"- {question}: {answer}")
                    else:
                        parts.append(f"- {item_id}: {answer}")

            return "\n".join(parts)

        elif response.action == HITLResponseAction.REVISE:
            # User wants a redo with specific feedback
            type_label = hitl.type.value.replace("_", " ")
            parts = [f"Please redo the {type_label}."]

            if response.feedback:
                parts.append(f"\nFocus on this: {response.feedback}")
            else:
                parts.append("\nPlease ask me what changes I'd like.")

            return "\n".join(parts)

        else:
            # Fallback for any other response (shouldn't happen with enum)
            return str(response)

    def _get_next_step_instruction(self, hitl_type: HITLType) -> str:
        """Get specific next step instruction based on HITL type.

        This helps the agent understand exactly what to do after approval,
        preventing it from looping back to exploration mode.
        """
        instructions = {
            HITLType.CONFIRM_ARCHITECTURE: (
                "APPROVED: Architecture is approved.\n\n"
                "CRITICAL INSTRUCTION: You MUST now proceed to the CRAFT phase.\n"
                "- Output a 'review_agent' HITL with the manager agent specification.\n"
                "- After manager is approved, output 'review_agent' HITLs for each worker.\n"
                "- DO NOT ask questions. DO NOT return to exploration mode.\n"
                "- Your next output MUST be a review_agent HITL for the manager agent."
            ),
            HITLType.REVIEW_AGENT: (
                "APPROVED: Agent specification is approved.\n\n"
                "CRITICAL INSTRUCTION: Proceed immediately to the next step.\n"
                "- If there are more agents to define, output the next 'review_agent' HITL.\n"
                "- If ALL agents are defined, output 'create_blueprint' action.\n"
                "- DO NOT ask questions. DO NOT return to exploration mode.\n"
                "- Your next output MUST be either another review_agent HITL or create_blueprint."
            ),
            HITLType.REVIEW_BLUEPRINT: (
                "APPROVED: Blueprint specification is approved.\n\n"
                "CRITICAL INSTRUCTION: Create the blueprint NOW.\n"
                "- Output the 'create_blueprint' action with the full blueprint specification.\n"
                "- DO NOT ask any more questions."
            ),
            HITLType.CONFIRM_CREATE: (
                "CONFIRMED: Create the blueprint NOW.\n"
                "Output the 'create_blueprint' action immediately."
            ),
        }
        return instructions.get(
            hitl_type,
            "APPROVED. Proceed to the next step immediately. Do not ask questions."
        )

    def format_agent_saved_message(self, agent_yaml: AgentYAMLSpec, crafting_progress: str) -> str:
        """Format a message confirming agent YAML was saved.

        Args:
            agent_yaml: The saved agent spec
            crafting_progress: Progress string like "2/4"

        Returns:
            Formatted confirmation message for the agent
        """
        agent_type = "manager" if agent_yaml.is_manager else "worker"
        return (
            f"Saved {agent_type} agent '{agent_yaml.name}' ({agent_yaml.filename}). "
            f"Progress: {crafting_progress} agents crafted. "
            f"Please proceed to the next agent or finalize the blueprint."
        )

    def format_legacy_response(self, hitl: HITLSuggestion, response: str) -> str:
        """Format legacy string response for backward compatibility.

        Handles old-style responses like "approve" or "request_changes".

        Args:
            hitl: The HITL suggestion that was shown
            response: User's response string

        Returns:
            Formatted message to send to the agent
        """
        type_label = hitl.type.value.replace("_", " ")

        if response == "approve" or response == "proceed":
            return self._get_next_step_instruction(hitl.type)
        elif response == "request_changes" or response == "revise":
            return f"I'd like to request changes to the {type_label}. Let me explain what I want different."
        else:
            # User provided custom feedback directly
            return response

    def _find_question(self, info_items: list[InfoItem], item_id: str) -> Optional[str]:
        """Find the question text for a given info item ID."""
        for item in info_items:
            if item.id == item_id:
                return item.question
        return None

    def validate_response(
        self, hitl: HITLSuggestion, response: HITLResponse
    ) -> tuple[bool, Optional[str]]:
        """Validate that the response has all required info.

        Args:
            hitl: The HITL suggestion
            response: User's response

        Returns:
            Tuple of (is_valid, error_message)
        """
        if response.action == HITLResponseAction.PROCEED:
            # Check all required info items are answered
            required_items = [item for item in hitl.info_items if item.required]

            if required_items and not response.info_answers:
                missing = [item.question for item in required_items]
                return False, f"Missing required info: {', '.join(missing)}"

            if response.info_answers:
                missing = []
                for item in required_items:
                    if item.id not in response.info_answers:
                        missing.append(item.question)

                if missing:
                    return False, f"Missing required info: {', '.join(missing)}"

        elif response.action == HITLResponseAction.REVISE:
            # Revise should have feedback (though not strictly required)
            if not response.feedback:
                # This is a soft warning, not an error
                pass

        return True, None

    def blueprint_spec_to_config(self, spec: BlueprintSpec) -> dict:
        """Convert legacy BlueprintSpec to BlueprintConfig-compatible dict.

        Args:
            spec: BlueprintSpec from agent

        Returns:
            Dict compatible with BlueprintClient.create()
        """
        return {
            "name": spec.name,
            "description": spec.description,
            "category": spec.category,
            "tags": spec.tags,
            "manager": {
                "name": spec.manager_name,
                "role": spec.manager_role,
                "goal": spec.manager_goal,
                "instructions": spec.manager_instructions,
                "model": spec.manager_model,
                "temperature": spec.manager_temperature,
            },
            "workers": spec.workers,
        }

    def create_proceed_response(
        self, info_answers: Optional[dict[str, str]] = None
    ) -> HITLResponse:
        """Helper to create a proceed response.

        Args:
            info_answers: Optional answers to info items

        Returns:
            HITLResponse with action=proceed
        """
        return HITLResponse(
            action=HITLResponseAction.PROCEED,
            info_answers=info_answers,
        )

    def create_revise_response(self, feedback: str) -> HITLResponse:
        """Helper to create a revise response.

        Args:
            feedback: Specific feedback for what to focus on in the redo

        Returns:
            HITLResponse with action=revise
        """
        return HITLResponse(
            action=HITLResponseAction.REVISE,
            feedback=feedback,
        )

    def get_action_type(self, output: StructuredOutput) -> str:
        """Get a human-readable action type string.

        Args:
            output: The structured output

        Returns:
            String describing the action type
        """
        if output.action == AgentAction.HITL:
            if output.hitl:
                return f"hitl:{output.hitl.type.value}"
            return "hitl"
        elif output.action == AgentAction.CREATE_BLUEPRINT:
            return "create_blueprint"
        else:
            return output.action.value
