"""Stage-based builder routes for app-orchestrated workflow.

This module provides direct routes to specialized agents:
- POST /architect - Design architecture from requirements
- POST /craft - Create agent specification
- POST /create - Create blueprint from session data
"""

from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..config import get_settings
from ..models.hitl import AgentYAMLSpec
from ..services.blueprint import BlueprintService
from ..services.inference import InferenceService

router = APIRouter()


# Request/Response Models

class ArchitectRequest(BaseModel):
    """Request to design architecture."""

    session_id: Optional[str] = None
    requirements: str = Field(..., description="User requirements from GuidedChat")


class ArchitectResponse(BaseModel):
    """Architecture design response."""

    session_id: str
    pattern: str  # Inferred: "single_agent" | "manager_workers"
    reasoning: str
    manager: dict[str, str]  # {name, purpose}
    workers: list[dict[str, str]] = []  # [{name, purpose}]

    @classmethod
    def from_agent_response(cls, session_id: str, result: dict) -> "ArchitectResponse":
        """Create response from pattern-agnostic agent output.

        The architect agent returns:
        - main_agent: {name, purpose}
        - specialists: [{name, purpose}]

        We infer the pattern and map to our schema.
        """
        # Handle both old and new schema for backward compatibility
        if "main_agent" in result:
            # New pattern-agnostic schema
            main_agent = result.get("main_agent", {})
            specialists = result.get("specialists", [])
            pattern = "single_agent" if len(specialists) == 0 else "manager_workers"

            return cls(
                session_id=session_id,
                pattern=pattern,
                reasoning=result.get("reasoning", ""),
                manager=main_agent,
                workers=specialists,
            )
        else:
            # Old schema with explicit pattern
            return cls(
                session_id=session_id,
                pattern=result.get("pattern", "manager_workers"),
                reasoning=result.get("reasoning", ""),
                manager=result.get("manager", {}),
                workers=result.get("workers", []),
            )


class CraftRequest(BaseModel):
    """Request to craft an agent specification."""

    session_id: str
    agent_name: str
    agent_purpose: str
    is_manager: bool = False
    agent_index: int = 0
    context: str = Field(..., description="Architecture context for the agent")
    worker_names: list[str] = Field(default_factory=list, description="Worker names for manager's sub_agents")


class CraftResponse(BaseModel):
    """Agent specification response."""

    session_id: str
    agent_yaml: dict[str, Any]


class CreateRequest(BaseModel):
    """Request to create blueprint."""

    session_id: str


class CreateResponse(BaseModel):
    """Blueprint creation response."""

    session_id: str
    blueprint_id: str
    blueprint_name: str
    studio_url: str
    manager_id: str
    worker_ids: list[str]
    organization_id: str
    created_at: str
    share_type: str = "private"


# Helper Functions

