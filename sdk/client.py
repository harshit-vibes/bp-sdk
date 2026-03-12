"""Blueprint Client

Main interface for the bp-sdk.
Provides CRUD operations for blueprints with automatic sync handling.
"""

import logging
from typing import Any

from .api import AgentAPI, BlueprintAPI, MarketplaceAPI

logger = logging.getLogger(__name__)
from .builders import PayloadBuilder, TreeBuilder
from .exceptions import (
    AgentCreationError,
    APIError,
    BlueprintCreationError,
    SyncError,
    ValidationError,
)
from .models import (
    AgentConfig,
    App,
    AppConfig,
    AppTags,
    Blueprint,
    BlueprintConfig,
    BlueprintUpdate,
    ListFilters,
    ValidationReport,
    Visibility,
)
from .utils.sanitize import sanitize_agent_data, sanitize_for_update
from .utils.validation import doctor, validate_blueprint_data


class BlueprintClient:
    """Client for managing Lyzr blueprints and agents.

    This is the main interface for the bp-sdk. It handles:
    - Creating blueprints with manager and worker agents
    - Fetching and listing blueprints with advanced filters
    - Updating blueprints with automatic tree sync
    - Deleting blueprints with cleanup
    - Visibility management
    - Validation (doctor)

    Example:
        ```python
        from sdk import BlueprintClient, BlueprintConfig, AgentConfig

        client = BlueprintClient(
            agent_api_key="...",
            blueprint_bearer_token="...",
            organization_id="...",
        )

        config = BlueprintConfig(
            name="HR Assistant",
            description="Automates HR workflows",
            manager=AgentConfig(
                name="HR Manager",
                description="Orchestrates HR tasks",
                instructions="You are an HR manager...",
            ),
            workers=[
                AgentConfig(
                    name="Resume Screener",
                    description="Screens resumes",
                    instructions="You analyze resumes...",
                    features=["memory"],  # Optional: enable memory feature
                    usage_description="Use for resume analysis",
                ),
            ],
        )

        blueprint = client.create(config)
        print(f"Created: {blueprint.studio_url}")
        ```
    """

    def __init__(
        self,
        agent_api_key: str,
        blueprint_bearer_token: str,
        organization_id: str,
        user_id: str | None = None,
        agent_base_url: str | None = None,
        blueprint_base_url: str | None = None,
    ):
        """Initialize Blueprint client.

        Args:
            agent_api_key: X-API-Key for Agent API
            blueprint_bearer_token: Bearer token for Blueprint API
            organization_id: Organization ID for Blueprint API
            user_id: Optional user ID (for sharing defaults)
            agent_base_url: Optional Agent API base URL
            blueprint_base_url: Optional Blueprint API base URL
        """
        self._agent_api = AgentAPI(agent_api_key, agent_base_url)
        self._blueprint_api = BlueprintAPI(
            blueprint_bearer_token, organization_id, blueprint_base_url
        )
        self._organization_id = organization_id
        self._user_id = user_id
        self._bearer_token = blueprint_bearer_token
        self._payload_builder = PayloadBuilder()
        self._tree_builder = TreeBuilder()
        self._marketplace_api: MarketplaceAPI | None = None

    @property
    def default_share_org_ids(self) -> list[str]:
        """Get default organization IDs for sharing (self org)."""
        return [self._organization_id]

    @property
    def default_share_user_ids(self) -> list[str]:
        """Get default user IDs for sharing (self user)."""
        if self._user_id:
            return [self._user_id]
        return []

    @property
    def marketplace_api(self) -> MarketplaceAPI:
        """Get marketplace API client (lazy initialization).

        Requires user_id to be set in client initialization.

        Raises:
            ValueError: If user_id was not provided during initialization
        """
        if self._marketplace_api is None:
            if not self._user_id:
                raise ValueError(
                    "user_id is required for marketplace operations. "
                    "Provide it when initializing BlueprintClient."
                )
            self._marketplace_api = MarketplaceAPI(
                bearer_token=self._bearer_token,
                user_id=self._user_id,
            )
        return self._marketplace_api

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_worker_ids(bp_data: dict[str, Any]) -> list[str]:
        """Extract worker agent IDs from blueprint data.

        Workers are all agents in the blueprint except the manager.
        Uses the agents dict and excludes the manager_agent_id.

        Args:
            bp_data: Blueprint data dict (from blueprint_data field)

        Returns:
            List of worker agent IDs
        """
        manager_id = bp_data.get("manager_agent_id", "")
        agents = bp_data.get("agents", {})

        # Workers are all agents except the manager
        return [agent_id for agent_id in agents.keys() if agent_id != manager_id]

    def _rollback_agents(self, agent_ids: list[str], operation: str) -> list[tuple[str, str]]:
        """Rollback created agents with logging.

        Attempts to delete all agents in the list, logging failures.

        Args:
            agent_ids: List of agent IDs to delete
            operation: Description of the operation that failed (for logging)

        Returns:
            List of (agent_id, error_message) tuples for failed deletions
        """
        failed_cleanups: list[tuple[str, str]] = []

        for agent_id in agent_ids:
            try:
                self._agent_api.delete(agent_id)
                logger.debug(f"Rollback: deleted agent {agent_id}")
            except Exception as e:
                error_msg = str(e)
                failed_cleanups.append((agent_id, error_msg))
                logger.warning(
                    f"Rollback failed for agent {agent_id} during {operation}: {error_msg}"
                )

        if failed_cleanups:
            logger.error(
                f"Rollback incomplete during {operation}: "
                f"{len(failed_cleanups)}/{len(agent_ids)} agents failed to delete"
            )

        return failed_cleanups

    def _find_marketplace_app_by_agent(self, agent_id: str) -> str | None:
        """Find marketplace app ID for a given agent.

        Searches user's marketplace apps to find one with matching agent_id.

        Args:
            agent_id: Agent ID to search for

        Returns:
            Marketplace app ID if found, None otherwise
        """
        if not self._user_id:
            return None

        # Try listing by organization first
        try:
            result = self.marketplace_api.list_by_organization(
                organization_id=self._organization_id,
                limit=100,
            )
            apps_data = result if isinstance(result, list) else result.get("data", [])

            for app_data in apps_data:
                if app_data.get("agent_id") == agent_id:
                    return app_data.get("id") or app_data.get("_id")
        except Exception:
            pass

        # Fallback: try listing by user
        try:
            apps_data = self.marketplace_api.list_by_user()
            for app_data in apps_data:
                if app_data.get("agent_id") == agent_id:
                    return app_data.get("id") or app_data.get("_id")
        except Exception:
            pass

        return None

    def _publish_or_update_marketplace(
        self,
        manager_id: str,
        name: str,
        description: str,
        marketplace_name: str | None = None,
        marketplace_description: str | None = None,
        welcome_message: str | None = None,
        industry: str | None = None,
        function: str | None = None,
        marketplace_category: str | None = None,
    ) -> str | None:
        """Publish manager to marketplace or update existing app.

        Args:
            manager_id: Manager agent ID
            name: Blueprint name (fallback for app name)
            description: Blueprint description (fallback for app description)
            marketplace_name: Custom app name
            marketplace_description: Custom app description
            welcome_message: Welcome message
            industry: Industry tag
            function: Function tag
            marketplace_category: Category tag

        Returns:
            Marketplace app ID if successful, None otherwise
        """
        if not self._user_id:
            logger.warning("Cannot publish to marketplace: user_id not set")
            return None

        try:
            # Check if already published
            existing_app_id = self._find_marketplace_app_by_agent(manager_id)

            app_name = marketplace_name or name
            app_desc = marketplace_description or description

            if existing_app_id:
                # Update existing app
                result = self.marketplace_api.update(
                    app_id=existing_app_id,
                    name=app_name,
                    description=app_desc,
                    welcome_message=welcome_message,
                    industry=industry,
                    function=function,
                    category=marketplace_category,
                )
                logger.info(f"Updated marketplace app: {existing_app_id}")
                return existing_app_id
            else:
                # Create new app
                try:
                    result = self.marketplace_api.create(
                        name=app_name,
                        agent_id=manager_id,
                        description=app_desc,
                        creator="SDK",
                        public=True,
                        organization_id=self._organization_id,
                        welcome_message=welcome_message,
                        industry=industry,
                        function=function,
                        category=marketplace_category,
                    )
                    app_id = result.get("id") or result.get("_id")
                    logger.info(f"Published to marketplace: {app_id}")
                    return app_id
                except APIError as create_err:
                    # If app already exists, try to find and update it
                    if "already exists" in str(create_err).lower():
                        logger.info("App already exists, trying to find and update...")
                        # Try to find by name (get accepts name or ID)
                        try:
                            existing = self.marketplace_api.get(app_name)
                            found_app_id = existing.get("id") or existing.get("_id")
                            if found_app_id:
                                self.marketplace_api.update(
                                    app_id=found_app_id,
                                    description=app_desc,
                                    welcome_message=welcome_message,
                                    industry=industry,
                                    function=function,
                                    category=marketplace_category,
                                )
                                logger.info(f"Updated existing marketplace app: {found_app_id}")
                                return found_app_id
                        except Exception:
                            pass
                    raise create_err

        except Exception as e:
            logger.warning(f"Failed to publish/update marketplace: {e}")
            return None

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    def create(self, config: BlueprintConfig) -> Blueprint:
        """Create a new blueprint with agents and publish to marketplace.

        This performs the full creation sequence:
        1. Validate configuration
        2. Create worker agents
        3. Create manager agent with managed_agents
        4. Build tree structure
        5. Create blueprint
        6. Publish manager to marketplace (if enabled)

        By default, the manager agent is automatically published to the
        marketplace. Set `config.publish_to_marketplace=False` to disable.

        On failure, automatically rolls back created agents.

        Args:
            config: Blueprint configuration

        Returns:
            Created Blueprint object with:
            - `studio_url`: URL to view blueprint in Lyzr Studio
            - `marketplace_url`: URL to view manager in marketplace (if published)
            - `marketplace_app_id`: Marketplace app ID (if published)

        Raises:
            ValidationError: If configuration is invalid
            AgentCreationError: If agent creation fails
            BlueprintCreationError: If blueprint creation fails

        Example:
            ```python
            config = BlueprintConfig(
                name="My Assistant",
                description="Helpful assistant blueprint",
                manager=AgentConfig(...),
                workers=[AgentConfig(...)],
                # Marketplace config (all optional)
                industry="Technology",
                function="Support",
                marketplace_category="Productivity",
            )
            blueprint = client.create(config)
            print(f"Blueprint: {blueprint.studio_url}")
            print(f"Marketplace: {blueprint.marketplace_url}")
            ```
        """
        # 1. Validate
        report = self.doctor_config(config)
        if not report.valid:
            raise ValidationError(report.errors)

        # Track created agents for rollback
        created_agent_ids: list[str] = []

        try:
            # 2. Create workers first
            worker_ids: list[str] = []
            workers_data: list[dict] = []

            for worker in config.workers:
                payload = self._payload_builder.build_agent_payload(
                    worker, is_manager=False
                )
                result = self._agent_api.create(payload)
                agent_id = result.get("agent_id") or result.get("_id") or result.get("id")

                if not agent_id:
                    raise AgentCreationError(
                        worker.name, "No ID returned from API", created_agent_ids
                    )

                created_agent_ids.append(agent_id)
                worker_ids.append(agent_id)

                # Fetch full data for tree building
                full_data = self._agent_api.get(agent_id)
                workers_data.append(sanitize_agent_data(full_data))

            # 3. Create manager with managed_agents
            managed_agents = self._payload_builder.build_managed_agents_list(
                config.workers, worker_ids
            )
            manager_payload = self._payload_builder.build_agent_payload(
                config.manager, is_manager=True, managed_agents=managed_agents
            )
            manager_result = self._agent_api.create(manager_payload)
            manager_id = manager_result.get("agent_id") or manager_result.get("_id") or manager_result.get("id")

            if not manager_id:
                raise AgentCreationError(
                    config.manager.name, "No ID returned from API", created_agent_ids
                )

            created_agent_ids.append(manager_id)

            # Fetch full manager data
            manager_data = sanitize_agent_data(self._agent_api.get(manager_id))

            # 4. Build tree structure
            tree_data = self._tree_builder.build(
                manager_data=manager_data,
                workers_data=workers_data,
                manager_id=manager_id,
                worker_ids=worker_ids,
            )

            # Validate tree before sending
            errors = validate_blueprint_data(tree_data)
            if errors:
                raise BlueprintCreationError(
                    config.name,
                    f"Tree validation failed: {'; '.join(errors)}",
                    created_agent_ids,
                )

            # 5. Create blueprint
            bp_payload = self._payload_builder.build_blueprint_payload(
                config=config,
                tree_data=tree_data,
                manager_id=manager_id,
            )
            bp_result = self._blueprint_api.create(bp_payload)
            blueprint_id = bp_result.get("_id") or bp_result.get("id")

            if not blueprint_id:
                raise BlueprintCreationError(
                    config.name, "No ID returned from API", created_agent_ids
                )

            # 6. Publish to marketplace (if enabled and user_id is set)
            marketplace_app_id: str | None = None
            if config.publish_to_marketplace and self._user_id:
                marketplace_app_id = self._publish_or_update_marketplace(
                    manager_id=manager_id,
                    name=config.name,
                    description=config.description,
                    marketplace_name=config.marketplace_name,
                    marketplace_description=config.marketplace_description,
                    welcome_message=config.welcome_message,
                    industry=config.industry,
                    function=config.function,
                    marketplace_category=config.marketplace_category,
                )

            return Blueprint.from_api_response(
                bp_result, manager_id, worker_ids, marketplace_app_id
            )

        except Exception as e:
            # Rollback: delete created agents with logging
            self._rollback_agents(created_agent_ids, f"create_blueprint:{config.name}")

            if isinstance(e, (ValidationError, AgentCreationError, BlueprintCreationError)):
                raise
            raise BlueprintCreationError(config.name, str(e), created_agent_ids)

    def get(self, blueprint_id: str) -> Blueprint:
        """Get a blueprint by ID.

        Args:
            blueprint_id: Blueprint API ID

        Returns:
            Blueprint object
        """
        data = self._blueprint_api.get(blueprint_id)
        bp_data = data.get("blueprint_data", {})

        manager_id = bp_data.get("manager_agent_id", "")
        worker_ids = self._extract_worker_ids(bp_data)

        return Blueprint.from_api_response(data, manager_id, worker_ids)

    def get_all(self, filters: ListFilters | None = None) -> list[Blueprint]:
        """List all blueprints.

        Args:
            filters: Optional filters for listing

        Returns:
            List of Blueprint objects
        """
        filters = filters or ListFilters()
        result = self._blueprint_api.list(
            page_size=filters.page_size,
            page=filters.page,
            share_type=filters.visibility.value if filters.visibility else None,
            category=filters.category,
            search=filters.search,
            orchestration_type=filters.orchestration_type,
            tags=filters.tags,
            owner_id=filters.owner_id,
            is_template=filters.is_template,
            sort_by=filters.sort_by,
        )

        # Extract blueprints list from response
        data_list = result.get("blueprints", []) if isinstance(result, dict) else result

        blueprints = []
        for data in data_list:
            bp_data = data.get("blueprint_data", {})
            manager_id = bp_data.get("manager_agent_id", "")
            worker_ids = self._extract_worker_ids(bp_data)
            blueprints.append(Blueprint.from_api_response(data, manager_id, worker_ids))

        return blueprints

    def get_all_with_pagination(
        self, filters: ListFilters | None = None
    ) -> tuple[list[Blueprint], dict]:
        """List blueprints with pagination info.

        Args:
            filters: Optional filters for listing

        Returns:
            Tuple of (blueprints list, pagination info dict)
            Pagination info: {"total": int, "page": int, "has_more": bool}
        """
        filters = filters or ListFilters()
        result = self._blueprint_api.list(
            page_size=filters.page_size,
            page=filters.page,
            share_type=filters.visibility.value if filters.visibility else None,
            category=filters.category,
            search=filters.search,
            orchestration_type=filters.orchestration_type,
            tags=filters.tags,
            owner_id=filters.owner_id,
            is_template=filters.is_template,
            sort_by=filters.sort_by,
        )

        # Extract blueprints list
        data_list = result.get("blueprints", []) if isinstance(result, dict) else result

        blueprints = []
        for data in data_list:
            bp_data = data.get("blueprint_data", {})
            manager_id = bp_data.get("manager_agent_id", "")
            worker_ids = self._extract_worker_ids(bp_data)
            blueprints.append(Blueprint.from_api_response(data, manager_id, worker_ids))

        # Extract pagination info
        pagination = {
            "total": result.get("total", len(blueprints)),
            "page": result.get("page", filters.page),
            "has_more": result.get("has_more", False),
        }

        return blueprints, pagination

    def update(self, blueprint_id: str, updates: BlueprintUpdate) -> Blueprint:
        """Update a blueprint and publish/update marketplace app.

        Smart path detection:
        - If only metadata fields (name, description, tags, category, visibility, readme)
          are being updated, uses fast path without touching agents.
        - If agent changes are included, performs full sync.

        Full sync handles:
        1. Update agents via Agent API
        2. Fetch fresh agent data
        3. Rebuild tree structure
        4. Update blueprint with fresh tree
        5. Publish/update marketplace app (if enabled)

        Args:
            blueprint_id: Blueprint API ID
            updates: Update configuration

        Returns:
            Updated Blueprint object with marketplace info

        Raises:
            SyncError: If sync fails
        """
        # Smart path detection: check if only metadata is changing
        has_agent_changes = updates.manager is not None or (
            updates.workers is not None and len(updates.workers) > 0
        )

        if not has_agent_changes:
            # FAST PATH: Only metadata changes, skip agent sync
            # But still publish to marketplace if requested
            blueprint = self.update_metadata(
                blueprint_id,
                name=updates.name,
                description=updates.description,
                tags=updates.tags,
                category=updates.category,
                visibility=updates.visibility,
            )

            # Publish to marketplace if enabled
            marketplace_app_id: str | None = None
            if updates.publish_to_marketplace and self._user_id:
                marketplace_app_id = self._publish_or_update_marketplace(
                    manager_id=blueprint.manager_id,
                    name=updates.name or blueprint.name,
                    description=updates.description or blueprint.description,
                    marketplace_name=updates.marketplace_name,
                    marketplace_description=updates.marketplace_description,
                    welcome_message=updates.welcome_message,
                    industry=updates.industry,
                    function=updates.function,
                    marketplace_category=updates.marketplace_category,
                )

            # Return blueprint with marketplace info
            if marketplace_app_id:
                return Blueprint.from_api_response(
                    self._blueprint_api.get(blueprint_id),
                    blueprint.manager_id,
                    blueprint.worker_ids,
                    marketplace_app_id,
                )
            return blueprint

        # FULL PATH: Agent changes require full sync
        # 1. Fetch current blueprint
        current = self._blueprint_api.get(blueprint_id)
        bp_data = current.get("blueprint_data", {})
        manager_id = bp_data.get("manager_agent_id")

        if not manager_id:
            raise SyncError("update", "No manager_agent_id in blueprint")

        # 2. Update agents if requested
        if updates.manager:
            self._update_agent(manager_id, updates.manager.model_dump(exclude_none=True))

        for worker_update in updates.workers or []:
            if worker_update.id:
                self._update_agent(
                    worker_update.id, worker_update.model_dump(exclude_none=True)
                )

        # 3. Fetch fresh agent data
        fresh_agents: dict[str, dict] = {}

        # Manager
        manager_data = sanitize_agent_data(self._agent_api.get(manager_id))
        fresh_agents[manager_id] = manager_data

        # Workers from managed_agents
        for ma in manager_data.get("managed_agents", []):
            worker_id = ma.get("id")
            if worker_id:
                fresh_agents[worker_id] = sanitize_agent_data(
                    self._agent_api.get(worker_id)
                )

        # 4. Rebuild tree
        # Filter out manager_id to get only worker IDs (safe, no ValueError)
        worker_ids = [aid for aid in fresh_agents.keys() if aid != manager_id]
        workers_data = [fresh_agents[wid] for wid in worker_ids]

        tree_data = self._tree_builder.build(
            manager_data=manager_data,
            workers_data=workers_data,
            manager_id=manager_id,
            worker_ids=worker_ids,
        )

        # 5. Build update payload
        field_updates = {}
        if updates.name:
            field_updates["name"] = updates.name
        if updates.description:
            field_updates["description"] = updates.description
        if updates.category:
            field_updates["category"] = updates.category
        if updates.tags is not None:
            field_updates["tags"] = updates.tags
        if updates.visibility:
            field_updates["share_type"] = updates.visibility.value
        if updates.readme:
            field_updates["readme"] = updates.readme

        bp_payload = self._payload_builder.build_update_payload(
            current_blueprint=current,
            new_tree_data=tree_data,
            updates=field_updates,
        )

        # 6. Update blueprint
        result = self._blueprint_api.update(blueprint_id, bp_payload)

        # 7. Publish to marketplace (if enabled)
        marketplace_app_id: str | None = None
        if updates.publish_to_marketplace and self._user_id:
            marketplace_app_id = self._publish_or_update_marketplace(
                manager_id=manager_id,
                name=updates.name or current.get("name", ""),
                description=updates.description or current.get("description", ""),
                marketplace_name=updates.marketplace_name,
                marketplace_description=updates.marketplace_description,
                welcome_message=updates.welcome_message,
                industry=updates.industry,
                function=updates.function,
                marketplace_category=updates.marketplace_category,
            )

        return Blueprint.from_api_response(result, manager_id, worker_ids, marketplace_app_id)

    def delete(self, blueprint_id: str, delete_agents: bool = True) -> bool:
        """Delete a blueprint.

        IMPORTANT: Agents are deleted FIRST, then blueprint.
        This ensures proper cleanup order since agents are managed by
        Agent API and blueprint is just metadata in Blueprint API.

        Args:
            blueprint_id: Blueprint API ID
            delete_agents: If True, also delete all associated agents

        Returns:
            True if deleted successfully
        """
        if delete_agents:
            # Fetch blueprint to get agent IDs
            try:
                current = self._blueprint_api.get(blueprint_id)
                bp_data = current.get("blueprint_data", {})

                # Collect all agent IDs
                agent_ids = list(bp_data.get("agents", {}).keys())

                # 1. Delete agents FIRST (Agent API) with logging
                failed_cleanups = self._rollback_agents(
                    agent_ids, f"delete_blueprint:{blueprint_id}"
                )

                if failed_cleanups:
                    logger.warning(
                        f"Some agents failed to delete for blueprint {blueprint_id}: "
                        f"{len(failed_cleanups)}/{len(agent_ids)} failed"
                    )

                # 2. Then delete blueprint (Blueprint API)
                self._blueprint_api.delete(blueprint_id)

                return True
            except Exception as e:
                logger.error(f"Error during blueprint delete {blueprint_id}: {e}")
                # If fetching fails, just try to delete blueprint
                return self._blueprint_api.delete(blueprint_id)
        else:
            return self._blueprint_api.delete(blueprint_id)

    # -------------------------------------------------------------------------
    # Visibility
    # -------------------------------------------------------------------------

    def set_visibility(
        self,
        blueprint_id: str,
        visibility: Visibility,
        user_ids: list[str] | None = None,
        organization_ids: list[str] | None = None,
    ) -> Blueprint:
        """Set blueprint visibility and sharing targets.

        Args:
            blueprint_id: Blueprint API ID
            visibility: New visibility setting
            user_ids: List of user IDs to share with (for SPECIFIC_USERS)
            organization_ids: List of organization IDs to share with (for SPECIFIC_USERS)

        Returns:
            Updated Blueprint object

        Example:
            # Make public
            client.set_visibility(bp_id, Visibility.PUBLIC)

            # Share with specific users
            client.set_visibility(
                bp_id,
                Visibility.SPECIFIC_USERS,
                user_ids=["user-1", "user-2"],
            )

            # Share with specific organizations
            client.set_visibility(
                bp_id,
                Visibility.SPECIFIC_USERS,
                organization_ids=["org-1", "org-2"],
            )
        """
        result = self._blueprint_api.set_share_type(
            blueprint_id,
            visibility.value,
            user_ids=user_ids,
            organization_ids=organization_ids,
        )
        bp_data = result.get("blueprint_data", {})
        manager_id = bp_data.get("manager_agent_id", "")
        worker_ids = self._extract_worker_ids(bp_data)
        return Blueprint.from_api_response(result, manager_id, worker_ids)

    def clone(self, blueprint_id: str, new_name: str | None = None) -> Blueprint:
        """Clone a blueprint.

        Creates a complete copy with new agent IDs.
        The cloned blueprint is always private.

        Args:
            blueprint_id: Blueprint API ID to clone
            new_name: Optional new name for the clone

        Returns:
            Cloned Blueprint object
        """
        result = self._blueprint_api.clone(
            blueprint_id,
            api_key=self._agent_api.api_key,
            new_name=new_name,
        )
        bp_data = result.get("blueprint_data", {})
        manager_id = bp_data.get("manager_agent_id", "")
        worker_ids = self._extract_worker_ids(bp_data)
        return Blueprint.from_api_response(result, manager_id, worker_ids)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def doctor(self, blueprint_id: str) -> ValidationReport:
        """Validate an existing blueprint.

        Fetches the blueprint and validates its structure.

        Args:
            blueprint_id: Blueprint API ID

        Returns:
            ValidationReport with errors and warnings
        """
        data = self._blueprint_api.get(blueprint_id)
        bp_data = data.get("blueprint_data", {})

        errors = validate_blueprint_data(bp_data)
        warnings: list[str] = []

        # Additional checks
        agents = bp_data.get("agents", {})
        for agent_id, agent_data in agents.items():
            # Check for missing usage_description on workers
            if agent_data.get("agent_role") == "Worker":
                if not agent_data.get("usage_description"):
                    warnings.append(
                        f"Worker '{agent_data.get('name', agent_id)}': "
                        "missing usage_description"
                    )

        return ValidationReport(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def doctor_config(self, config: BlueprintConfig) -> ValidationReport:
        """Validate a blueprint configuration before creation.

        Args:
            config: Blueprint configuration

        Returns:
            ValidationReport with errors and warnings
        """
        return doctor(config)

    # -------------------------------------------------------------------------
    # Sync (Advanced)
    # -------------------------------------------------------------------------

    def sync(self, blueprint_id: str) -> Blueprint:
        """Sync blueprint with latest agent data.

        Fetches fresh data from Agent API and rebuilds the tree.
        Use this if agents were updated outside the SDK.

        Args:
            blueprint_id: Blueprint API ID

        Returns:
            Synced Blueprint object
        """
        # Force full sync by fetching and rebuilding tree
        current = self._blueprint_api.get(blueprint_id)
        bp_data = current.get("blueprint_data", {})
        manager_id = bp_data.get("manager_agent_id")

        if not manager_id:
            raise SyncError("sync", "No manager_agent_id in blueprint")

        # Fetch fresh agent data
        manager_data = sanitize_agent_data(self._agent_api.get(manager_id))
        workers_data = []
        worker_ids = []

        for ma in manager_data.get("managed_agents", []):
            wid = ma.get("id")
            if wid:
                workers_data.append(sanitize_agent_data(self._agent_api.get(wid)))
                worker_ids.append(wid)

        # Rebuild tree
        tree_data = self._tree_builder.build(
            manager_data=manager_data,
            workers_data=workers_data,
            manager_id=manager_id,
            worker_ids=worker_ids,
        )

        # Update blueprint with fresh tree
        bp_payload = self._payload_builder.build_update_payload(
            current_blueprint=current,
            new_tree_data=tree_data,
            updates={},
        )
        result = self._blueprint_api.update(blueprint_id, bp_payload)

        return Blueprint.from_api_response(result, manager_id, worker_ids)

    # -------------------------------------------------------------------------
    # Fast Metadata Update
    # -------------------------------------------------------------------------

    def update_metadata(
        self,
        blueprint_id: str,
        name: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        visibility: Visibility | None = None,
    ) -> Blueprint:
        """Update blueprint metadata without touching agents or tree.

        This is a fast path that skips:
        - Agent API calls
        - Tree rebuilding
        - Full sync

        Use this for simple metadata changes like name, description, tags.

        Args:
            blueprint_id: Blueprint API ID
            name: New blueprint name
            description: New description
            tags: New tags list
            category: New category
            visibility: New visibility setting

        Returns:
            Updated Blueprint object
        """
        # Build minimal payload with only provided fields
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if tags is not None:
            payload["tags"] = tags
        if category is not None:
            payload["category"] = category
        if visibility is not None:
            payload["share_type"] = visibility.value

        if not payload:
            # Nothing to update, just return current
            return self.get(blueprint_id)

        result = self._blueprint_api.update(blueprint_id, payload)
        bp_data = result.get("blueprint_data", {})
        manager_id = bp_data.get("manager_agent_id", "")
        worker_ids = self._extract_worker_ids(bp_data)
        return Blueprint.from_api_response(result, manager_id, worker_ids)

    # -------------------------------------------------------------------------
    # Worker Management (Incremental)
    # -------------------------------------------------------------------------

    def add_worker(self, blueprint_id: str, worker: AgentConfig) -> Blueprint:
        """Add a single worker to an existing blueprint.

        This is more efficient than full update when adding one worker:
        1. Create worker agent
        2. Update manager's managed_agents
        3. Rebuild tree with new worker
        4. Update blueprint

        Args:
            blueprint_id: Blueprint API ID
            worker: Worker configuration

        Returns:
            Updated Blueprint object

        Raises:
            ValidationError: If worker config is invalid
            AgentCreationError: If worker creation fails
        """
        # 1. Fetch current blueprint
        current = self._blueprint_api.get(blueprint_id)
        bp_data = current.get("blueprint_data", {})
        manager_id = bp_data.get("manager_agent_id")

        if not manager_id:
            raise SyncError("add_worker", "No manager_agent_id in blueprint")

        # 2. Validate worker has usage_description
        if not worker.usage_description:
            raise ValidationError(["Worker must have usage_description"])

        # 3. Create worker agent
        worker_payload = self._payload_builder.build_agent_payload(
            worker, is_manager=False
        )
        worker_result = self._agent_api.create(worker_payload)
        new_worker_id = (
            worker_result.get("agent_id")
            or worker_result.get("_id")
            or worker_result.get("id")
        )

        if not new_worker_id:
            raise AgentCreationError(worker.name, "No ID returned from API", [])

        try:
            # 4. Get current manager data and update managed_agents
            manager_data = sanitize_agent_data(self._agent_api.get(manager_id))
            current_managed = manager_data.get("managed_agents", [])

            # Add new worker to managed_agents
            new_managed_agent = {
                "id": new_worker_id,
                "name": worker.name,
                "tool_usage_description": worker.usage_description,
            }
            current_managed.append(new_managed_agent)

            # Update manager with new managed_agents
            self._agent_api.update(manager_id, {"managed_agents": current_managed})

            # 5. Fetch all fresh data and rebuild tree
            manager_data = sanitize_agent_data(self._agent_api.get(manager_id))
            workers_data = []
            worker_ids = []

            for ma in manager_data.get("managed_agents", []):
                wid = ma.get("id")
                if wid:
                    workers_data.append(sanitize_agent_data(self._agent_api.get(wid)))
                    worker_ids.append(wid)

            tree_data = self._tree_builder.build(
                manager_data=manager_data,
                workers_data=workers_data,
                manager_id=manager_id,
                worker_ids=worker_ids,
            )

            # 6. Update blueprint with new tree
            bp_payload = self._payload_builder.build_update_payload(
                current_blueprint=current,
                new_tree_data=tree_data,
                updates={},
            )
            result = self._blueprint_api.update(blueprint_id, bp_payload)

            return Blueprint.from_api_response(result, manager_id, worker_ids)

        except Exception as e:
            # Rollback: delete the newly created worker
            self._rollback_agents([new_worker_id], f"add_worker:{worker.name}")
            raise

    def remove_worker(self, blueprint_id: str, worker_id: str) -> Blueprint:
        """Remove a single worker from a blueprint.

        This is the proper way to remove a worker:
        1. Remove from manager's managed_agents
        2. Rebuild tree without the worker
        3. Update blueprint
        4. Delete worker agent

        Args:
            blueprint_id: Blueprint API ID
            worker_id: Worker agent ID to remove

        Returns:
            Updated Blueprint object

        Raises:
            SyncError: If operation fails
            ValidationError: If trying to remove the last worker
        """
        # 1. Fetch current blueprint
        current = self._blueprint_api.get(blueprint_id)
        bp_data = current.get("blueprint_data", {})
        manager_id = bp_data.get("manager_agent_id")

        if not manager_id:
            raise SyncError("remove_worker", "No manager_agent_id in blueprint")

        # 2. Get current workers
        current_worker_ids = self._extract_worker_ids(bp_data)

        if worker_id not in current_worker_ids:
            raise ValidationError([f"Worker {worker_id} not found in blueprint"])

        # Note: Removing the last worker is allowed - creates a single-agent blueprint

        # 3. Get manager and remove worker from managed_agents
        manager_data = sanitize_agent_data(self._agent_api.get(manager_id))
        current_managed = manager_data.get("managed_agents", [])
        new_managed = [ma for ma in current_managed if ma.get("id") != worker_id]

        # Update manager with new managed_agents
        self._agent_api.update(manager_id, {"managed_agents": new_managed})

        # 4. Fetch fresh data and rebuild tree (without removed worker)
        manager_data = sanitize_agent_data(self._agent_api.get(manager_id))
        workers_data = []
        worker_ids = []

        for ma in manager_data.get("managed_agents", []):
            wid = ma.get("id")
            if wid:
                workers_data.append(sanitize_agent_data(self._agent_api.get(wid)))
                worker_ids.append(wid)

        tree_data = self._tree_builder.build(
            manager_data=manager_data,
            workers_data=workers_data,
            manager_id=manager_id,
            worker_ids=worker_ids,
        )

        # 5. Update blueprint with new tree
        bp_payload = self._payload_builder.build_update_payload(
            current_blueprint=current,
            new_tree_data=tree_data,
            updates={},
        )
        result = self._blueprint_api.update(blueprint_id, bp_payload)

        # 6. Delete the removed worker agent
        try:
            self._agent_api.delete(worker_id)
        except Exception as e:
            logger.warning(f"Failed to delete removed worker {worker_id}: {e}")

        return Blueprint.from_api_response(result, manager_id, worker_ids)

    # -------------------------------------------------------------------------
    # Agent Inspection
    # -------------------------------------------------------------------------

    def get_manager(self, blueprint_id: str) -> dict[str, Any]:
        """Get manager agent details from a blueprint.

        Always fetches fresh data from Agent API (blueprint_data.agents may be stale).

        Args:
            blueprint_id: Blueprint API ID

        Returns:
            Manager agent data dictionary
        """
        data = self._blueprint_api.get(blueprint_id)
        bp_data = data.get("blueprint_data", {})
        manager_id = bp_data.get("manager_agent_id")

        if not manager_id:
            raise SyncError("get_manager", "No manager_agent_id in blueprint")

        # Always fetch from Agent API (blueprint_data.agents may be stale)
        return self._agent_api.get(manager_id)

    def get_workers(self, blueprint_id: str) -> list[dict[str, Any]]:
        """Get all worker agents from a blueprint.

        Always fetches fresh data from Agent API (blueprint_data.agents may be stale).

        Args:
            blueprint_id: Blueprint API ID

        Returns:
            List of worker agent data dictionaries
        """
        data = self._blueprint_api.get(blueprint_id)
        bp_data = data.get("blueprint_data", {})
        worker_ids = self._extract_worker_ids(bp_data)

        # Always fetch from Agent API (blueprint_data.agents may be stale)
        workers = []
        for wid in worker_ids:
            workers.append(self._agent_api.get(wid))

        return workers

    # -------------------------------------------------------------------------
    # YAML-Based Operations
    # -------------------------------------------------------------------------

    def create_from_yaml(self, yaml_path: "Path") -> Blueprint:
        """Create blueprint from YAML definition.

        This method:
        1. Loads and validates the YAML files
        2. Converts to BlueprintConfig
        3. Creates the blueprint via create()
        4. Writes IDs back to the YAML file

        Args:
            yaml_path: Path to blueprint.yaml file

        Returns:
            Created Blueprint object

        Example:
            ```python
            blueprint = client.create_from_yaml(Path("my-blueprint/blueprint.yaml"))
            print(f"Created: {blueprint.studio_url}")
            ```
        """
        from pathlib import Path

        from .yaml import BlueprintLoader, IDManager, load_and_convert

        yaml_path = Path(yaml_path)

        # Load and convert YAML to config
        loader = BlueprintLoader()
        blueprint_yaml, agents = loader.load(yaml_path)
        config = load_and_convert(yaml_path)

        # Create the blueprint
        blueprint = self.create(config)

        # Build agent ID mapping (file path -> agent ID)
        agent_ids: dict[str, str] = {}

        # Get manager ID
        manager_path = blueprint_yaml.root_agents[0]
        agent_ids[manager_path] = blueprint.manager_id

        # Get worker IDs in order
        agent_order = loader.get_agent_order()
        worker_paths = [p for p in agent_order if p != str(yaml_path.parent / manager_path)]

        for i, worker_path in enumerate(worker_paths):
            if i < len(blueprint.worker_ids):
                # Convert absolute path back to relative
                rel_path = self._make_relative_path(yaml_path.parent, worker_path)
                agent_ids[rel_path] = blueprint.worker_ids[i]

        # Write IDs back to YAML
        id_manager = IDManager(yaml_path)
        id_manager.save_ids(blueprint.id, agent_ids)

        return blueprint

    def update_from_yaml(self, yaml_path: "Path") -> Blueprint:
        """Update blueprint from YAML definition.

        This method:
        1. Loads YAML with existing IDs
        2. Updates agents and blueprint metadata
        3. Syncs the blueprint tree

        Args:
            yaml_path: Path to blueprint.yaml file (must have IDs section)

        Returns:
            Updated Blueprint object

        Raises:
            ValidationError: If YAML has no IDs (use create_from_yaml instead)
        """
        from pathlib import Path

        from .yaml import BlueprintLoader, IDManager, yaml_to_config

        yaml_path = Path(yaml_path)

        # Load YAML
        loader = BlueprintLoader()
        blueprint_yaml, agents = loader.load(yaml_path)

        # Check for IDs
        id_manager = IDManager(yaml_path)
        blueprint_id = id_manager.get_blueprint_id()

        if not blueprint_id:
            raise ValidationError(
                errors=["No blueprint ID found in YAML. Use create_from_yaml() for new blueprints."]
            )

        # Convert to config for validation
        config = yaml_to_config(blueprint_yaml, agents, loader)

        # Update each agent
        agent_order = loader.get_agent_order()

        for agent_path in agent_order:
            agent_id = id_manager.get_agent_id(
                self._make_relative_path(yaml_path.parent, agent_path)
            )
            if agent_id and agent_path in agents:
                agent_yaml = agents[agent_path]
                self._update_agent_from_yaml(agent_id, agent_yaml)

        # Update blueprint metadata
        self.update_metadata(
            blueprint_id,
            name=config.name,
            description=config.description,
            category=config.category,
            tags=config.tags,
            visibility=config.visibility,
        )

        # Sync to rebuild tree
        return self.sync(blueprint_id)

    def export_to_yaml(
        self,
        blueprint_id: str,
        output_dir: "Path",
        blueprint_filename: str = "blueprint.yaml",
    ) -> "Path":
        """Export blueprint to YAML files.

        This method:
        1. Fetches the blueprint and all agents
        2. Converts to YAML format
        3. Writes files to the output directory

        Args:
            blueprint_id: Blueprint API ID
            output_dir: Directory to write YAML files
            blueprint_filename: Name for blueprint file (default: blueprint.yaml)

        Returns:
            Path to the created blueprint.yaml file

        Example:
            ```python
            path = client.export_to_yaml("bp-123", Path("./exported"))
            print(f"Exported to: {path}")
            ```
        """
        from pathlib import Path

        from .yaml import api_response_to_yaml, write_blueprint

        output_dir = Path(output_dir)

        # Get blueprint data
        blueprint_data = self._blueprint_api.get(blueprint_id)

        # Get manager
        bp_data = blueprint_data.get("blueprint_data", {})
        manager_id = bp_data.get("manager_agent_id")
        worker_ids = self._extract_worker_ids(bp_data)

        # Fetch all agents
        agents = []
        if manager_id:
            agents.append(self._agent_api.get(manager_id))
        for wid in worker_ids:
            agents.append(self._agent_api.get(wid))

        # Convert to YAML format
        blueprint_yaml, agent_yamls = api_response_to_yaml(blueprint_data, agents)

        # Write files
        return write_blueprint(output_dir, blueprint_yaml, agent_yamls, blueprint_filename)

    def validate_yaml(self, yaml_path: "Path") -> ValidationReport:
        """Validate YAML blueprint without making API calls.

        This method:
        1. Loads and parses YAML files
        2. Checks all file references exist
        3. Converts to BlueprintConfig
        4. Runs doctor() validation

        Args:
            yaml_path: Path to blueprint.yaml file

        Returns:
            ValidationReport with validation results

        Example:
            ```python
            report = client.validate_yaml(Path("my-blueprint/blueprint.yaml"))
            if report.valid:
                print("YAML is valid!")
            else:
                for error in report.errors:
                    print(f"Error: {error}")
            ```
        """
        from pathlib import Path

        from .yaml import BlueprintLoader, yaml_to_config

        yaml_path = Path(yaml_path)
        errors: list[str] = []
        warnings: list[str] = []

        # Step 1: Load YAML
        try:
            loader = BlueprintLoader()
            blueprint_yaml, agents = loader.load(yaml_path)
        except ValidationError as e:
            return ValidationReport(valid=False, errors=e.errors, warnings=[])
        except Exception as e:
            return ValidationReport(valid=False, errors=[str(e)], warnings=[])

        # Step 2: Check file references
        missing = loader.validate_all_files_exist()
        if missing:
            errors.extend([f"Missing file: {f}" for f in missing])

        # Step 3: Convert to config
        try:
            config = yaml_to_config(blueprint_yaml, agents, loader)
        except Exception as e:
            errors.append(f"Conversion error: {e}")
            return ValidationReport(valid=False, errors=errors, warnings=warnings)

        # Step 4: Run doctor validation
        doctor_report = self.doctor_config(config)

        # Merge results
        errors.extend(doctor_report.errors)
        warnings.extend(doctor_report.warnings)

        return ValidationReport(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _update_agent_from_yaml(self, agent_id: str, agent_yaml: "AgentYAML") -> dict:
        """Update an agent from YAML model.

        Args:
            agent_id: Agent API ID
            agent_yaml: AgentYAML model

        Returns:
            Updated agent data
        """
        updates = {
            "name": agent_yaml.metadata.name,
            "description": agent_yaml.metadata.description,
            "instructions": agent_yaml.spec.instructions,
            "model": agent_yaml.spec.model,
            "temperature": agent_yaml.spec.temperature,
            "top_p": agent_yaml.spec.top_p,
            "response_format": agent_yaml.spec.response_format,
            "store_messages": agent_yaml.spec.store_messages,
            "file_output": agent_yaml.spec.file_output,
        }

        # Add optional fields
        if agent_yaml.spec.role:
            updates["role"] = agent_yaml.spec.role
        if agent_yaml.spec.goal:
            updates["goal"] = agent_yaml.spec.goal
        if agent_yaml.spec.context:
            updates["context"] = agent_yaml.spec.context
        if agent_yaml.spec.output:
            updates["output_format"] = agent_yaml.spec.output
        if agent_yaml.spec.examples:
            updates["examples"] = agent_yaml.spec.examples
        if agent_yaml.spec.usage:
            updates["usage_description"] = agent_yaml.spec.usage

        return self._update_agent(agent_id, updates)

    def _make_relative_path(self, base_dir: "Path", absolute_path: str) -> str:
        """Convert absolute path to relative path from base directory.

        Handles sibling directories by computing proper relative paths with '..'.
        For example:
            base_dir: /foo/blueprints/
            absolute_path: /foo/agents/worker.yaml
            result: ../agents/worker.yaml

        Args:
            base_dir: Base directory
            absolute_path: Absolute path to convert

        Returns:
            Relative path string (may include '..' for sibling directories)
        """
        import os
        from pathlib import Path

        # Use os.path.relpath which handles sibling directories correctly
        abs_path = Path(absolute_path).resolve()
        base_path = Path(base_dir).resolve()

        return os.path.relpath(abs_path, base_path)

    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------

    def _update_agent(self, agent_id: str, updates: dict) -> dict:
        """Update an agent while preserving managed_agents.

        Args:
            agent_id: Agent API ID
            updates: Fields to update

        Returns:
            Updated agent data
        """
        # MUST fetch current to preserve managed_agents
        current = self._agent_api.get(agent_id)

        # Merge updates while preserving critical fields
        payload = sanitize_for_update(current, updates)

        # Map config field names to API field names
        # IMPORTANT: Use correct API field names (not agent_persona_*)
        field_mapping = {
            "instructions": "agent_instructions",
            "role": "agent_role",
            "goal": "agent_goal",
            "context": "agent_context",
            "output_format": "agent_output",
            "usage_description": "tool_usage_description",
        }

        for config_key, api_key in field_mapping.items():
            if config_key in updates:
                payload[api_key] = updates[config_key]
                if config_key in payload:
                    del payload[config_key]

        # Ensure response_format is in correct API format (dict with "type" key)
        if "response_format" in payload:
            rf = payload["response_format"]
            if isinstance(rf, str):
                payload["response_format"] = {"type": rf}

        return self._agent_api.update(agent_id, payload)

    # -------------------------------------------------------------------------
    # Marketplace Operations
    # -------------------------------------------------------------------------

    def publish_to_marketplace(
        self,
        blueprint_id: str,
        name: str,
        description: str | None = None,
        creator: str | None = None,
        public: bool = True,
        welcome_message: str | None = None,
        industry: str | None = None,
        function: str | None = None,
        category: str | None = None,
    ) -> App:
        """Publish a blueprint's manager agent to the marketplace.

        This publishes the manager agent as a marketplace app, making it
        discoverable and usable by other users.

        Args:
            blueprint_id: Blueprint ID to publish
            name: App name (must be unique in marketplace)
            description: App description (defaults to blueprint description)
            creator: Creator name (defaults to "SDK")
            public: Whether app is publicly visible (default True)
            welcome_message: Welcome message shown when users open the app
            industry: Industry tag (e.g., "Banking & Financial Services")
            function: Function tag (e.g., "Marketing", "Sales")
            category: Category tag (e.g., "Productivity & Cost Savings")

        Returns:
            Created App object

        Raises:
            ValueError: If user_id not set in client
            APIError: If publishing fails (e.g., duplicate name)

        Example:
            ```python
            app = client.publish_to_marketplace(
                blueprint_id="bp-123",
                name="My HR Assistant",
                description="Automates HR workflows",
                industry="People & HR",
                function="HR",
                category="Productivity & Cost Savings",
            )
            print(f"Published: {app.marketplace_url}")
            ```
        """
        # Get blueprint to extract manager agent ID
        blueprint = self.get(blueprint_id)

        # Use blueprint description if not provided
        if description is None:
            bp_data = self._blueprint_api.get(blueprint_id)
            description = bp_data.get("description", "")

        # Publish to marketplace
        result = self.marketplace_api.create(
            name=name,
            agent_id=blueprint.manager_id,
            description=description,
            creator=creator,
            public=public,
            organization_id=self._organization_id,
            welcome_message=welcome_message,
            industry=industry,
            function=function,
            category=category,
        )

        return App.from_api_response(result)

    def get_marketplace_app(self, app_id: str) -> App:
        """Get a marketplace app by ID.

        Args:
            app_id: App ID

        Returns:
            App object
        """
        result = self.marketplace_api.get(app_id)
        return App.from_api_response(result)

    def list_marketplace_apps(self, user_id: str | None = None) -> list[App]:
        """List marketplace apps owned by a user.

        Args:
            user_id: User ID (defaults to client's user_id)

        Returns:
            List of App objects
        """
        results = self.marketplace_api.list_by_user(user_id)
        return [App.from_api_response(r) for r in results]

    def list_marketplace_apps_with_public(
        self,
        user_id: str | None = None,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None,
    ) -> tuple[list[App], dict]:
        """List user's apps plus public apps with pagination.

        Args:
            user_id: User ID (defaults to client's user_id)
            skip: Number of items to skip
            limit: Max items to return
            search: Search term for name/description

        Returns:
            Tuple of (apps list, pagination info dict)
        """
        result = self.marketplace_api.list_user_and_public(
            user_id=user_id,
            skip=skip,
            limit=limit,
            search=search,
        )

        apps = [App.from_api_response(r) for r in result.get("data", [])]
        pagination = {
            "total": result.get("total", len(apps)),
            "skip": result.get("skip", skip),
            "limit": result.get("limit", limit),
        }

        return apps, pagination

    def update_marketplace_app(
        self,
        app_id: str,
        name: str | None = None,
        description: str | None = None,
        public: bool | None = None,
        welcome_message: str | None = None,
        industry: str | None = None,
        function: str | None = None,
        category: str | None = None,
    ) -> App:
        """Update a marketplace app.

        Args:
            app_id: App ID to update
            name: New name
            description: New description
            public: New visibility
            welcome_message: New welcome message
            industry: Industry tag
            function: Function tag
            category: Category tag

        Returns:
            Updated App object
        """
        result = self.marketplace_api.update(
            app_id=app_id,
            name=name,
            description=description,
            public=public,
            welcome_message=welcome_message,
            industry=industry,
            function=function,
            category=category,
        )
        return App.from_api_response(result)

    def delete_marketplace_app(self, app_id: str) -> bool:
        """Delete a marketplace app.

        Args:
            app_id: App ID to delete

        Returns:
            True if deleted successfully
        """
        return self.marketplace_api.delete(app_id)

    def get_marketplace_leaderboard(self) -> list[App]:
        """Get top marketplace apps by upvotes.

        Returns:
            List of top 10 apps sorted by upvotes
        """
        results = self.marketplace_api.get_leaderboard()
        return [App.from_api_response(r) for r in results]
