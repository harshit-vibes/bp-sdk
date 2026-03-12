"""Blueprint Builder API - FastAPI Application.

Main entry point for the conversational blueprint creation backend.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routes import builder, chat, health, sessions
from .services.session import SessionService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup: Initialize services
    settings = get_settings()
    app.state.session_service = SessionService(ttl_minutes=settings.session_ttl_minutes)
    print(f"Blueprint Builder API started on {settings.host}:{settings.port}")
    print(f"Builder Agent ID: {settings.builder_agent_id}")
    print(f"Architect Agent ID: {settings.architect_agent_id or '(not configured)'}")
    print(f"Crafter Agent ID: {settings.crafter_agent_id or '(not configured)'}")
    print(f"Loader Agent ID: {settings.loader_agent_id or '(not configured - using fallbacks)'}")
    print(f"Suggest Agent ID: {settings.suggest_agent_id or '(not configured - using fallbacks)'}")

    yield

    # Shutdown: Cleanup
    print("Blueprint Builder API shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Blueprint Builder API",
        description="Conversational blueprint creation with HITL checkpoints",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(health.router, tags=["Health"])
    app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(builder.router, prefix="/api/v1/builder", tags=["Builder"])

    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