async def call_agent_and_parse_json(
    agent_id: str,
    message: str,
    session_id: str,
    settings: Any,
) -> dict:
    """Call an agent and parse JSON response."""
    if not agent_id:
        raise HTTPException(
            status_code=500,
            detail="Agent ID not configured. Deploy agents first.",
        )

    inference_service = InferenceService(
        agent_id=agent_id,
        api_key=settings.lyzr_api_key,
        base_url=settings.agent_api_url,
    )

    # Collect full response
    full_response = ""
    async for chunk in inference_service.stream(
        session_id=session_id,
        message=message,
    ):
        full_response += chunk

    # Parse JSON response
    response_text = full_response.strip()

    # SSE streaming double-escapes the JSON content
    # First, try treating it as a JSON-encoded string and decode it
    if response_text.startswith('\\"') or '\\n' in response_text or '\\"' in response_text:
        # The response is double-escaped, decode using unicode_escape
        try:
            # This handles \n, \t, \" etc. properly
            response_text = response_text.encode('utf-8').decode('unicode_escape')
        except UnicodeDecodeError:
            # Fallback to manual replacement if unicode_escape fails
            response_text = (
                response_text
                .replace('\\"', '"')
                .replace("\\n", "\n")
                .replace("\\t", "\t")
            )

    # Remove markdown code blocks if present
    if "```json" in response_text:
        # Extract content between ```json and ```
        start = response_text.find("```json") + 7
        end = response_text.find("```", start)
        if end > start:
            response_text = response_text[start:end].strip()
    elif "```" in response_text:
        # Extract content between ``` and ```
        start = response_text.find("```") + 3
        end = response_text.find("```", start)
        if end > start:
            response_text = response_text[start:end].strip()

    try:
        # Try to parse directly, allowing control characters in strings
        return json.loads(response_text, strict=False)
    except json.JSONDecodeError as e:
        # Try to extract JSON from response
        # Sometimes the model may include extra text before/after JSON

        # First, check if it looks like an array
        array_start = response_text.find("[")
        array_end = response_text.rfind("]") + 1
        if array_start != -1 and array_end > array_start:
            json_text = response_text[array_start:array_end]
            try:
                return json.loads(json_text, strict=False)
            except json.JSONDecodeError:
                pass  # Try other methods below

        # Check for object
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start != -1 and end > start:
            json_text = response_text[start:end]
            try:
                return json.loads(json_text, strict=False)
            except json.JSONDecodeError:
                # The model might have returned comma-separated objects without array brackets
                # Try wrapping in array brackets
                try:
                    wrapped = "[" + json_text + "]"
                    return json.loads(wrapped, strict=False)
                except json.JSONDecodeError as e2:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Agent did not return valid JSON. Error: {e2}. Response: {json_text[:300]}",
                    )
        raise HTTPException(
            status_code=500,
            detail=f"Agent did not return valid JSON: {response_text[:200]}",
        )


# Routes

@router.post("/architect", response_model=ArchitectResponse)
async def design_architecture(
    request: ArchitectRequest,
    http_request: Request,
) -> ArchitectResponse:
    """Design blueprint architecture from requirements.

    Calls the Architect Agent with user requirements and returns
    a structured architecture proposal.
    """
    settings = get_settings()
    session_service = http_request.app.state.session_service

    # Get or create session
    session = session_service.get(request.session_id)
    if not session:
        session = session_service.create(request.session_id)

    # Build prompt for architect agent
    prompt = f"""Design a blueprint architecture for the following requirements:

{request.requirements}

Return ONLY valid JSON with the architecture proposal."""

    # Call architect agent
    result = await call_agent_and_parse_json(
        agent_id=settings.architect_agent_id,
        message=prompt,
        session_id=session.session_id,
        settings=settings,
    )

    # Store in session
    session.requirements_summary = request.requirements
    session_service.update(session)

    # Use factory method to handle both old and new schema
    return ArchitectResponse.from_agent_response(session.session_id, result)


@router.post("/craft", response_model=CraftResponse)
async def craft_agent(
    request: CraftRequest,
    http_request: Request,
) -> CraftResponse:
    """Craft an agent specification.

    Calls the Crafter Agent to create a detailed agent specification
    for one agent at a time (manager or worker).
    """
    settings = get_settings()
    session_service = http_request.app.state.session_service

    # Get session
    session = session_service.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build prompt for crafter agent
    agent_type = "manager" if request.is_manager else "worker"
    worker_list = ""
    if request.is_manager and request.worker_names:
        worker_filenames = [f"{name.lower().replace(' ', '-')}.yaml" for name in request.worker_names]
        worker_list = f"\n\nThis manager has the following workers: {', '.join(request.worker_names)}"
        worker_list += f"\nWorker filenames for sub_agents: {worker_filenames}"

    prompt = f"""Create a detailed specification for a {agent_type} agent.

Agent Name: {request.agent_name}
Agent Purpose: {request.agent_purpose}
Agent Index: {request.agent_index}
Is Manager: {request.is_manager}

Context about the blueprint:
{request.context}{worker_list}

Return ONLY valid JSON with the agent_yaml specification."""

    # Call crafter agent
    result = await call_agent_and_parse_json(
        agent_id=settings.crafter_agent_id,
        message=prompt,
        session_id=session.session_id,
        settings=settings,
    )

    # Extract agent_yaml from result
    agent_yaml = result.get("agent_yaml", result)

    # Store in session
    try:
        spec = AgentYAMLSpec.model_validate(agent_yaml)
        session.save_agent_yaml(spec)
        session_service.update(session)
    except Exception:
        pass  # Non-critical, continue

    return CraftResponse(
        session_id=session.session_id,
        agent_yaml=agent_yaml,
    )


