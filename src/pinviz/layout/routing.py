"""Wire routing logic for diagram connections."""

import logging
import math
import time

from ..model import DEFAULT_COLORS, Diagram, Point, WireStyle
from .types import LayoutConfig, LayoutConstants, RoutedWire, WireData

logger = logging.getLogger(__name__)


class WireDataCollector:
    """Collects and groups wire data from diagram connections."""

    def __init__(
        self, board_margin_left: float, board_margin_top: float, constants: LayoutConstants
    ):
        self.board_margin_left = board_margin_left
        self.board_margin_top = board_margin_top
        self.constants = constants

    def collect(self, diagram: Diagram) -> list[WireData]:
        """Collect wire connection data from the diagram.

        Resolves absolute pin positions for both board-to-device and
        device-to-device connections.
        """
        wire_data: list[WireData] = []
        device_by_name = {device.name: device for device in diagram.devices}

        for conn in diagram.connections:
            is_device_to_device = conn.source_device is not None
            target_device = device_by_name.get(conn.device_name)
            if not target_device:
                continue
            target_pin = target_device.get_pin_by_name(conn.device_pin_name)
            if not target_pin:
                continue

            if is_device_to_device:
                source_device = device_by_name.get(conn.source_device)
                if not source_device:
                    continue
                source_pin = source_device.get_pin_by_name(conn.source_pin)
                if not source_pin:
                    continue

                from_pos = Point(
                    source_device.position.x + source_pin.position.x,
                    source_device.position.y + source_pin.position.y,
                )
                to_pos = Point(
                    target_device.position.x + target_pin.position.x,
                    target_device.position.y + target_pin.position.y,
                )
                is_source_right_side = source_pin.position.x > (source_device.width / 2)
                is_target_right_side = target_pin.position.x > (target_device.width / 2)

                if conn.color:
                    color = conn.color.value if hasattr(conn.color, "value") else conn.color
                else:
                    color = DEFAULT_COLORS.get(source_pin.role, "#808080")

                wire_data.append(
                    WireData(
                        conn,
                        from_pos,
                        to_pos,
                        color,
                        target_device,
                        source_device,
                        is_source_right_side,
                        is_target_right_side,
                    )
                )
            else:
                board_pin = diagram.board.get_pin_by_number(conn.board_pin)
                if not board_pin or not board_pin.position:
                    continue

                from_pos = Point(
                    self.board_margin_left + board_pin.position.x,
                    self.board_margin_top + board_pin.position.y,
                )
                to_pos = Point(
                    target_device.position.x + target_pin.position.x,
                    target_device.position.y + target_pin.position.y,
                )
                is_target_right_side = target_pin.position.x > (target_device.width / 2)

                if conn.color:
                    color = conn.color.value if hasattr(conn.color, "value") else conn.color
                else:
                    color = DEFAULT_COLORS.get(board_pin.role, "#808080")

                wire_data.append(
                    WireData(
                        conn,
                        from_pos,
                        to_pos,
                        color,
                        target_device,
                        None,
                        False,
                        is_target_right_side,
                    )
                )

        return wire_data

    def group_by_position(self, wire_data: list[WireData]) -> dict[int, list[int]]:
        """Group wires by starting Y position for vertical offset calculation."""
        y_tolerance = self.constants.Y_POSITION_TOLERANCE
        y_groups: dict[int, list[int]] = {}

        for idx, wire in enumerate(wire_data):
            group_id = None
            for gid, wire_indices in y_groups.items():
                first_wire_y = wire_data[wire_indices[0]].from_pos.y
                if abs(wire.from_pos.y - first_wire_y) < y_tolerance:
                    group_id = gid
                    break

            if group_id is None:
                group_id = len(y_groups)
                y_groups[group_id] = []

            y_groups[group_id].append(idx)

        return y_groups


