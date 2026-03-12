"""Session management routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..models.session import Session, SessionResponse

router = APIRouter()


@router.post("/", response_model=SessionResponse)
async def create_session(request: Request) -> SessionResponse:
    """Create a new chat session."""
    session_service = request.app.state.session_service
    session = session_service.create()
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        message="Session created successfully",
    )


@router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str, request: Request) -> Session:
    """Get session details."""
    session_service = request.app.state.session_service
    session = session_service.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str, request: Request) -> dict[str, str]:
    """Delete a session."""
    session_service = request.app.state.session_service
    if not session_service.get(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    session_service.delete(session_id)
    return {"message": "Session deleted successfully"}