@router.post("/create", response_model=CreateResponse)
async def create_blueprint(
    request: CreateRequest,
    http_request: Request,
) -> CreateResponse:
    """Create blueprint from session data.

    Uses the collected architecture and agent specifications from
    the session to create a blueprint via the SDK.
    """
    settings = get_settings()
    session_service = http_request.app.state.session_service

    # Get session
    session = session_service.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all agent YAMLs
    all_yamls = session.crafting.get_all_yamls()
    if not all_yamls:
        raise HTTPException(
            status_code=400,
            detail="No agent specifications found. Complete the craft stage first.",
        )

    manager_yaml = session.crafting.manager_yaml
    if not manager_yaml:
        raise HTTPException(
            status_code=400,
            detail="Manager specification not found.",
        )

    # Build blueprint config
    from sdk import BlueprintConfig, AgentConfig

    # Create manager config
    manager = AgentConfig(
        name=manager_yaml.name,
        description=manager_yaml.description,
        role=manager_yaml.role,
        goal=manager_yaml.goal,
        instructions=manager_yaml.instructions,
        model=manager_yaml.model,
        temperature=manager_yaml.temperature,
    )

    # Create worker configs
    workers = []
    for worker_yaml in session.crafting.worker_yamls:
        workers.append(AgentConfig(
            name=worker_yaml.name,
            description=worker_yaml.description,
            role=worker_yaml.role,
            goal=worker_yaml.goal,
            instructions=worker_yaml.instructions,
            model=worker_yaml.model,
            temperature=worker_yaml.temperature,
            usage_description=worker_yaml.usage_description,
        ))

    # Create blueprint config
    bp_config = BlueprintConfig(
        name=manager_yaml.name.replace("Coordinator", "Blueprint").replace("Manager", "Blueprint"),
        description=manager_yaml.description,
        category="general",
        tags=[],
        manager=manager,
        workers=workers,
    )

    # Create blueprint
    blueprint_service = BlueprintService(
        api_key=settings.lyzr_api_key,
        bearer_token=settings.blueprint_bearer_token,
        org_id=settings.lyzr_org_id,
    )

    try:
        blueprint = blueprint_service.create_from_config(bp_config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create blueprint: {str(e)}",
        )

    # Update session
    session.blueprint_id = blueprint.id
    session.studio_url = blueprint.studio_url
    session_service.update(session)

    from datetime import datetime

    return CreateResponse(
        session_id=session.session_id,
        blueprint_id=blueprint.id,
        blueprint_name=blueprint.name,
        studio_url=blueprint.studio_url or "",
        manager_id=blueprint.manager_id or "",
        worker_ids=blueprint.worker_ids or [],
        organization_id=settings.lyzr_org_id,
        created_at=datetime.utcnow().isoformat(),
        share_type="private",
    )


class LoaderTextRequest(BaseModel):
    """Request for loader text generation."""

    session_id: str
    stage: str = Field(..., description="Current stage: designing, crafting, creating")
    context: Optional[str] = None


class SuggestRequest(BaseModel):
    """Request for revision suggestions."""

    session_id: str
    type: str = Field(..., description="Type: architecture or agent")
    agent_name: Optional[str] = None
    role: Optional[str] = None
    goal: Optional[str] = None
    instructions: Optional[str] = None


class SuggestResponse(BaseModel):
    """Revision suggestions response."""

    suggestions: list[str]


# Fallback loading messages by stage
FALLBACK_LOADER_MESSAGES = {
    "designing": [
        "Consulting the architecture council...",
        "Sketching the blueprint foundation...",
        "Debating agent responsibilities...",
        "Mapping the delegation hierarchy...",
        "Calculating optimal worker count...",
        "Architecting your AI team...",
    ],
    "crafting": [
        "Forging agent personality matrices...",
        "Calibrating instruction parameters...",
        "Infusing domain expertise...",
        "Polishing the goal alignment...",
        "Weaving the prompt tapestry...",
        "Fine-tuning the agent's voice...",
    ],
    "creating": [
        "Materializing your blueprint...",
        "Registering agents in the system...",
        "Establishing the hierarchy links...",
        "Applying final configurations...",
        "Summoning your AI team...",
        "Almost there, one moment...",
    ],
    "options": [
        "Scanning the multiverse of choices...",
        "Consulting the options oracle...",
        "Curating the perfect selection...",
        "Handpicking the best options...",
        "Reading between the lines...",
        "Finding your perfect match...",
    ],
}