class RailAssigner:
    """Assigns vertical rail positions to devices for wire routing."""

    def __init__(self, config: LayoutConfig, constants: LayoutConstants, board_margin_left: float):
        self.config = config
        self.constants = constants
        self.board_margin_left = board_margin_left

    def assign(
        self,
        wire_data: list[WireData],
        board_width: float,
        y_groups: dict[int, list[int]],
    ) -> list[dict]:
        """Assign rail positions and calculate initial wire paths.

        Returns list of wire info dicts with rail_x, y_offset, and positions.
        """
        device_to_base_rail, wire_count_per_device = self._assign_rail_positions(
            wire_data, board_width
        )
        return self._calculate_initial_wire_paths(
            wire_data, y_groups, device_to_base_rail, wire_count_per_device
        )

    def _assign_rail_positions(
        self, wire_data: list[WireData], board_width: float
    ) -> tuple[dict[str, float], dict[str, int]]:
        """Assign rail X positions for each device to prevent wire crossings."""
        board_right_edge = self.board_margin_left + board_width
        base_rail_x = board_right_edge + self.config.rail_offset

        unique_devices = []
        seen_devices: set[str] = set()
        for wire in wire_data:
            if wire.device.name not in seen_devices:
                unique_devices.append(wire.device)
                seen_devices.add(wire.device.name)

        device_to_base_rail: dict[str, float] = {}
        for idx, device in enumerate(unique_devices):
            device_to_base_rail[device.name] = base_rail_x + (
                idx * self.config.wire_spacing * self.constants.RAIL_SPACING_MULTIPLIER
            )

        wire_count_per_device: dict[str, int] = {}
        for wire in wire_data:
            wire_count_per_device[wire.device.name] = (
                wire_count_per_device.get(wire.device.name, 0) + 1
            )

        return device_to_base_rail, wire_count_per_device

    def _calculate_initial_wire_paths(
        self,
        wire_data: list[WireData],
        y_groups: dict[int, list[int]],
        device_to_base_rail: dict[str, float],
        wire_count_per_device: dict[str, int],
    ) -> list[dict]:
        """Calculate initial wire paths with rail positions and vertical offsets."""
        wire_index_per_device: dict[str, int] = {}
        initial_wires = []

        for wire_idx, wire in enumerate(wire_data):
            base_rail = device_to_base_rail[wire.device.name]
            dev_wire_idx = wire_index_per_device.get(wire.device.name, 0)
            wire_index_per_device[wire.device.name] = dev_wire_idx + 1

            num_wires = wire_count_per_device[wire.device.name]
            if num_wires > 1:
                spread = (num_wires - 1) * self.config.wire_spacing / 2
                offset = dev_wire_idx * self.config.wire_spacing - spread
            else:
                offset = 0

            rail_x = base_rail + offset

            y_offset = 0.0
            for _group_id, group_indices in y_groups.items():
                if wire_idx in group_indices:
                    pos_in_group = group_indices.index(wire_idx)
                    num_in_group = len(group_indices)
                    if num_in_group > 1:
                        vertical_spacing = (
                            self.config.wire_spacing * self.constants.VERTICAL_SPACING_MULTIPLIER
                        )
                        spread = (num_in_group - 1) * vertical_spacing / 2
                        y_offset = pos_in_group * vertical_spacing - spread
                    break

            initial_wires.append(
                {
                    "conn": wire.connection,
                    "from_pos": wire.from_pos,
                    "to_pos": wire.to_pos,
                    "color": wire.color,
                    "device": wire.device,
                    "rail_x": rail_x,
                    "y_offset": y_offset,
                    "wire_idx": wire_idx,
                    "source_device": wire.source_device,
                    "is_source_right_side": wire.is_source_right_side,
                    "is_target_right_side": wire.is_target_right_side,
                }
            )

        return initial_wires


