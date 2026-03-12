"""Inference service for streaming from Lyzr agents."""

from __future__ import annotations

from typing import AsyncGenerator

import httpx


class InferenceService:
    """Stream responses from Lyzr Agent API."""

    def __init__(
        self,
        agent_id: str,
        api_key: str,
        base_url: str = "https://agent-prod.studio.lyzr.ai",
    ) -> None:
        """Initialize inference service.

        Args:
            agent_id: The agent ID to stream from
            api_key: Lyzr API key
            base_url: Agent API base URL
        """
        self.agent_id = agent_id
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def stream(
        self,
        session_id: str,
        message: str,
        user_id: str = "builder-user",
        timeout: float = 180.0,
    ) -> AsyncGenerator[str, None]:
        """Stream response from the agent.

        Args:
            session_id: Session ID for context
            message: User message
            user_id: User identifier
            timeout: Request timeout in seconds

        Yields:
            Text chunks from the agent response
        """
        payload = {
            "agent_id": self.agent_id,
            "session_id": session_id,
            "user_id": user_id,
            "message": message,
        }

        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v3/inference/stream/",
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    # Handle SSE format: data: <content>
                    if line.startswith("data: "):
                        content = line[6:]  # Remove "data: " prefix

                        # Check for end marker
                        if content == "[DONE]":
                            break

                        yield content
