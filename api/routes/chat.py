"""Chat streaming endpoint with HITL support."""

from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from ..config import get_settings
from ..models.chat import ChatRequest, ChatEvent
from ..models.hitl import AgentAction
from ..services.blueprint import BlueprintService
from ..services.hitl import HITLService
from ..services.inference import InferenceService

router = APIRouter()


@router.post("/stream")
async def stream_chat(chat_request: ChatRequest, request: Request) -> EventSourceResponse:
    """Stream chat responses with structured output handling.

    Flow:
    1. Stream text chunks to frontend in real-time
    2. After stream completes, parse full response for structured JSON
    3. If HITL needed: emit hitl event, store in session
    4. If blueprint creation: create via API, emit created event
    """
    settings = get_settings()
    session_service = request.app.state.session_service

    # Get or create session
    session = session_service.get(chat_request.session_id)
    if not session:
        session = session_service.create(chat_request.session_id)

    # Initialize services
    inference_service = InferenceService(
        agent_id=settings.builder_agent_id,
        api_key=settings.lyzr_api_key,
        base_url=settings.agent_api_url,
    )
    hitl_service = HITLService()
    blueprint_service = BlueprintService(
        api_key=settings.lyzr_api_key,
        bearer_token=settings.blueprint_bearer_token,
        org_id=settings.lyzr_org_id,
    )

    # Determine the message to send
    if chat_request.hitl_response and session.pending_hitl:
        # User responded to HITL prompt
        message = hitl_service.format_response(
            session.pending_hitl,
            chat_request.hitl_response,
        )
        session_service.clear_pending_hitl(session.session_id)
    else:
        message = chat_request.message

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    # Add user message to session history
    session_service.add_message(session.session_id, "user", message)

    async def event_generator() -> AsyncGenerator[dict, None]:
        """Generate SSE events from agent response."""
        full_response = ""

        try:
            # Phase 1: Stream text chunks
            async for chunk in inference_service.stream(
                session_id=session.session_id,
                message=message,
            ):
                full_response += chunk

                # Emit text chunk immediately
                yield {
                    "event": "text",
                    "data": json.dumps(ChatEvent(
                        type="text",
                        content=chunk,
                    ).model_dump()),
                }

            # Phase 2: Parse for structured output after stream completes
            clean_text, structured_output = hitl_service.parse_response(full_response)

            if structured_output:
                if structured_output.action == AgentAction.HITL:
                    hitl = hitl_service.extract_hitl(structured_output)
                    if hitl:
                        # Store pending HITL in session
                        session_service.set_pending_hitl(session.session_id, hitl)
                        # Emit HITL event
                        yield {
                            "event": "hitl",
                            "data": json.dumps(ChatEvent(
                                type="hitl",
                                hitl=hitl,
                            ).model_dump()),
                        }

                elif structured_output.action == AgentAction.CREATE_BLUEPRINT:
                    blueprint_spec = hitl_service.extract_blueprint(structured_output)
                    if blueprint_spec:
                        try:
                            # Convert spec to config and create blueprint
                            config = hitl_service.blueprint_spec_to_config(blueprint_spec)
                            blueprint = blueprint_service.create(config)
                            session.blueprint_id = blueprint.id
                            session_service.update(session)

                            # Emit created event
                            yield {
                                "event": "created",
                                "data": json.dumps(ChatEvent(
                                    type="created",
                                    blueprint_id=blueprint.id,
                                    studio_url=blueprint.studio_url,
                                ).model_dump()),
                            }
                        except Exception as e:
                            yield {
                                "event": "error",
                                "data": json.dumps(ChatEvent(
                                    type="error",
                                    content=f"Failed to create blueprint: {str(e)}",
                                ).model_dump()),
                            }

                # Store clean text (without JSON block) in session
                session_service.add_message(session.session_id, "assistant", clean_text)
            else:
                # No structured output, store full response
                session_service.add_message(session.session_id, "assistant", full_response)

            # Done event
            yield {
                "event": "done",
                "data": json.dumps(ChatEvent(type="done").model_dump()),
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps(ChatEvent(
                    type="error",
                    content=str(e),
                ).model_dump()),
            }

    return EventSourceResponse(event_generator())
