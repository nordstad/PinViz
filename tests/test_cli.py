"""Tests for CLI commands."""

import sys
from unittest.mock import Mock, patch

from pinviz import cli


def test_main_with_no_args_shows_help(capsys):
    """Test that main with no arguments shows error (subcommand required)."""
    import pytest

    with patch.object(sys, "argv", ["pinviz"]):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 2  # argparse error exit code
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()


def test_main_with_render_command(sample_yaml_config, temp_output_dir):
    """Test main with render command."""
    output_file = temp_output_dir / "test_output.svg"
    with (
        patch.object(
            sys,
            "argv",
            ["pinviz", "render", str(sample_yaml_config), "-o", str(output_file)],
        ),
        patch("pinviz.cli.SVGRenderer") as mock_renderer,
    ):
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = cli.main()
        assert result == 0
        mock_instance.render.assert_called_once()


def test_main_with_example_command(temp_output_dir):
    """Test main with example command."""
    output_file = temp_output_dir / "bh1750.svg"
    with (
        patch.object(sys, "argv", ["pinviz", "example", "bh1750", "-o", str(output_file)]),
        patch("pinviz.cli.SVGRenderer") as mock_renderer,
    ):
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = cli.main()
        assert result == 0
        mock_instance.render.assert_called_once()


def test_main_with_list_command(capsys):
    """Test main with list command."""
    with patch.object(sys, "argv", ["pinviz", "list"]):
        result = cli.main()
        assert result == 0
        captured = capsys.readouterr()
        assert "Available Boards:" in captured.out
        assert "Available Device Templates:" in captured.out


