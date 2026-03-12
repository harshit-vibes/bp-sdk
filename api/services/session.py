"""Session management service."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional

from ..models.hitl import HITLSuggestion
from ..models.session import Message, Session


class SessionService:
    """In-memory session management with TTL."""

    def __init__(self, ttl_minutes: int = 60) -> None:
        """Initialize session service.

        Args:
            ttl_minutes: Session time-to-live in minutes
        """
        self.sessions: dict[str, Session] = {}
        self.ttl_minutes = ttl_minutes

    def create(self, session_id: Optional[str] = None) -> Session:
        """Create a new session.

        Args:
            session_id: Optional session ID (generated if not provided)

        Returns:
            The created session
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        session = Session(
            session_id=session_id,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )
        self.sessions[session_id] = session
        self._cleanup_expired()
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.

        Args:
            session_id: The session ID

        Returns:
            The session if found and not expired, None otherwise
        """
        self._cleanup_expired()
        session = self.sessions.get(session_id)
        if session:
            session.last_activity = datetime.utcnow()
        return session

    def update(self, session: Session) -> None:
        """Update a session.

        Args:
            session: The session to update
        """
        session.last_activity = datetime.utcnow()
        self.sessions[session.session_id] = session

    def delete(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: The session ID to delete
        """
        self.sessions.pop(session_id, None)

    def add_message(
        self, session_id: str, role: str, content: str
    ) -> Optional[Session]:
        """Add a message to session history.

        Args:
            session_id: The session ID
            role: Message role (user, assistant, system)
            content: Message content

        Returns:
            Updated session or None if not found
        """
        session = self.get(session_id)
        if not session:
            return None

        message = Message(
            role=role,  # type: ignore
            content=content,
            timestamp=datetime.utcnow(),
        )
        session.messages.append(message)
        self.update(session)
        return session

    def set_pending_hitl(
        self, session_id: str, hitl: HITLSuggestion
    ) -> Optional[Session]:
        """Set pending HITL for a session.

        Args:
            session_id: The session ID
            hitl: The HITL suggestion

        Returns:
            Updated session or None if not found
        """
        session = self.get(session_id)
        if not session:
            return None

        session.pending_hitl = hitl
        self.update(session)
        return session

    def clear_pending_hitl(self, session_id: str) -> Optional[Session]:
        """Clear pending HITL for a session.

        Args:
            session_id: The session ID

        Returns:
            Updated session or None if not found
        """
        session = self.get(session_id)
        if not session:
            return None

        session.pending_hitl = None
        self.update(session)
        return session

    def _cleanup_expired(self) -> None:
        """Remove expired sessions."""
        now = datetime.utcnow()
        expiry = timedelta(minutes=self.ttl_minutes)

        expired = [
            sid
            for sid, session in self.sessions.items()
            if now - session.last_activity > expiry
        ]

        for sid in expired:
            del self.sessions[sid]