# Fallback revision suggestions (8 options each)
FALLBACK_SUGGESTIONS = {
    "architecture": [
        "Add more worker agents",
        "Simplify the structure",
        "Add specialized roles",
        "Improve task delegation",
        "Add error handling",
        "Enhance coordination",
        "Split responsibilities",
        "Change the pattern",
    ],
    "agent": [
        "Add detailed steps",
        "Clarify the goal",
        "Improve instructions",
        "Add edge cases",
        "Enhance output format",
        "Add constraints",
        "Simplify the role",
        "Change the tone",
    ],
}


class LoaderTextResponse(BaseModel):
    """Single loading text response."""

    text: str


@router.get("/loader-text", response_model=LoaderTextResponse)
async def get_loader_text(
    session_id: str = "default",
    stage: str = "designing",
    context: Optional[str] = None,
    http_request: Request = None,
) -> LoaderTextResponse:
    """Get a witty loading text message.

    Returns a single entertaining, contextual loading message.
    The frontend calls this repeatedly while loading.
    """
    import random

    settings = get_settings()

    # If loader agent is configured, try to use it
    if settings.loader_agent_id:
        try:
            inference_service = InferenceService(
                agent_id=settings.loader_agent_id,
                api_key=settings.lyzr_api_key,
                base_url=settings.agent_api_url,
            )

            prompt = f"""Generate ONE witty, fun loading message for a user who is waiting.
Stage: {stage}
Context: {context or 'Building an AI blueprint'}

Rules:
- Keep it under 50 characters
- Be clever and entertaining
- Match the stage mood
- No markdown, just text
- No quotes around the text"""

            full_response = ""
            async for chunk in inference_service.stream(
                session_id=session_id,
                message=prompt,
            ):
                full_response += chunk

            # Clean up the response
            message = full_response.strip().strip('"').strip("'")
            # Remove common artifacts
            message = message.replace("\\n", " ").replace("\\", "").strip()
            # Skip if contains error markers or is too short/long
            if (
                message
                and "[Request" not in message
                and "[Error" not in message
                and len(message) > 5
                and len(message) < 100
            ):
                return LoaderTextResponse(text=message)

        except Exception:
            # Fall back to local messages
            pass

    # Return a random fallback message
    messages = FALLBACK_LOADER_MESSAGES.get(stage, FALLBACK_LOADER_MESSAGES["designing"])
    return LoaderTextResponse(text=random.choice(messages))


@router.post("/suggest", response_model=SuggestResponse)
async def get_revision_suggestions(
    request: SuggestRequest,
    http_request: Request,
) -> SuggestResponse:
    """Get contextual revision suggestions.

    Returns 8 suggestion labels that the user can click
    to provide feedback on architecture or agent specs.
    """
    settings = get_settings()

    # If suggest agent is configured, use it
    if settings.suggest_agent_id:
        try:
            agent_context = ""
            if request.agent_name:
                agent_context = f"""
Agent Name: {request.agent_name}
Role: {request.role or 'Not specified'}
Goal: {request.goal or 'Not specified'}
Instructions Preview: {(request.instructions or '')[:200]}"""

            prompt = f"""Generate exactly 8 revision suggestion labels for a user reviewing a {request.type}.

{agent_context}

Rules:
- Each suggestion should be 2-5 words
- Be specific and actionable
- Cover different aspects (clarity, detail, structure, edge cases, output format, etc.)
- All 8 suggestions must be distinct and useful
- Do NOT include "Other..." - provide 8 real suggestions
- Return as JSON array: ["suggestion1", "suggestion2", ...]"""

            result = await call_agent_and_parse_json(
                agent_id=settings.suggest_agent_id,
                message=prompt,
                session_id=request.session_id,
                settings=settings,
            )

            suggestions = result if isinstance(result, list) else result.get("suggestions", [])
            if len(suggestions) == 8:
                return SuggestResponse(suggestions=suggestions)

        except Exception:
            # Fall back to local suggestions
            pass

    # Return fallback suggestions
    suggestions = FALLBACK_SUGGESTIONS.get(request.type, FALLBACK_SUGGESTIONS["agent"])
    return SuggestResponse(suggestions=suggestions)


