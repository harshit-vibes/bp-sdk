"""API Configuration.

Settings loaded from environment variables with pydantic-settings.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Lyzr credentials
    lyzr_api_key: str
    blueprint_bearer_token: str
    lyzr_org_id: str

    # Legacy: Blueprint Builder manager agent ID (from Phase 1)
    builder_agent_id: str = "695aad9ba45696ac999e18cf"

    # App-orchestrated agents (Phase 2)
    architect_agent_id: str = "695ddac652ab53b7bf377604"
    crafter_agent_id: str = "695ddac628a3f341188dfa81"

    # UI enhancement agents (Phase 3)
    loader_agent_id: str = "695d568328a3f341188df4da"  # Witty loading text generator
    suggest_agent_id: str = "695d568428a3f341188df4db"  # Contextual revision suggestions
    options_agent_id: str = "695d568552ab53b7bf377073"  # Dynamic statement options generator
    reply_suggester_agent_id: str = "695dcae732e7bb62a51c7d42"  # Chat reply suggestions
    idea_suggester_agent_id: str = "695dcae752ab53b7bf37758d"  # Create another suggestions

    # API URLs
    agent_api_url: str = "https://agent-prod.studio.lyzr.ai"
    blueprint_api_url: str = "https://pagos-prod.studio.lyzr.ai"

    # Session configuration
    session_ttl_minutes: int = 60

    # CORS origins
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
