"""User-friendly error formatting for validation and configuration errors.

This module provides utilities to format error messages with examples and actionable
fixes, making it easier for users to diagnose and resolve issues without consulting
documentation.
"""


def format_validation_error(
    message: str,
    example: str | None = None,
    fix: str | None = None,
) -> str:
    """
    Format a user-friendly validation error with examples and fixes.

    Errors are kept concise (<5 lines when possible) and include:
    - Clear problem description
    - Example of correct usage (optional)
    - Actionable fix suggestion (optional)

    Args:
        message: Brief description of the error
        example: Example of correct usage (optional)
        fix: Suggestion for how to fix the issue (optional)

    Returns:
        Formatted error message string

    Examples:
        >>> err = format_validation_error(
        ...     "Connection must have exactly one source",
        ...     example="board_pin: 1, device: 'LED', device_pin: 'VCC'",
        ...     fix="Remove either board_pin or source_device/source_pin"
        ... )
        >>> print(err)
        Connection must have exactly one source
        <BLANKLINE>
        Example: board_pin: 1, device: 'LED', device_pin: 'VCC'
        <BLANKLINE>
        Fix: Remove either board_pin or source_device/source_pin
    """
    parts = [message]

    if example:
        parts.append(f"\nExample: {example}")

    if fix:
        parts.append(f"\nFix: {fix}")

    return "\n".join(parts)


def format_connection_error(
    error_type: str,
    board_pin: int | None = None,
    source_device: str | None = None,
    source_pin: str | None = None,
    device_name: str | None = None,
    device_pin_name: str | None = None,
) -> str:
    """
    Format connection-specific validation errors with context.

    Args:
        error_type: Type of connection error
        board_pin: Board pin number (if applicable)
        source_device: Source device name (if applicable)
        source_pin: Source pin name (if applicable)
        device_name: Target device name
        device_pin_name: Target device pin name

    Returns:
        Formatted error message with examples

    Raises:
        ValueError: If error_type is not recognized
    """
    target_info = ""
    if device_name and device_pin_name:
        target_info = f" Target: {device_name}.{device_pin_name}"

    if error_type == "missing_device_name":
        return format_validation_error(
            f"Connection missing 'device_name' (target device).{target_info}",
            example="device_name: 'BH1750', device_pin_name: 'VCC'",
            fix="Add 'device' or 'device_name' field to connection",
        )

    elif error_type == "missing_device_pin":
        return format_validation_error(
            f"Connection missing 'device_pin_name' (target pin). Device: {device_name}",
            example="device_pin_name: 'VCC' (or device_pin: 'VCC')",
            fix="Add 'device_pin' or 'device_pin_name' field to connection",
        )

    elif error_type == "incomplete_device_source":
        return format_validation_error(
            f"Incomplete device-to-device connection. "
            f"source_device={source_device}, source_pin={source_pin}.{target_info}",
            example="source_device: 'Power', source_pin: 'OUT', device: 'LED', device_pin: 'VIN'",
            fix="Specify both 'source_device' AND 'source_pin' together",
        )

    elif error_type == "both_sources":
        return format_validation_error(
            f"Connection has BOTH board_pin ({board_pin}) and device source "
            f"({source_device}.{source_pin}).{target_info}",
            example=(
                "Board: board_pin: 1, device: 'LED', device_pin: 'VCC'\n"
                "         OR Device: source_device: 'Power', source_pin: 'OUT',\n"
                "                    device: 'LED', device_pin: 'VIN'"
            ),
            fix="Use EITHER board_pin OR source_device/source_pin, not both",
        )

    elif error_type == "no_source":
        return format_validation_error(
            f"Connection has no source specified.{target_info}",
            example=(
                "Board: board_pin: 1, device: 'LED', device_pin: 'VCC'\n"
                "         OR Device: source_device: 'Power', source_pin: 'OUT',\n"
                "                    device: 'LED', device_pin: 'VIN'"
            ),
            fix="Specify EITHER board_pin OR both source_device and source_pin",
        )

    else:
        raise ValueError(f"Unknown connection error type: {error_type}")


def format_config_error(
    error_type: str,
    detail: str | None = None,
    context: dict[str, str] | None = None,
) -> str:
    """
    Format configuration loading errors with helpful examples.

    Args:
        error_type: Type of configuration error
        detail: Additional detail about the error
        context: Dictionary of context information

    Returns:
        Formatted error message

    Raises:
        ValueError: If error_type is not recognized
    """
    context = context or {}

    if error_type == "device_not_found":
        device_type = context.get("device_type", "unknown")
        return format_validation_error(
            f"Device type '{device_type}' not found in registry",
            example="type: 'bh1750'  # Use predefined device\nOR define custom:\n"
            "  name: 'Custom', pins: [{name: 'VCC', role: '3V3'}]",
            fix="Check 'pinviz list' for available devices or define custom device",
        )

    elif error_type == "board_not_found":
        board_name = context.get("board_name", "unknown")
        return format_validation_error(
            f"Board '{board_name}' not found",
            example="board: 'raspberry_pi_5'  # or 'rpi5', 'rpi4', 'pico'",
            fix="Use 'pinviz list' to see available boards",
        )

    elif error_type == "invalid_pin_number":
        pin_num = context.get("pin_number", "?")
        max_pin = context.get("max_pin", "40")
        return format_validation_error(
            f"Invalid board_pin: {pin_num} (must be 1-{max_pin})",
            example=f"board_pin: 1  # Physical pin number (1-{max_pin})",
            fix=f"Use a physical pin number between 1 and {max_pin}",
        )

    elif error_type == "invalid_yaml":
        return format_validation_error(
            f"Invalid YAML syntax: {detail}",
            fix="Check indentation (use spaces, not tabs) and quote special characters",
        )

    elif error_type == "invalid_json":
        return format_validation_error(
            f"Invalid JSON syntax: {detail}",
            fix="Validate JSON at jsonlint.com or use a JSON formatter",
        )

    elif error_type == "file_too_large":
        return format_validation_error(
            f"Config file too large: {detail}",
            fix="Split large diagrams into multiple files or reduce connections",
        )

    else:
        raise ValueError(f"Unknown config error type: {error_type}")


def format_validation_issue_summary(
    issue_count: int,
    error_count: int,
    warning_count: int,
) -> str:
    """
    Format a summary of validation issues.

    Args:
        issue_count: Total number of issues
        error_count: Number of errors
        warning_count: Number of warnings

    Returns:
        Human-readable summary string
    """
    if issue_count == 0:
        return "Validation passed with no issues"

    parts = [f"Found {issue_count} validation issue{'s' if issue_count > 1 else ''}:"]

    if error_count > 0:
        parts.append(f"  {error_count} error{'s' if error_count > 1 else ''}")

    if warning_count > 0:
        parts.append(f"  {warning_count} warning{'s' if warning_count > 1 else ''}")

    return "\n".join(parts)