# Fallback options for statement slots (8 options each)
FALLBACK_OPTIONS = {
    "role": [
        {"value": "product manager", "label": "Product Manager", "description": "Building and shipping products"},
        {"value": "customer success lead", "label": "Customer Success", "description": "Ensuring customer satisfaction"},
        {"value": "sales leader", "label": "Sales Leader", "description": "Growing revenue and closing deals"},
        {"value": "marketing director", "label": "Marketing Director", "description": "Driving awareness and demand"},
        {"value": "operations manager", "label": "Operations Manager", "description": "Streamlining processes"},
        {"value": "engineering lead", "label": "Engineering Lead", "description": "Building technical solutions"},
        {"value": "HR manager", "label": "HR Manager", "description": "Managing people and culture"},
        {"value": "founder", "label": "Founder / Executive", "description": "Leading the organization"},
    ],
    "problem": [
        {"value": "automate repetitive tasks that consume my team's time", "label": "Automate Repetitive Work", "description": "Free up time from manual tasks"},
        {"value": "respond to customer inquiries faster and more consistently", "label": "Faster Customer Response", "description": "Improve response time and quality"},
        {"value": "qualify and prioritize incoming leads efficiently", "label": "Lead Qualification", "description": "Focus on high-value prospects"},
        {"value": "generate and optimize content at scale", "label": "Content at Scale", "description": "Create more content, faster"},
        {"value": "extract insights from documents and data", "label": "Extract Insights", "description": "Make sense of information"},
        {"value": "onboard and train team members effectively", "label": "Team Onboarding", "description": "Get people up to speed"},
        {"value": "research and synthesize information quickly", "label": "Research & Synthesis", "description": "Gather and summarize knowledge"},
        {"value": "coordinate work across multiple processes", "label": "Process Coordination", "description": "Orchestrate complex workflows"},
    ],
    "domain": [
        {"value": "customer support", "label": "Customer Support", "description": "Tickets, inquiries, help desk"},
        {"value": "sales", "label": "Sales", "description": "Leads, deals, pipeline"},
        {"value": "marketing", "label": "Marketing", "description": "Campaigns, content, demand gen"},
        {"value": "human resources", "label": "Human Resources", "description": "Recruiting, policies, L&D"},
        {"value": "product development", "label": "Product", "description": "Features, roadmap, feedback"},
        {"value": "operations", "label": "Operations", "description": "Processes, efficiency, logistics"},
        {"value": "finance", "label": "Finance", "description": "Accounting, reporting, analysis"},
        {"value": "legal and compliance", "label": "Legal & Compliance", "description": "Contracts, policies, risk"},
    ],
}


class OptionsRequest(BaseModel):
    """Request for dynamic statement options."""

    slot_type: str = Field(..., description="Slot type: role, problem, or domain")
    context: Optional[dict] = None


class OptionsResponse(BaseModel):
    """Statement options response."""

    options: list[dict]


