"""Tests for CLI commands using Typer CliRunner."""

from unittest.mock import Mock, patch

from typer.testing import CliRunner

from pinviz.cli import app

runner = CliRunner()


def test_main_with_no_args_shows_help():
    """Test that main with no arguments shows help (Typer default)."""
    result = runner.invoke(app, [])
    # Typer exits with code 2 when showing help due to missing command
    assert result.exit_code == 2
    assert "Usage:" in result.stdout or "Missing command" in result.stderr
    assert "Commands" in result.stdout or result.exit_code == 2


def test_main_with_render_command(sample_yaml_config, temp_output_dir):
    """Test main with render command."""
    output_file = temp_output_dir / "test_output.svg"
    with patch("pinviz.cli.commands.render.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = runner.invoke(
            app,
            ["render", str(sample_yaml_config), "-o", str(output_file)],
        )
        assert result.exit_code == 0
        mock_instance.render.assert_called_once()


def test_main_with_example_command(temp_output_dir):
    """Test main with example command."""
    output_file = temp_output_dir / "bh1750.svg"
    with patch("pinviz.cli.commands.example.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = runner.invoke(
            app,
            ["example", "bh1750", "-o", str(output_file)],
        )
        assert result.exit_code == 0
        mock_instance.render.assert_called_once()


def test_main_with_list_command(capsys):
    """Test main with list command."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Available Boards:" in result.stdout
    assert "Available Device Templates:" in result.stdout


def test_render_command_success(sample_yaml_config, temp_output_dir):
    """Test successful render command."""
    output_file = temp_output_dir / "test.svg"
    with patch("pinviz.cli.commands.render.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = runner.invoke(
            app,
            ["render", str(sample_yaml_config), "-o", str(output_file)],
        )
        assert result.exit_code == 0
        mock_instance.render.assert_called_once()


def test_render_command_default_output(sample_yaml_config):
    """Test render command with default output path."""
    with patch("pinviz.cli.commands.render.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = runner.invoke(
            app,
            ["render", str(sample_yaml_config)],
        )
        assert result.exit_code == 0
        # Check that SVG was rendered
        assert mock_instance.render.called
        # Get the output path from the call args
        call_args = mock_instance.render.call_args
        output_path = call_args[0][1]
        assert output_path.suffix == ".svg"


def test_render_command_creates_output_directory(sample_yaml_config, temp_output_dir):
    """Test that render command creates output directory if needed."""
    nested_output = temp_output_dir / "nested" / "dir" / "output.svg"
    with patch("pinviz.cli.commands.render.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = runner.invoke(
            app,
            ["render", str(sample_yaml_config), "-o", str(nested_output)],
        )
        assert result.exit_code == 0
        assert nested_output.parent.exists()


def test_render_command_file_not_found():
    """Test render command with non-existent file."""
    result = runner.invoke(
        app,
        ["render", "nonexistent.yaml"],
    )
    # Typer validates file existence before calling the command
    assert result.exit_code != 0


def test_render_command_handles_exception(sample_yaml_config):
    """Test that render command handles exceptions gracefully."""
    with patch("pinviz.cli.commands.render.load_diagram") as mock_load:
        mock_load.side_effect = Exception("Test error")
        result = runner.invoke(
            app,
            ["render", str(sample_yaml_config)],
        )
        assert result.exit_code == 1
        assert "Error" in result.stdout or "error" in result.stdout.lower()


def test_example_command_bh1750(temp_output_dir):
    """Test example command with bh1750."""
    output_file = temp_output_dir / "bh1750.svg"
    with patch("pinviz.cli.commands.example.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = runner.invoke(
            app,
            ["example", "bh1750", "-o", str(output_file)],
        )
        assert result.exit_code == 0
        mock_instance.render.assert_called_once()


def test_example_command_ir_led(temp_output_dir):
    """Test example command with ir_led."""
    output_file = temp_output_dir / "ir_led.svg"
    with patch("pinviz.cli.commands.example.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = runner.invoke(
            app,
            ["example", "ir_led", "-o", str(output_file)],
        )
        assert result.exit_code == 0
        mock_instance.render.assert_called_once()


def test_example_command_i2c_spi(temp_output_dir):
    """Test example command with i2c_spi."""
    output_file = temp_output_dir / "i2c_spi.svg"
    with patch("pinviz.cli.commands.example.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = runner.invoke(
            app,
            ["example", "i2c_spi", "-o", str(output_file)],
        )
        assert result.exit_code == 0
        mock_instance.render.assert_called_once()


def test_example_command_default_output():
    """Test example command with default output path."""
    with patch("pinviz.cli.commands.example.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = runner.invoke(
            app,
            ["example", "bh1750"],
        )
        assert result.exit_code == 0
        mock_instance.render.assert_called_once()


def test_example_command_unknown_example():
    """Test example command with unknown example name."""
    result = runner.invoke(
        app,
        ["example", "unknown"],
    )
    assert result.exit_code == 1
    assert "Unknown example" in result.stdout


def test_example_command_handles_exception():
    """Test that example command handles exceptions gracefully."""
    with patch("pinviz.cli.commands.example.create_bh1750_example") as mock_create:
        mock_create.side_effect = Exception("Test error")
        result = runner.invoke(
            app,
            ["example", "bh1750"],
        )
        assert result.exit_code == 1


def test_list_command_displays_boards():
    """Test that list command shows available boards."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Available Boards" in result.stdout
    assert "raspberry_pi_5" in result.stdout


