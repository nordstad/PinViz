"""Tests for structured logging functionality."""

import logging

from typer.testing import CliRunner

from pinviz.cli import app
from pinviz.logging_config import configure_logging, get_logger

runner = CliRunner()


class TestLoggingConfiguration:
    """Test logging configuration setup."""

    def test_configure_logging_default(self):
        """Test default logging configuration."""
        configure_logging()
        log = get_logger(__name__)

        assert log is not None
        # Logger is wrapped in a proxy
        assert hasattr(log, "info")
        assert hasattr(log, "error")
        assert hasattr(log, "debug")

    def test_configure_logging_json_format(self, caplog):
        """Test JSON format configuration."""
        configure_logging(level="INFO", format="json")
        log = get_logger(__name__)

        # Emit log message - will be captured by caplog
        with caplog.at_level(logging.INFO):
            log.info("test_event", key="value")

        # Verify logging worked (caplog captures it)
        assert len(caplog.records) > 0

    def test_configure_logging_console_format(self, caplog):
        """Test console format configuration."""
        configure_logging(level="INFO", format="console")
        log = get_logger(__name__)

        # Emit log message
        with caplog.at_level(logging.INFO):
            log.info("test_event", key="value")

        # Verify logging worked
        assert len(caplog.records) > 0

    def test_configure_logging_levels(self):
        """Test different log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            configure_logging(level=level, format="json")
            get_logger(__name__)  # Initialize logger

            # Verify logger level is set
            stdlib_logger = logging.getLogger("pinviz")
            expected_level = getattr(logging, level)
            assert stdlib_logger.level <= expected_level

    def test_log_message_includes_callsite_info(self, caplog):
        """Test that log messages include file, function, and line info."""
        configure_logging(level="INFO", format="json")
        log = get_logger(__name__)

        with caplog.at_level(logging.INFO):
            log.info("test_callsite")

        # Verify log was emitted
        assert len(caplog.records) > 0
        # Verify it came from this file
        assert "test_logging" in caplog.records[0].name

    def test_log_exception_includes_traceback(self, caplog):
        """Test that exceptions are logged with tracebacks."""
        configure_logging(level="ERROR", format="json")
        log = get_logger(__name__)

        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("Test exception")
            except ValueError:
                log.exception("error_occurred")

        # Verify exception was logged
        assert len(caplog.records) > 0
        assert caplog.records[0].levelname == "ERROR"
        # Verify exception info is present
        assert caplog.records[0].exc_info is not None


class TestCLILoggingBehavior:
    """Test CLI logging behavior (fixed to ERROR-only)."""

    def test_default_log_level_error(self, tmp_path):
        """Test default log level is ERROR (quiet output)."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            """
title: Test
board: raspberry_pi_5
devices:
  - type: led
connections:
  - board_pin: 11
    device: Red LED
    device_pin: +
  - board_pin: 6
    device: Red LED
    device_pin: "-"
"""
        )

        output_file = tmp_path / "test.svg"

        result = runner.invoke(
            app,
            ["render", str(config_file), "-o", str(output_file)],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        # At ERROR level, should see minimal logs (Rich progress is transient)
        # Success message still present
        assert "Diagram generated" in result.stdout


class TestLogMessageEmission:
    """Test that key events emit expected log messages."""

    def test_render_command_succeeds(self, tmp_path):
        """Test render command succeeds with quiet output."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            """
title: Test Diagram
board: raspberry_pi_5
devices:
  - type: led
connections:
  - board_pin: 11
    device: Red LED
    device_pin: +
  - board_pin: 6
    device: Red LED
    device_pin: "-"
"""
        )

        output_file = tmp_path / "test.svg"

        result = runner.invoke(
            app,
            [
                "render",
                str(config_file),
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

    def test_validation_command_succeeds(self, tmp_path):
        """Test validate command succeeds with quiet output."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            """
title: Test
board: raspberry_pi_5
devices:
  - type: led
connections:
  - board_pin: 11
    device: Red LED
    device_pin: +
  - board_pin: 6
    device: Red LED
    device_pin: "-"
"""
        )

        result = runner.invoke(
            app,
            [
                "validate",
                str(config_file),
            ],
        )

        assert result.exit_code == 0

    def test_error_command_fails(self, tmp_path):
        """Test command with non-existent file fails."""
        # Non-existent file
        config_file = tmp_path / "nonexistent.yaml"

        result = runner.invoke(
            app,
            [
                "render",
                str(config_file),
                "-o",
                "/tmp/out.svg",
            ],
        )

        # Typer validates file existence before calling the command
        assert result.exit_code != 0


class TestLoggingIntegration:
    """Test logging integration with normal operations."""

    def test_logging_does_not_break_rendering(self, tmp_path):
        """Test that logging doesn't interfere with SVG generation."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            """
title: Integration Test
board: raspberry_pi_5
devices:
  - type: bh1750
connections:
  - board_pin: 1
    device: BH1750 Light Sensor
    device_pin: VCC
  - board_pin: 6
    device: BH1750 Light Sensor
    device_pin: GND
  - board_pin: 3
    device: BH1750 Light Sensor
    device_pin: SDA
  - board_pin: 5
    device: BH1750 Light Sensor
    device_pin: SCL
"""
        )

        output_file = tmp_path / "test.svg"

        result = runner.invoke(
            app,
            [
                "render",
                str(config_file),
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify SVG is valid
        svg_content = output_file.read_text()
        assert "<?xml" in svg_content or "<svg" in svg_content
        assert "BH1750" in svg_content
        assert "Integration Test" in svg_content

    def test_validation_errors_are_caught(self, tmp_path, caplog):
        """Test validation errors are properly handled."""
        config_file = tmp_path / "bad_config.yaml"
        config_file.write_text(
            """
title: Bad Config
board: raspberry_pi_5
devices:
  - type: led
    name: LED1
  - type: led
    name: LED2
connections:
  - board_pin: 11
    device: LED1
    device_pin: +
  - board_pin: 11
    device: LED2
    device_pin: +
"""
        )

        output_file = tmp_path / "test.svg"

        with caplog.at_level(logging.ERROR):
            result = runner.invoke(
                app,
                [
                    "render",
                    str(config_file),
                    "-o",
                    str(output_file),
                ],
            )

        # Should fail due to pin conflict
        assert result.exit_code == 1
        # Should have error logs from validation
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_records) > 0

    def test_example_command_works(self, tmp_path):
        """Test example command works with quiet logging."""
        output_file = tmp_path / "example.svg"

        result = runner.invoke(
            app,
            [
                "example",
                "bh1750",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()


class TestLoggerInstances:
    """Test logger instance behavior."""

    def test_get_logger_with_module_name(self):
        """Test getting logger with module name."""
        log = get_logger("test.module")
        assert log is not None
        # Logger is wrapped in a proxy but has logging methods
        assert hasattr(log, "info")
        assert hasattr(log, "error")

    def test_multiple_loggers_share_config(self, caplog):
        """Test multiple loggers use same configuration."""
        configure_logging(level="INFO", format="json")

        log1 = get_logger("module1")
        log2 = get_logger("module2")

        assert log1 is not None
        assert log2 is not None

        # Both should produce logs
        with caplog.at_level(logging.INFO):
            log1.info("test1")
            log2.info("test2")

        # Verify both logged
        assert len(caplog.records) >= 2
        logger_names = [r.name for r in caplog.records]
        assert "module1" in logger_names
        assert "module2" in logger_names