def test_render_command_success(sample_yaml_config, temp_output_dir):
    """Test successful render command."""
    output_file = temp_output_dir / "test.svg"
    args = Mock(config=str(sample_yaml_config), output=str(output_file))

    with patch("pinviz.cli.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = cli.render_command(args)
        assert result == 0
        mock_instance.render.assert_called_once()


def test_render_command_default_output(sample_yaml_config):
    """Test render command with default output path."""
    args = Mock(config=str(sample_yaml_config), output=None)

    with patch("pinviz.cli.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = cli.render_command(args)
        assert result == 0
        # Check that output path is derived from config path
        call_args = mock_instance.render.call_args
        output_path = call_args[0][1]
        assert output_path.suffix == ".svg"


def test_render_command_creates_output_directory(sample_yaml_config, temp_output_dir):
    """Test that render command creates output directory if needed."""
    nested_output = temp_output_dir / "nested" / "dir" / "output.svg"
    args = Mock(config=str(sample_yaml_config), output=str(nested_output))

    with patch("pinviz.cli.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = cli.render_command(args)
        assert result == 0
        assert nested_output.parent.exists()


def test_render_command_file_not_found(capsys):
    """Test render command with non-existent config file."""
    args = Mock(config="/nonexistent/file.yaml", output="output.svg")
    result = cli.render_command(args)
    assert result == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "not found" in captured.err


def test_render_command_handles_exception(sample_yaml_config, capsys):
    """Test render command handles exceptions gracefully."""
    args = Mock(config=str(sample_yaml_config), output="output.svg")

    with patch("pinviz.cli.load_diagram") as mock_load:
        mock_load.side_effect = Exception("Test error")
        result = cli.render_command(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err


def test_example_command_bh1750(temp_output_dir):
    """Test generating BH1750 example."""
    output_file = temp_output_dir / "bh1750.svg"
    args = Mock()
    args.name = "bh1750"
    args.output = str(output_file)

    with patch("pinviz.cli.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = cli.example_command(args)
        assert result == 0
        mock_instance.render.assert_called_once()


def test_example_command_ir_led(temp_output_dir):
    """Test generating IR LED example."""
    output_file = temp_output_dir / "ir_led.svg"
    args = Mock()
    args.name = "ir_led"
    args.output = str(output_file)

    with patch("pinviz.cli.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = cli.example_command(args)
        assert result == 0
        mock_instance.render.assert_called_once()


def test_example_command_i2c_spi(temp_output_dir):
    """Test generating I2C/SPI example."""
    output_file = temp_output_dir / "i2c_spi.svg"
    args = Mock()
    args.name = "i2c_spi"
    args.output = str(output_file)

    with patch("pinviz.cli.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = cli.example_command(args)
        assert result == 0
        mock_instance.render.assert_called_once()


def test_example_command_default_output():
    """Test example command with default output path."""
    args = Mock()
    args.name = "bh1750"
    args.output = None

    with patch("pinviz.cli.SVGRenderer") as mock_renderer:
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance
        result = cli.example_command(args)
        assert result == 0
        # Check that default output is in ./out directory
        call_args = mock_instance.render.call_args
        output_path = call_args[0][1]
        assert "out" in str(output_path)
        assert output_path.name == "bh1750.svg"


def test_example_command_unknown_example(capsys):
    """Test example command with unknown example name."""
    args = Mock()
    args.name = "unknown_example"
    args.output = "output.svg"
    result = cli.example_command(args)
    assert result == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "Unknown example" in captured.err


def test_example_command_handles_exception(capsys):
    """Test example command handles exceptions gracefully."""
    args = Mock()
    args.name = "bh1750"
    args.output = "output.svg"

    with patch("pinviz.cli.create_bh1750_example") as mock_create:
        mock_create.side_effect = Exception("Test error")
        result = cli.example_command(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err


def test_list_command_displays_boards(capsys):
    """Test that list command displays available boards."""
    result = cli.list_command()
    assert result == 0
    captured = capsys.readouterr()
    assert "Available Boards:" in captured.out
    assert "raspberry_pi_5" in captured.out
    assert "rpi5" in captured.out


def test_list_command_displays_devices(capsys):
    """Test that list command displays available device templates."""
    result = cli.list_command()
    assert result == 0
    captured = capsys.readouterr()
    assert "Available Device Templates:" in captured.out
    assert "bh1750" in captured.out.lower() or "BH1750" in captured.out


def test_list_command_displays_examples(capsys):
    """Test that list command displays available examples."""
    result = cli.list_command()
    assert result == 0
    captured = capsys.readouterr()
    assert "Available Examples:" in captured.out
    assert "bh1750" in captured.out
    assert "ir_led" in captured.out
    assert "i2c_spi" in captured.out


def test_create_bh1750_example():
    """Test BH1750 example creator."""
    diagram = cli.create_bh1750_example()
    assert diagram is not None
    assert "BH1750" in diagram.title
    assert len(diagram.devices) == 1
    assert diagram.devices[0].name == "BH1750"
    assert len(diagram.connections) == 4
    assert diagram.show_gpio_diagram is True


def test_create_ir_led_example():
    """Test IR LED example creator."""
    diagram = cli.create_ir_led_example()
    assert diagram is not None
    assert "IR LED" in diagram.title
    assert len(diagram.devices) == 1
    assert "IR LED Ring" in diagram.devices[0].name
    assert len(diagram.connections) == 3
    assert diagram.show_gpio_diagram is True


def test_create_i2c_spi_example():
    """Test I2C/SPI example creator."""
    diagram = cli.create_i2c_spi_example()
    assert diagram is not None
    assert "I2C" in diagram.title or "SPI" in diagram.title
    assert len(diagram.devices) == 3
    # Should have BH1750, SPI device, and LED
    device_names = [d.name for d in diagram.devices]
    assert "BH1750" in device_names
    assert any("LED" in name for name in device_names)
    assert len(diagram.connections) > 6  # Multiple device connections
    assert diagram.show_gpio_diagram is True


def test_full_render_workflow(sample_yaml_config, temp_output_dir):
    """Test complete render workflow from config to SVG."""
    output_file = temp_output_dir / "integration_test.svg"

    with (
        patch("pinviz.cli.SVGRenderer") as mock_renderer,
        patch.object(
            sys,
            "argv",
            ["pinviz", "render", str(sample_yaml_config), "-o", str(output_file)],
        ),
    ):
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance

        result = cli.main()
        assert result == 0

        # Verify renderer was called with correct arguments
        mock_instance.render.assert_called_once()
        call_args = mock_instance.render.call_args[0]
        diagram = call_args[0]
        output_path = call_args[1]

        assert diagram.title == "Test Configuration"
        assert str(output_path) == str(output_file)


def test_full_example_workflow(temp_output_dir):
    """Test complete example workflow."""
    output_file = temp_output_dir / "example_test.svg"

    with (
        patch("pinviz.cli.SVGRenderer") as mock_renderer,
        patch.object(
            sys,
            "argv",
            ["pinviz", "example", "bh1750", "-o", str(output_file)],
        ),
    ):
        mock_instance = Mock()
        mock_renderer.return_value = mock_instance

        result = cli.main()
        assert result == 0

        # Verify renderer was called
        mock_instance.render.assert_called_once()
        call_args = mock_instance.render.call_args[0]
        diagram = call_args[0]

        assert "BH1750" in diagram.title
        assert len(diagram.devices) == 1