class PathGenerator:
    """Generates Bezier curve paths for wire routing."""

    def __init__(self, constants: LayoutConstants):
        self.constants = constants

    def generate(
        self, initial_wires: list[dict], y_offset_adjustments: dict[int, float]
    ) -> list[RoutedWire]:
        """Generate final routed wires with all adjustments applied."""
        routed_wires: list[RoutedWire] = []

        for wire_info in initial_wires:
            adjustment = y_offset_adjustments.get(wire_info["wire_idx"], 0.0)
            final_y_offset = wire_info["y_offset"] + adjustment

            path_points = self.calculate_path(
                wire_info["from_pos"],
                wire_info["to_pos"],
                wire_info["rail_x"],
                final_y_offset,
                wire_info["conn"].style,
                wire_info["is_source_right_side"],
                wire_info["is_target_right_side"],
            )

            routed_wires.append(
                RoutedWire(
                    connection=wire_info["conn"],
                    path_points=path_points,
                    color=wire_info["color"],
                    from_pin_pos=wire_info["from_pos"],
                    to_pin_pos=wire_info["to_pos"],
                )
            )

        return routed_wires

    def calculate_path(
        self,
        from_pos: Point,
        to_pos: Point,
        rail_x: float,
        y_offset: float,
        style: WireStyle,
        is_source_right_side: bool = False,
        is_target_right_side: bool = False,
    ) -> list[Point]:
        """Calculate wire path selecting the appropriate curve type."""
        connection_point, extended_end = self._connection_points(to_pos, is_target_right_side)

        if is_source_right_side:
            from_pos = Point(from_pos.x + self.constants.WIRE_PIN_EXTENSION, from_pos.y)
            if to_pos.x > from_pos.x:
                return self._right_to_right_path(from_pos, connection_point, extended_end, y_offset)

        dy = to_pos.y - from_pos.y

        if abs(dy) < self.constants.SIMILAR_Y_THRESHOLD:
            return self._gentle_arc_path(from_pos, rail_x, y_offset, connection_point, extended_end)
        else:
            return self._s_curve_path(from_pos, rail_x, y_offset, connection_point, extended_end)

    def _connection_points(self, to_pos: Point, is_right_side: bool = False) -> tuple[Point, Point]:
        """Calculate connection and extended end points for wire routing."""
        if is_right_side:
            connection_point = Point(to_pos.x + self.constants.STRAIGHT_SEGMENT_LENGTH, to_pos.y)
            extended_end = Point(to_pos.x - self.constants.WIRE_PIN_EXTENSION, to_pos.y)
        else:
            connection_point = Point(to_pos.x - self.constants.STRAIGHT_SEGMENT_LENGTH, to_pos.y)
            extended_end = Point(to_pos.x + self.constants.WIRE_PIN_EXTENSION, to_pos.y)
        return connection_point, extended_end

    def _gentle_arc_path(
        self,
        from_pos: Point,
        rail_x: float,
        y_offset: float,
        connection_point: Point,
        extended_end: Point,
    ) -> list[Point]:
        """Gentle horizontal arc path for wires with similar Y positions."""
        ctrl1 = Point(
            rail_x * self.constants.GENTLE_ARC_CTRL1_RAIL_RATIO
            + from_pos.x * self.constants.GENTLE_ARC_CTRL1_START_RATIO,
            from_pos.y + y_offset * self.constants.GENTLE_ARC_CTRL1_OFFSET_RATIO,
        )
        ctrl2_x = (
            rail_x * self.constants.GENTLE_ARC_CTRL2_RAIL_RATIO
            + connection_point.x * self.constants.GENTLE_ARC_CTRL2_END_RATIO
        )
        ctrl2_y = connection_point.y + y_offset * self.constants.GENTLE_ARC_CTRL2_OFFSET_RATIO
        ctrl2 = Point(ctrl2_x, ctrl2_y)
        return [from_pos, ctrl1, ctrl2, connection_point, extended_end]

    def _s_curve_path(
        self,
        from_pos: Point,
        rail_x: float,
        y_offset: float,
        connection_point: Point,
        extended_end: Point,
    ) -> list[Point]:
        """Smooth S-curve path for wires with vertical separation."""
        ctrl1_x = from_pos.x + (rail_x - from_pos.x) * self.constants.S_CURVE_CTRL1_RATIO
        ctrl1_y = from_pos.y + y_offset * self.constants.S_CURVE_CTRL1_OFFSET_RATIO
        ctrl2_x = (
            connection_point.x + (rail_x - connection_point.x) * self.constants.S_CURVE_CTRL2_RATIO
        )
        ctrl2_y = connection_point.y + y_offset * self.constants.S_CURVE_CTRL2_OFFSET_RATIO

        return [
            from_pos,
            Point(ctrl1_x, ctrl1_y),
            Point(ctrl2_x, ctrl2_y),
            connection_point,
            extended_end,
        ]

    def _right_to_right_path(
        self,
        from_pos: Point,
        connection_point: Point,
        extended_end: Point,
        y_offset: float,
    ) -> list[Point]:
        """Wire path for right-side output to another device."""
        dy = connection_point.y - from_pos.y
        dx = connection_point.x - from_pos.x

        if abs(dy) < self.constants.SIMILAR_Y_THRESHOLD:
            mid_x = from_pos.x + dx * 0.5
            ctrl1 = Point(mid_x, from_pos.y + y_offset * 0.3)
            ctrl2 = Point(mid_x, connection_point.y + y_offset * 0.3)
        else:
            ctrl1_x = from_pos.x + dx * 0.3
            ctrl1_y = from_pos.y + y_offset * 0.5
            ctrl2_x = from_pos.x + dx * 0.7
            ctrl2_y = connection_point.y + y_offset * 0.5
            ctrl1 = Point(ctrl1_x, ctrl1_y)
            ctrl2 = Point(ctrl2_x, ctrl2_y)

        return [from_pos, ctrl1, ctrl2, connection_point, extended_end]


