"""Graph utilities for analyzing device connection topology.

This module provides the ConnectionGraph class for analyzing the topology of
device connections in a PinViz diagram. It supports:
- Hierarchical level assignment for multi-tier layouts
- Cycle detection to prevent invalid configurations
- Dependency analysis for devices

The graph represents connections between the board and devices, and between
devices themselves. The board is treated as a special node at level -1.
"""

from __future__ import annotations

from collections import defaultdict, deque

from .model import Connection, Device


class ConnectionGraph:
    """
    A directed graph representing device connections for topology analysis.

    The graph has the following structure:
    - Nodes: "board" (special node) + device names
    - Edges: directed edges from source to destination based on connections
    - Board is at level -1 (root of the hierarchy)
    - Devices directly connected to board are at level 0
    - Device-to-device connections create edges in the graph

    Attributes:
        devices: List of Device objects in the diagram
        connections: List of Connection objects in the diagram
        adjacency_list: Directed graph mapping source -> list of targets
        device_levels: Computed hierarchical levels for each device

    Examples:
        >>> devices = [Device("Sensor", [...]), Device("Display", [...])]
        >>> connections = [
        ...     Connection(board_pin=1, device_name="Sensor", device_pin_name="VCC"),
        ...     Connection(source_device="Sensor", source_pin="OUT",
        ...                device_name="Display", device_pin_name="IN")
        ... ]
        >>> graph = ConnectionGraph(devices, connections)
        >>> graph.calculate_device_levels()
        >>> print(graph.device_levels)
        {'Sensor': 0, 'Display': 1}
    """

    def __init__(self, devices: list[Device], connections: list[Connection]) -> None:
        """
        Initialize the connection graph.

        Args:
            devices: List of Device objects in the diagram
            connections: List of Connection objects in the diagram
        """
        self.devices = devices
        self.connections = connections
        self.adjacency_list: dict[str, list[str]] = {}
        self.device_levels: dict[str, int] = {}

        # Build the graph structure
        self.build_adjacency_list()

    def build_adjacency_list(self) -> dict[str, list[str]]:
        """
        Build a directed adjacency list from connections.

        Creates a mapping of source node -> list of target nodes.
        Board connections create edges from "board" to device.
        Device-to-device connections create edges from source device to target device.

        Returns:
            Dictionary mapping source node names to lists of target node names.

        Examples:
            >>> # For connections: board->A, A->B, board->C
            >>> graph.build_adjacency_list()
            {'board': ['A', 'C'], 'A': ['B']}
        """
        adjacency: dict[str, list[str]] = defaultdict(list)

        for conn in self.connections:
            if conn.is_board_connection():
                # Board-to-device connection
                source = "board"
                target = conn.device_name
                # device_name is guaranteed non-None by Connection.__post_init__
                assert target is not None
            else:
                # Device-to-device connection
                # source_device and device_name are guaranteed non-None by Connection.__post_init__
                assert conn.source_device is not None
                assert conn.device_name is not None
                source = conn.source_device
                target = conn.device_name

            # Add edge from source to target (avoid duplicates)
            if target not in adjacency[source]:
                adjacency[source].append(target)

        self.adjacency_list = dict(adjacency)
        return self.adjacency_list

    def detect_cycles(self) -> list[list[str]]:
        """
        Detect all cycles in the connection graph using DFS.

        Uses depth-first search to find cycles. Returns all cycles found,
        including self-loops (device connected to itself).

        Returns:
            List of cycles, where each cycle is a list of node names forming
            the cycle path. Empty list if graph is acyclic.

        Examples:
            >>> # For A->B->C->A cycle
            >>> cycles = graph.detect_cycles()
            >>> print(cycles)
            [['A', 'B', 'C', 'A']]
            >>>
            >>> # For self-loop A->A
            >>> cycles = graph.detect_cycles()
            >>> print(cycles)
            [['A', 'A']]
        """
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            """DFS helper to detect cycles."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Visit all neighbors
            for neighbor in self.adjacency_list.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found a cycle - extract the cycle path
                    cycle_start_idx = path.index(neighbor)
                    cycle = path[cycle_start_idx:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        # Check all nodes (including those not reachable from board)
        all_nodes = set(self.adjacency_list.keys())
        for device in self.devices:
            all_nodes.add(device.name)

        for node in all_nodes:
            if node not in visited:
                dfs(node)

        return cycles

    def is_acyclic(self) -> bool:
        """
        Quick check if the graph has no cycles.

        Returns:
            True if graph is acyclic (no cycles), False otherwise.

        Examples:
            >>> # For linear chain A->B->C
            >>> graph.is_acyclic()
            True
            >>> # For cycle A->B->A
            >>> graph.is_acyclic()
            False
        """
        return len(self.detect_cycles()) == 0

    def calculate_device_levels(self) -> dict[str, int]:
        """
        Calculate hierarchical levels for all devices using BFS.

        Assigns a level to each device based on its position in the connection
        hierarchy:
        - Board is at level -1 (implicit, not in the result)
        - Devices directly connected to board are at level 0
        - For device-to-device connections: level = max(dependency levels) + 1

        This handles diamond patterns correctly: if a device has multiple
        incoming connections, it's placed at one level below its furthest
        ancestor.

        Returns:
            Dictionary mapping device names to their hierarchical levels.

        Raises:
            ValueError: If the graph contains cycles (must be acyclic).

        Examples:
            >>> # Linear chain: board->A->B->C
            >>> levels = graph.calculate_device_levels()
            >>> print(levels)
            {'A': 0, 'B': 1, 'C': 2}
            >>>
            >>> # Diamond: board->A, board->B, A->C, B->C
            >>> levels = graph.calculate_device_levels()
            >>> print(levels)
            {'A': 0, 'B': 0, 'C': 1}
        """
        if not self.is_acyclic():
            raise ValueError("Cannot calculate levels: graph contains cycles")

        levels: dict[str, int] = {}
        queue: deque[tuple[str, int]] = deque()

        # Start BFS from the board (level -1)
        # Add all board-connected devices to queue at level 0
        for device in self.adjacency_list.get("board", []):
            queue.append((device, 0))
            levels[device] = 0

        # BFS to calculate levels
        while queue:
            current_device, current_level = queue.popleft()

            # Process all devices connected from this device
            for target_device in self.adjacency_list.get(current_device, []):
                new_level = current_level + 1

                # Handle diamond patterns: use maximum level
                if target_device in levels:
                    levels[target_device] = max(levels[target_device], new_level)
                else:
                    levels[target_device] = new_level

                # Add to queue if not already processed at this level
                queue.append((target_device, new_level))

        # Store calculated levels
        self.device_levels = levels
        return levels

    def get_device_dependencies(self, device_name: str) -> list[str]:
        """
        Get all devices that the specified device depends on (upstream).

        Returns all devices that have direct connections TO the specified device.
        This includes both board (if board-connected) and other devices.

        Args:
            device_name: Name of the device to query

        Returns:
            List of device names that connect to the specified device.
            Includes "board" if the device has board connections.

        Examples:
            >>> # For connections: board->A, B->A
            >>> graph.get_device_dependencies("A")
            ['board', 'B']
        """
        dependencies: list[str] = []

        # Check all nodes in adjacency list
        for source, targets in self.adjacency_list.items():
            if device_name in targets:
                dependencies.append(source)

        return dependencies

    def get_device_dependents(self, device_name: str) -> list[str]:
        """
        Get all devices that depend on the specified device (downstream).

        Returns all devices that the specified device connects TO.

        Args:
            device_name: Name of the device to query

        Returns:
            List of device names that the specified device connects to.

        Examples:
            >>> # For connections: A->B, A->C
            >>> graph.get_device_dependents("A")
            ['B', 'C']
        """
        return self.adjacency_list.get(device_name, []).copy()

    def get_root_devices(self) -> list[str]:
        """
        Get all devices directly connected to the board (level 0 devices).

        Returns:
            List of device names that have board connections.

        Examples:
            >>> # For connections: board->A, board->B, A->C
            >>> graph.get_root_devices()
            ['A', 'B']
        """
        return self.adjacency_list.get("board", []).copy()

    def get_leaf_devices(self) -> list[str]:
        """
        Get all devices with no outgoing connections (leaf nodes).

        Returns:
            List of device names that don't connect to any other devices.

        Examples:
            >>> # For connections: A->B, C->D, B and D are leaves
            >>> graph.get_leaf_devices()
            ['B', 'D']
        """
        # Collect all devices that appear as targets
        all_devices = {device.name for device in self.devices}

        # Collect all devices that have outgoing connections
        devices_with_outgoing = set(self.adjacency_list.keys()) - {"board"}

        # Leaf devices are those with no outgoing connections
        leaf_devices = all_devices - devices_with_outgoing

        return sorted(leaf_devices)
