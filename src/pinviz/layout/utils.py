"""Utility functions for layout calculations."""

from ..model import Point


def create_bezier_path(points: list[Point], corner_radius: float = 5.0) -> str:
    """
    Create an SVG path string with smooth Bezier curves.

    Creates organic, flowing curves through the points using cubic Bezier curves,
    similar to the classic Fritzing diagram style.

    Args:
        points: List of points defining the path (including control points)
        corner_radius: Not used, kept for API compatibility

    Returns:
        SVG path d attribute string with smooth curves
    """
    if len(points) < 2:
        return ""

    # Start at first point
    path_parts = [f"M {points[0].x:.2f},{points[0].y:.2f}"]

    if len(points) == 2:
        # Simple line
        path_parts.append(f"L {points[1].x:.2f},{points[1].y:.2f}")
    elif len(points) == 3:
        # Quadratic Bezier through middle point
        path_parts.append(
            f"Q {points[1].x:.2f},{points[1].y:.2f} {points[2].x:.2f},{points[2].y:.2f}"
        )
    elif len(points) == 4:
        # Smooth cubic Bezier using middle two points as control points
        path_parts.append(
            f"C {points[1].x:.2f},{points[1].y:.2f} "
            f"{points[2].x:.2f},{points[2].y:.2f} "
            f"{points[3].x:.2f},{points[3].y:.2f}"
        )
    elif len(points) == 5:
        # Cubic Bezier curve followed by straight line into pin
        # This ensures the wire visually connects directly into the device pin
        # points[0] = start, points[1] = ctrl1, points[2] = ctrl2
        # points[3] = connection point, points[4] = pin center

        # Smooth cubic Bezier using middle two points as control points
        path_parts.append(
            f"C {points[1].x:.2f},{points[1].y:.2f} "
            f"{points[2].x:.2f},{points[2].y:.2f} "
            f"{points[3].x:.2f},{points[3].y:.2f}"
        )

        # Straight line segment into the pin for clear visual connection
        path_parts.append(f"L {points[4].x:.2f},{points[4].y:.2f}")
    else:
        # Many points - create smooth curve through all
        for i in range(1, len(points)):
            if i == len(points) - 1:
                # Last segment - simple curve
                prev = points[i - 1]
                curr = points[i]
                # Create smooth approach to final point
                cx = prev.x + (curr.x - prev.x) * 0.5
                path_parts.append(f"Q {cx:.2f},{curr.y:.2f} {curr.x:.2f},{curr.y:.2f}")
            else:
                # Use current point as control, next as target
                curr = points[i]
                next_pt = points[i + 1]
                path_parts.append(f"Q {curr.x:.2f},{curr.y:.2f} {next_pt.x:.2f},{next_pt.y:.2f}")
                i += 1  # Skip next point since we used it

    return " ".join(path_parts)