@router.post("/options", response_model=OptionsResponse)
async def get_statement_options(
    request: OptionsRequest,
    http_request: Request,
) -> OptionsResponse:
    """Get dynamic options for statement slots.

    Uses an AI agent to generate contextual options based on
    the slot type and any prior selections.
    """
    settings = get_settings()

    # Validate slot type
    if request.slot_type not in ["role", "problem", "domain"]:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Invalid slot_type. Must be: role, problem, or domain"
        )

    # If options agent is configured, use it
    if settings.options_agent_id:
        try:
            # Build rich context from previous selections
            context_parts = []
            has_context = False

            if request.context:
                if request.context.get("role"):
                    context_parts.append(f"ROLE SELECTED: \"{request.context['role']}\"")
                    has_context = True
                if request.context.get("problem"):
                    context_parts.append(f"PROBLEM SELECTED: \"{request.context['problem']}\"")
                    has_context = True
                if request.context.get("domain"):
                    context_parts.append(f"DOMAIN SELECTED: \"{request.context['domain']}\"")
                    has_context = True

            # Build contextual prompt based on slot type and previous selections
            if request.slot_type == "role":
                slot_guidance = "Generate 8 business roles that might need AI automation (e.g., Product Manager, Sales Leader, HR Manager)."
            elif request.slot_type == "problem":
                if has_context:
                    slot_guidance = f"Generate 8 problems that a {request.context.get('role', 'professional')} would want AI to solve. Make them SPECIFIC to this role."
                else:
                    slot_guidance = "Generate 8 business problems that AI can help solve (e.g., automate tasks, qualify leads, generate content)."
            else:  # domain
                if has_context:
                    role = request.context.get('role', '')
                    problem = request.context.get('problem', '')
                    slot_guidance = f"""Generate 8 business DOMAINS (departments/functional areas) where a {role} would apply AI to help with "{problem}".

DOMAINS are business areas like: Customer Support, Sales Operations, Marketing, Human Resources, Finance, Legal, Product Management, Engineering, etc.
DO NOT generate problems or solutions - generate ONLY business department names where this use case applies."""
                else:
                    slot_guidance = "Generate 8 business DOMAINS (departments/functional areas) like: Customer Support, Sales, Marketing, Human Resources, Finance, Legal, Product, Operations."

            context_section = ""
            if context_parts:
                context_section = f"""
## PREVIOUS SELECTIONS (use these to generate RELEVANT options)
{chr(10).join(context_parts)}

IMPORTANT: Generate options that are DIRECTLY RELEVANT to the previous selections above.
"""

            prompt = f"""Generate exactly 8 options for the "{request.slot_type}" field.

{slot_guidance}
{context_section}
Return a JSON array with objects having: value, label, description
- value: the actual value (lowercase, specific phrase)
- label: display text (Title Case, 2-4 words)
- description: brief helpful context (4-8 words)

Example:
[{{"value": "automate customer inquiries", "label": "Automate Inquiries", "description": "Handle routine questions automatically"}}]

Rules:
- Generate exactly 8 options
- Each option must be distinct and specific
- If context provided, make ALL options relevant to it
- Return ONLY the JSON array"""

            result = await call_agent_and_parse_json(
                agent_id=settings.options_agent_id,
                message=prompt,
                session_id=request.context.get("session_id", "options") if request.context else "options",
                settings=settings,
            )

            # Handle both direct array and wrapped response
            options = result if isinstance(result, list) else result.get("options", [])
            if len(options) >= 4:  # Accept if we got at least 4 good options
                return OptionsResponse(options=options[:8])

        except Exception as e:
            # Log the error for debugging
            import logging
            logging.warning(f"Options agent failed: {e}")
            # Fall through to fallback

    # Return fallback options
    options = FALLBACK_OPTIONS.get(request.slot_type, FALLBACK_OPTIONS["role"])
    return OptionsResponse(options=options)


class ChatRequest(BaseModel):
    """Request to chat with manager agent."""

    manager_id: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response from manager agent."""

    response: str
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_manager(
    request: ChatRequest,
    http_request: Request,
) -> ChatResponse:
    """Chat with the manager agent of a blueprint.

    Sends a message to the manager agent and returns the response.
    """
    settings = get_settings()

    # Generate session ID if not provided
    import uuid
    session_id = request.session_id or str(uuid.uuid4())

    inference_service = InferenceService(
        agent_id=request.manager_id,
        api_key=settings.lyzr_api_key,
        base_url=settings.agent_api_url,
    )

    # Collect full response
    full_response = ""
    async for chunk in inference_service.stream(
        session_id=session_id,
        message=request.message,
    ):
        full_response += chunk

    return ChatResponse(
        response=full_response,
        session_id=session_id,
    )


class ChatSuggestionsRequest(BaseModel):
    """Request for chat reply suggestions."""

    manager_id: str
    conversation: list[dict] = Field(..., description="Conversation history [{role, content}]")
    session_id: Optional[str] = None


class ChatSuggestionsResponse(BaseModel):
    """Chat reply suggestions response."""

    suggestions: list[str]


# Fallback reply suggestions
FALLBACK_REPLY_SUGGESTIONS = [
    "Tell me more about this",
    "Can you show an example?",
    "What else can you help with?",
]


@router.post("/chat-suggestions", response_model=ChatSuggestionsResponse)
async def get_chat_suggestions(
    request: ChatSuggestionsRequest,
    http_request: Request,
) -> ChatSuggestionsResponse:
    """Get suggested replies for the chat conversation.

    Analyzes the conversation history and returns 3 contextual reply suggestions.
    """
    settings = get_settings()

    # If reply suggester agent is configured, use it
    if settings.reply_suggester_agent_id:
        try:
            # Format conversation for the agent
            conversation_text = "\n".join([
                f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
                for msg in request.conversation[-5:]  # Last 5 messages
            ])

            prompt = f"""Analyze this conversation and generate 3 reply suggestions:

