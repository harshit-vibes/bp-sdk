"""Tree Structure Builder

Builds the ReactFlow tree structure for blueprint visualization.
Handles agent nodes and edges with proper positioning.

Supports:
- Flat manager/workers structure (original)
- Recursive sub_agents with deep nesting
- Multiple root agents
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..utils.sanitize import sanitize_agent_data

if TYPE_CHECKING:
    from ..models import AgentConfig

# Position constants
ROOT_Y = 0
LEVEL_SPACING = 300  # Vertical spacing between levels
HORIZONTAL_SPACING = 500


def calculate_worker_positions(num_workers: int) -> list[int]:
    """Calculate X positions for workers, centered around 0.

    Args:
        num_workers: Number of worker agents

    Returns:
        List of X positions
    """
    if num_workers == 0:
        return []
    if num_workers == 1:
        return [0]

    total_width = (num_workers - 1) * HORIZONTAL_SPACING
    start_x = -(total_width / 2)
    return [int(start_x + i * HORIZONTAL_SPACING) for i in range(num_workers)]


def build_agent_node(
    agent_id: str,
    agent_data: dict,
    position: dict[str, int],
    agent_role: str = "Worker",
) -> dict:
    """Build a ReactFlow node for an agent.

    Args:
        agent_id: Agent API ID
        agent_data: Full agent data from API
        position: Node position {x, y}
        agent_role: "Manager" or "Worker"

    Returns:
        ReactFlow node dict
    """
    # Sanitize agent data to prevent NoneType errors
    data = sanitize_agent_data(agent_data)

    return {
        "id": agent_id,
        "type": "agent",
        "position": position,
        "data": {
            # Full agent data embedded first (so we can override specific fields)
            **data,
            # ReactFlow required fields (override any from agent data)
            "label": data.get("name", "Agent"),
            "template_type": "MANAGER" if agent_role == "Manager" else "STANDARD",
            "tool": "",
            # Agent identification
            "agent_role": agent_role,
            "agent_id": agent_id,
        },
    }


def build_edge(
    source_id: str,
    target_id: str,
    usage_description: str | None = None,
) -> dict:
    """Build a ReactFlow edge with default bezier curve.

    Args:
        source_id: Source node ID
        target_id: Target node ID
        usage_description: Optional label for the edge (worker's usage description)

    Returns:
        ReactFlow edge dict (uses default bezier curve)
    """
    edge = {
        "id": f"edge-{source_id}-{target_id}",
        "source": source_id,
        "target": target_id,
        # No type specified = ReactFlow default bezier curve
    }
    if usage_description:
        edge["label"] = usage_description
        edge["data"] = {"usageDescription": usage_description}
    return edge


class TreeBuilder:
    """Builds ReactFlow tree structure for blueprints."""

    def build(
        self,
        manager_data: dict,
        workers_data: list[dict],
        manager_id: str,
        worker_ids: list[str],
    ) -> dict:
        """Build complete tree structure.

        Args:
            manager_data: Full manager agent data from API
            workers_data: List of full worker agent data from API
            manager_id: Manager agent API ID
            worker_ids: List of worker agent API IDs

        Returns:
            Dict with nodes, edges, agents, and tree_structure
        """
        nodes: list[dict] = []
        edges: list[dict] = []
        agents: dict[str, dict] = {}

        # Sanitize all agent data
        manager_data = sanitize_agent_data(manager_data)
        workers_data = [sanitize_agent_data(w) for w in workers_data]

        # Store in agents dict
        agents[manager_id] = manager_data
        for worker_id, worker_data in zip(worker_ids, workers_data):
            agents[worker_id] = worker_data

        # Build manager node
        manager_node = build_agent_node(
            agent_id=manager_id,
            agent_data=manager_data,
            position={"x": 0, "y": ROOT_Y},
            agent_role="Manager",
        )
        nodes.append(manager_node)

        # Calculate worker positions
        worker_x_positions = calculate_worker_positions(len(workers_data))

        # Build worker nodes and edges
        for i, (worker_id, worker_data) in enumerate(zip(worker_ids, workers_data)):
            worker_node = build_agent_node(
                agent_id=worker_id,
                agent_data=worker_data,
                position={"x": worker_x_positions[i], "y": LEVEL_SPACING},
                agent_role="Worker",
            )
            nodes.append(worker_node)

            # Edge from manager to worker with usage description as label
            usage_desc = worker_data.get("tool_usage_description")
            edges.append(build_edge(manager_id, worker_id, usage_desc))

        return {
            "manager_agent_id": manager_id,
            "agents": agents,
            "nodes": nodes,
            "edges": edges,
            "tree_structure": {
                "nodes": nodes,
                "edges": edges,
            },
        }

    def rebuild_from_blueprint(
        self,
        blueprint_data: dict,
        fresh_agents: dict[str, dict],
    ) -> dict:
        """Rebuild tree structure with fresh agent data.

        Used during updates to sync stale embedded agent data.

        Args:
            blueprint_data: Current blueprint_data from API
            fresh_agents: Dict of agent_id -> fresh agent data from Agent API

        Returns:
            Updated blueprint_data with fresh tree structure
        """
        manager_id = blueprint_data.get("manager_agent_id")
        if not manager_id:
            raise ValueError("No manager_agent_id in blueprint_data")

        # Get manager data
        manager_data = fresh_agents.get(manager_id)
        if not manager_data:
            raise ValueError(f"Manager {manager_id} not in fresh_agents")

        # Get worker IDs from managed_agents
        worker_ids = [
            ma["id"]
            for ma in manager_data.get("managed_agents", [])
            if ma.get("id") in fresh_agents
        ]

        # Get worker data
        workers_data = [fresh_agents[wid] for wid in worker_ids]

        # Build fresh tree
        tree = self.build(
            manager_data=manager_data,
            workers_data=workers_data,
            manager_id=manager_id,
            worker_ids=worker_ids,
        )

        # Update blueprint_data
        result = blueprint_data.copy()
        result["agents"] = tree["agents"]
        result["nodes"] = tree["nodes"]
        result["edges"] = tree["edges"]
        result["tree_structure"] = tree["tree_structure"]

        return result

    def build_recursive(
        self,
        root_agents: list[tuple[str, dict[str, Any]]],
        agent_hierarchy: dict[str, list[tuple[str, dict[str, Any]]]],
    ) -> dict:
        """Build tree structure with recursive sub_agents support.

        Supports:
        - Multiple root agents
        - Deep nesting via sub_agents
        - Automatic circular dependency detection

        Args:
            root_agents: List of (agent_id, agent_data) tuples for root agents
            agent_hierarchy: Dict mapping parent_id -> list of (child_id, child_data) tuples

        Returns:
            Dict with nodes, edges, agents, and tree_structure

        Raises:
            ValueError: If circular dependency detected
        """
        nodes: list[dict] = []
        edges: list[dict] = []
        agents: dict[str, dict] = {}
        visited: set[str] = set()

        def process_agent(
            agent_id: str,
            agent_data: dict,
            level: int,
            x_offset: int,
            parent_id: str | None = None,
            path: list[str] | None = None,
        ) -> int:
            """Process an agent and its sub-agents recursively.

            Args:
                agent_id: Agent ID
                agent_data: Agent data dict
                level: Current tree level (0 = root)
                x_offset: X position offset for this subtree
                parent_id: Parent agent ID (for edge creation)
                path: Current path for circular dependency detection

            Returns:
                Width of this subtree (for sibling positioning)
            """
            if path is None:
                path = []

            # Check for circular dependency
            if agent_id in path:
                cycle = " -> ".join(path + [agent_id])
                raise ValueError(f"Circular dependency detected: {cycle}")

            # Skip if already processed (but not an error - can have multiple parents)
            if agent_id in visited:
                # Just add the edge if there's a parent
                if parent_id:
                    usage_desc = agent_data.get("tool_usage_description")
                    edges.append(build_edge(parent_id, agent_id, usage_desc))
                return 0

            visited.add(agent_id)
            current_path = path + [agent_id]

            # Sanitize and store agent data
            sanitized = sanitize_agent_data(agent_data)
            agents[agent_id] = sanitized

            # Determine agent role
            is_root = level == 0
            has_children = agent_id in agent_hierarchy and len(agent_hierarchy[agent_id]) > 0
            agent_role = "Manager" if (is_root or has_children) else "Worker"

            # Get children
            children = agent_hierarchy.get(agent_id, [])

            # Calculate subtree width
            if not children:
                subtree_width = HORIZONTAL_SPACING
            else:
                subtree_width = 0
                child_widths = []
                for child_id, child_data in children:
                    # Recursively calculate child widths
                    child_w = self._calculate_subtree_width(
                        child_id, agent_hierarchy, set(current_path)
                    )
                    child_widths.append(child_w)
                    subtree_width += child_w
                subtree_width = max(subtree_width, HORIZONTAL_SPACING)

            # Create node at center of subtree
            node_x = x_offset + subtree_width // 2
            node = build_agent_node(
                agent_id=agent_id,
                agent_data=sanitized,
                position={"x": node_x, "y": level * LEVEL_SPACING},
                agent_role=agent_role,
            )
            nodes.append(node)

            # Create edge from parent
            if parent_id:
                usage_desc = sanitized.get("tool_usage_description")
                edges.append(build_edge(parent_id, agent_id, usage_desc))

            # Process children
            child_x = x_offset
            for child_id, child_data in children:
                child_width = process_agent(
                    agent_id=child_id,
                    agent_data=child_data,
                    level=level + 1,
                    x_offset=child_x,
                    parent_id=agent_id,
                    path=current_path,
                )
                child_x += max(child_width, HORIZONTAL_SPACING)

            return subtree_width

        # Process all root agents
        x_offset = 0
        for agent_id, agent_data in root_agents:
            width = process_agent(
                agent_id=agent_id,
                agent_data=agent_data,
                level=0,
                x_offset=x_offset,
            )
            x_offset += max(width, HORIZONTAL_SPACING)

        # Determine manager_agent_id (first root, for backward compatibility)
        manager_id = root_agents[0][0] if root_agents else None

        return {
            "manager_agent_id": manager_id,
            "agents": agents,
            "nodes": nodes,
            "edges": edges,
            "tree_structure": {
                "nodes": nodes,
                "edges": edges,
            },
        }

    def _calculate_subtree_width(
        self,
        agent_id: str,
        agent_hierarchy: dict[str, list[tuple[str, dict[str, Any]]]],
        visited: set[str],
    ) -> int:
        """Calculate the width of a subtree for positioning.

        Args:
            agent_id: Root of subtree
            agent_hierarchy: Full hierarchy map
            visited: Already visited nodes (for cycle detection)

        Returns:
            Width in pixels
        """
        if agent_id in visited:
            return 0

        children = agent_hierarchy.get(agent_id, [])
        if not children:
            return HORIZONTAL_SPACING

        total_width = 0
        new_visited = visited | {agent_id}
        for child_id, _ in children:
            total_width += self._calculate_subtree_width(
                child_id, agent_hierarchy, new_visited
            )

        return max(total_width, HORIZONTAL_SPACING)