class OverlapResolver:
    """Detects and resolves overlapping wire paths."""

    def __init__(self, config: LayoutConfig, constants: LayoutConstants):
        self.config = config
        self.constants = constants

    def resolve(self, wires: list[dict], path_generator: PathGenerator) -> dict[int, float]:
        """Detect overlapping wire paths and return offset adjustments."""
        start_time = time.perf_counter()
        adjustments: dict[int, float] = {}
        min_separation = self.config.wire_spacing * self.constants.MIN_SEPARATION_MULTIPLIER

        total_wire_pairs = 0
        bbox_rejections = 0
        distance_checks = 0

        wire_samples = []
        for wire in wires:
            path_points = path_generator.calculate_path(
                wire["from_pos"],
                wire["to_pos"],
                wire["rail_x"],
                wire["y_offset"],
                wire["conn"].style,
                wire["is_source_right_side"],
                wire["is_target_right_side"],
            )

            samples = []
            min_x = float("inf")
            max_x = float("-inf")
            min_y = float("inf")
            max_y = float("-inf")

            for i in range(len(path_points) - 1):
                p1, p2 = path_points[i], path_points[i + 1]
                for t in self.constants.SAMPLE_POSITIONS:
                    x = p1.x + (p2.x - p1.x) * t
                    y = p1.y + (p2.y - p1.y) * t
                    samples.append((x, y))
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)

            wire_samples.append(
                {
                    "wire_idx": wire["wire_idx"],
                    "samples": samples,
                    "from_y": wire["from_pos"].y,
                    "bbox": (min_x, max_x, min_y, max_y),
                }
            )

        conflicts = []
        for i in range(len(wire_samples)):
            for j in range(i + 1, len(wire_samples)):
                total_wire_pairs += 1
                wire_a = wire_samples[i]
                wire_b = wire_samples[j]

                if (
                    abs(wire_a["from_y"] - wire_b["from_y"])
                    > self.constants.FROM_Y_POSITION_TOLERANCE
                ):
                    bbox_rejections += 1
                    continue

                bbox_a = wire_a["bbox"]
                bbox_b = wire_b["bbox"]
                bbox_margin = min_separation

                if (
                    bbox_a[1] + bbox_margin < bbox_b[0]
                    or bbox_b[1] + bbox_margin < bbox_a[0]
                    or bbox_a[3] + bbox_margin < bbox_b[2]
                    or bbox_b[3] + bbox_margin < bbox_a[2]
                ):
                    bbox_rejections += 1
                    continue

                distance_checks += 1

                min_dist = float("inf")
                found_conflict = False
                for pa in wire_a["samples"]:
                    for pb in wire_b["samples"]:
                        dist = math.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
                        if dist < min_separation:
                            min_dist = dist
                            found_conflict = True
                            break
                        min_dist = min(min_dist, dist)
                    if found_conflict:
                        break

                if min_dist < min_separation:
                    conflicts.append(
                        {
                            "wire_a": wire_a["wire_idx"],
                            "wire_b": wire_b["wire_idx"],
                            "severity": min_separation - min_dist,
                        }
                    )

        for conflict in sorted(conflicts, key=lambda c: c["severity"], reverse=True):
            adjustment_amount = conflict["severity"] / self.constants.CONFLICT_ADJUSTMENT_DIVISOR
            wire_a_idx = conflict["wire_a"]
            wire_b_idx = conflict["wire_b"]

            current_a = adjustments.get(wire_a_idx, 0.0)
            current_b = adjustments.get(wire_b_idx, 0.0)

            adjustments[wire_a_idx] = max(
                -self.constants.MAX_ADJUSTMENT,
                min(self.constants.MAX_ADJUSTMENT, current_a - adjustment_amount),
            )
            adjustments[wire_b_idx] = max(
                -self.constants.MAX_ADJUSTMENT,
                min(self.constants.MAX_ADJUSTMENT, current_b + adjustment_amount),
            )

        elapsed_time = time.perf_counter() - start_time
        if total_wire_pairs > 0:
            rejection_rate = (bbox_rejections / total_wire_pairs) * 100
            logger.debug(
                f"Wire conflict detection: {len(wires)} wires, "
                f"{total_wire_pairs} pairs checked, "
                f"{bbox_rejections} rejected ({rejection_rate:.1f}%), "
                f"{distance_checks} distance checks, "
                f"{len(conflicts)} conflicts found in {elapsed_time * 1000:.1f}ms"
            )

        return adjustments