{conversation_text}

Return ONLY valid JSON: {{"suggestions": ["suggestion1", "suggestion2", "suggestion3"]}}"""

            result = await call_agent_and_parse_json(
                agent_id=settings.reply_suggester_agent_id,
                message=prompt,
                session_id=request.session_id or "suggestions",
                settings=settings,
            )

            suggestions = result.get("suggestions", [])
            if len(suggestions) >= 3:
                return ChatSuggestionsResponse(suggestions=suggestions[:3])

        except Exception:
            # Fall through to fallback
            pass

    # Return fallback suggestions
    return ChatSuggestionsResponse(suggestions=FALLBACK_REPLY_SUGGESTIONS)


class CreateSuggestionsRequest(BaseModel):
    """Request for 'Create Another' blueprint suggestions."""

    session_id: Optional[str] = None
    blueprint_name: str = Field(..., description="Name of the just-created blueprint")
    blueprint_description: Optional[str] = None
    agent_types: Optional[list[str]] = Field(default=None, description="Types of agents in the blueprint")


class CreateSuggestionsResponse(BaseModel):
    """Create another suggestions response."""

    suggestions: list[dict]  # [{label, value, description}]


# Fallback suggestions for "Create Another"
FALLBACK_CREATE_SUGGESTIONS = [
    {"label": "Start Fresh", "value": "fresh", "description": "New blueprint from scratch"},
    {"label": "Similar Pattern", "value": "similar", "description": "Same structure, new purpose"},
    {"label": "Different Domain", "value": "different_domain", "description": "New business area"},
    {"label": "More Workers", "value": "more_workers", "description": "Larger team structure"},
    {"label": "Simpler Design", "value": "simpler", "description": "Single agent approach"},
    {"label": "Automation Focus", "value": "automation", "description": "Task automation blueprint"},
    {"label": "Customer Facing", "value": "customer", "description": "Support or sales agents"},
    {"label": "Internal Tools", "value": "internal", "description": "Back-office automation"},
]


@router.post("/create-suggestions", response_model=CreateSuggestionsResponse)
async def get_create_suggestions(
    request: CreateSuggestionsRequest,
    http_request: Request,
) -> CreateSuggestionsResponse:
    """Get contextual suggestions for what blueprint to create next.

    Analyzes the just-created blueprint and returns 8 relevant ideas
    for what the user might want to build next.
    """
    settings = get_settings()

    # If idea suggester agent is configured, use it
    if settings.idea_suggester_agent_id:
        try:
            agent_types_text = ""
            if request.agent_types:
                agent_types_text = f"\nAgent Types: {', '.join(request.agent_types)}"

            prompt = f"""The user just created a blueprint. Suggest 8 ideas for what they might build next.

Blueprint Name: {request.blueprint_name}
Description: {request.blueprint_description or 'Not provided'}{agent_types_text}

Return ONLY valid JSON with 8 suggestions:
{{"suggestions": [{{"label": "Short Label", "value": "unique_key", "description": "Brief description"}}]}}"""

            result = await call_agent_and_parse_json(
                agent_id=settings.idea_suggester_agent_id,
                message=prompt,
                session_id=request.session_id or "create-suggestions",
                settings=settings,
            )

            suggestions = result.get("suggestions", [])
            if len(suggestions) >= 6:  # Accept if we got at least 6 good options
                return CreateSuggestionsResponse(suggestions=suggestions[:8])

        except Exception:
            # Fall through to fallback
            pass

    # Return fallback suggestions
    return CreateSuggestionsResponse(suggestions=FALLBACK_CREATE_SUGGESTIONS)
