"""Chat models."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from .hitl import HITLSuggestion


class ChatRequest(BaseModel):
    """Request for chat streaming."""

    session_id: Optional[str] = None
    message: Optional[str] = None
    hitl_response: Optional[str] = None


class ChatEvent(BaseModel):
    """An event in the chat stream."""

    type: Literal["text", "hitl", "created", "done", "error"]
    content: Optional[str] = None
    hitl: Optional[HITLSuggestion] = None
    blueprint_id: Optional[str] = None
    studio_url: Optional[str] = None