class WireRouter:
    """
    Routes wires between board pins and device pins.

    Thin orchestrator that delegates to internal components:
    - WireDataCollector: resolves pin positions from diagram
    - RailAssigner: assigns routing rails to prevent crossings
    - OverlapResolver: detects and resolves wire conflicts
    - PathGenerator: generates Bezier curve paths
    """

    def __init__(self, config: LayoutConfig, board_margin_left: float, board_margin_top: float):
        self.config = config
        self.constants = LayoutConstants()
        self.board_margin_left = board_margin_left
        self.board_margin_top = board_margin_top

    def route_wires(self, diagram: Diagram) -> list[RoutedWire]:
        """Route all wires using device-based routing lanes."""
        collector = WireDataCollector(self.board_margin_left, self.board_margin_top, self.constants)
        wire_data = collector.collect(diagram)
        wire_data.sort(key=lambda w: (w.from_pos.y, w.device.position.y, w.to_pos.y))
        y_groups = collector.group_by_position(wire_data)

        assigner = RailAssigner(self.config, self.constants, self.board_margin_left)
        initial_wires = assigner.assign(wire_data, diagram.board.width, y_groups)

        path_gen = PathGenerator(self.constants)
        resolver = OverlapResolver(self.config, self.constants)
        adjustments = resolver.resolve(initial_wires, path_gen)

        return path_gen.generate(initial_wires, adjustments)