def test_list_command_displays_devices():
    """Test that list command shows available device templates."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Available Device Templates" in result.stdout


def test_list_command_displays_examples():
    """Test that list command shows available examples."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Available Examples" in result.stdout
    assert "bh1750" in result.stdout


def test_create_bh1750_example():
    """Test creating BH1750 example diagram."""
    from pinviz.cli.commands.example import create_bh1750_example

    diagram = create_bh1750_example()
    assert diagram is not None
    assert diagram.title == "BH1750 Light Sensor Wiring"
    assert len(diagram.devices) == 1
    assert len(diagram.connections) == 4


def test_create_ir_led_example():
    """Test creating IR LED example diagram."""
    from pinviz.cli.commands.example import create_ir_led_example

    diagram = create_ir_led_example()
    assert diagram is not None
    assert diagram.title == "IR LED Ring Wiring"
    assert len(diagram.devices) == 1
    assert len(diagram.connections) == 3


def test_create_i2c_spi_example():
    """Test creating I2C/SPI example diagram."""
    from pinviz.cli.commands.example import create_i2c_spi_example

    diagram = create_i2c_spi_example()
    assert diagram is not None
    assert diagram.title == "I2C and SPI Devices Example"
    assert len(diagram.devices) == 3
    assert len(diagram.connections) == 12


def test_full_render_workflow(sample_yaml_config, temp_output_dir):
    """Test complete render workflow from config to SVG."""
    output_file = temp_output_dir / "workflow_test.svg"
    result = runner.invoke(
        app,
        ["render", str(sample_yaml_config), "-o", str(output_file)],
    )
    assert result.exit_code == 0
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_full_example_workflow(temp_output_dir):
    """Test complete example workflow."""
    output_file = temp_output_dir / "example_workflow.svg"
    result = runner.invoke(
        app,
        ["example", "bh1750", "-o", str(output_file)],
    )
    assert result.exit_code == 0
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_version_flag():
    """Test --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "pinviz version" in result.stdout


def test_help_flag():
    """Test --help flag."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "Commands" in result.stdout


def test_render_help():
    """Test render --help."""
    result = runner.invoke(app, ["render", "--help"])
    assert result.exit_code == 0
    assert "CONFIG_FILE" in result.stdout


def test_render_with_json_output(sample_yaml_config, temp_output_dir):
    """Test render command with --json flag."""
    output_file = temp_output_dir / "test_json.svg"
    result = runner.invoke(
        app,
        ["render", str(sample_yaml_config), "-o", str(output_file), "--json"],
    )
    assert result.exit_code == 0
    assert "status" in result.stdout  # JSON output includes status
    assert output_file.exists()


def test_validate_command(sample_yaml_config):
    """Test validate command."""
    result = runner.invoke(
        app,
        ["validate", str(sample_yaml_config)],
    )
    assert result.exit_code == 0


def test_validate_command_strict(sample_yaml_config):
    """Test validate command with --strict flag."""
    result = runner.invoke(
        app,
        ["validate", str(sample_yaml_config), "--strict"],
    )
    # Should succeed if no warnings
    assert result.exit_code in [0, 1]  # Depends on validation results
