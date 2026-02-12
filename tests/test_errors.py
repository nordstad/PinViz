"""Tests for error formatting utilities."""

import pytest

from pinviz.errors import (
    format_config_error,
    format_connection_error,
    format_validation_error,
    format_validation_issue_summary,
)


class TestFormatValidationError:
    """Tests for format_validation_error function."""

    def test_message_only(self):
        """Test formatting with message only."""
        result = format_validation_error("Something went wrong")
        assert result == "Something went wrong"

    def test_message_with_example(self):
        """Test formatting with message and example."""
        result = format_validation_error("Invalid config", example="config: value")
        assert "Invalid config" in result
        assert "Example: config: value" in result

    def test_message_with_fix(self):
        """Test formatting with message and fix."""
        result = format_validation_error("Invalid config", fix="Use correct syntax")
        assert "Invalid config" in result
        assert "Fix: Use correct syntax" in result

    def test_message_with_example_and_fix(self):
        """Test formatting with all parameters."""
        result = format_validation_error(
            "Invalid config",
            example="config: value",
            fix="Use correct syntax",
        )
        assert "Invalid config" in result
        assert "Example: config: value" in result
        assert "Fix: Use correct syntax" in result


class TestFormatConnectionError:
    """Tests for format_connection_error function."""

    def test_missing_device_name(self):
        """Test missing device name error."""
        result = format_connection_error("missing_device_name")
        assert "missing 'device_name'" in result
        assert "Example:" in result
        assert "Fix:" in result

    def test_missing_device_pin(self):
        """Test missing device pin error."""
        result = format_connection_error("missing_device_pin", device_name="LED")
        assert "missing 'device_pin_name'" in result
        assert "Device: LED" in result
        assert "Example:" in result

    def test_incomplete_device_source(self):
        """Test incomplete device source error."""
        result = format_connection_error(
            "incomplete_device_source",
            source_device="Power",
            source_pin=None,
            device_name="LED",
            device_pin_name="VCC",
        )
        assert "Incomplete device-to-device connection" in result
        assert "source_device=Power" in result
        assert "Example:" in result

    def test_both_sources(self):
        """Test both sources specified error."""
        result = format_connection_error(
            "both_sources",
            board_pin=1,
            source_device="Power",
            source_pin="OUT",
            device_name="LED",
            device_pin_name="VCC",
        )
        assert "BOTH board_pin" in result
        assert "board_pin (1)" in result
        assert "Power.OUT" in result
        assert "Example:" in result

    def test_no_source(self):
        """Test no source specified error."""
        result = format_connection_error(
            "no_source",
            device_name="LED",
            device_pin_name="VCC",
        )
        assert "no source specified" in result
        assert "Target: LED.VCC" in result
        assert "Example:" in result

    def test_unknown_error_type(self):
        """Test unknown error type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown connection error type"):
            format_connection_error("unknown_type")


class TestFormatConfigError:
    """Tests for format_config_error function."""

    def test_device_not_found(self):
        """Test device not found error."""
        result = format_config_error(
            "device_not_found",
            context={"device_type": "xyz"},
        )
        assert "Device type 'xyz' not found" in result
        assert "Example:" in result
        assert "pinviz list" in result

    def test_board_not_found(self):
        """Test board not found error."""
        result = format_config_error(
            "board_not_found",
            context={"board_name": "xyz"},
        )
        assert "Board 'xyz' not found" in result
        assert "Example:" in result
        assert "pinviz list" in result

    def test_invalid_pin_number(self):
        """Test invalid pin number error."""
        result = format_config_error(
            "invalid_pin_number",
            context={"pin_number": "99", "max_pin": "40"},
        )
        assert "Invalid board_pin: 99" in result
        assert "1-40" in result
        assert "Example:" in result

    def test_invalid_yaml(self):
        """Test invalid YAML error."""
        result = format_config_error(
            "invalid_yaml",
            detail="syntax error on line 5",
        )
        assert "Invalid YAML syntax" in result
        assert "syntax error on line 5" in result
        assert "Fix:" in result

    def test_invalid_json(self):
        """Test invalid JSON error."""
        result = format_config_error(
            "invalid_json",
            detail="unexpected token",
        )
        assert "Invalid JSON syntax" in result
        assert "unexpected token" in result
        assert "Fix:" in result

    def test_file_too_large(self):
        """Test file too large error."""
        result = format_config_error(
            "file_too_large",
            detail="15MB (max: 10MB)",
        )
        assert "Config file too large" in result
        assert "15MB" in result
        assert "Fix:" in result

    def test_unknown_error_type(self):
        """Test unknown error type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown config error type"):
            format_config_error("unknown_type")


class TestFormatValidationIssueSummary:
    """Tests for format_validation_issue_summary function."""

    def test_no_issues(self):
        """Test summary with no issues."""
        result = format_validation_issue_summary(0, 0, 0)
        assert result == "Validation passed with no issues"

    def test_only_errors(self):
        """Test summary with only errors."""
        result = format_validation_issue_summary(3, 3, 0)
        assert "Found 3 validation issues" in result
        assert "3 errors" in result
        assert "warning" not in result

    def test_only_warnings(self):
        """Test summary with only warnings."""
        result = format_validation_issue_summary(2, 0, 2)
        assert "Found 2 validation issues" in result
        assert "2 warnings" in result
        assert "error" not in result.lower()

    def test_errors_and_warnings(self):
        """Test summary with both errors and warnings."""
        result = format_validation_issue_summary(5, 3, 2)
        assert "Found 5 validation issues" in result
        assert "3 errors" in result
        assert "2 warnings" in result

    def test_singular_forms(self):
        """Test singular forms for single issue."""
        result = format_validation_issue_summary(1, 1, 0)
        assert "1 validation issue:" in result
        assert "1 error" in result
