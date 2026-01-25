"""Integration tests for theme system with config loading and rendering."""

import tempfile
from pathlib import Path

import pytest

from pinviz.config_loader import load_diagram
from pinviz.model import Diagram
from pinviz.render_svg import SVGRenderer
from pinviz.theme import Theme


class TestThemeConfigLoading:
    """Tests for theme loading from YAML config."""

    def test_load_light_theme_from_yaml(self, tmp_path):
        """Test loading light theme from YAML config."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            """
title: "Test Diagram"
board: "raspberry_pi_5"
theme: "light"
devices:
  - type: "bh1750"
connections:
  - board_pin: 1
    device: "BH1750"
    device_pin: "VCC"
"""
        )

        diagram = load_diagram(config_file)
        assert diagram.theme == Theme.LIGHT

    def test_load_dark_theme_from_yaml(self, tmp_path):
        """Test loading dark theme from YAML config."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            """
title: "Test Diagram"
board: "raspberry_pi_5"
theme: "dark"
devices:
  - type: "bh1750"
connections:
  - board_pin: 1
    device: "BH1750"
    device_pin: "VCC"
"""
        )

        diagram = load_diagram(config_file)
        assert diagram.theme == Theme.DARK

    def test_default_theme_is_light(self, tmp_path):
        """Test default theme is light when not specified."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            """
title: "Test Diagram"
board: "raspberry_pi_5"
devices:
  - type: "bh1750"
connections:
  - board_pin: 1
    device: "BH1750"
    device_pin: "VCC"
"""
        )

        diagram = load_diagram(config_file)
        assert diagram.theme == Theme.LIGHT

    def test_case_insensitive_theme_loading(self, tmp_path):
        """Test theme loading is case-insensitive."""
        # Test uppercase
        config_file = tmp_path / "test1.yaml"
        config_file.write_text(
            """
title: "Test Diagram"
board: "raspberry_pi_5"
theme: "DARK"
devices:
  - type: "bh1750"
connections:
  - board_pin: 1
    device: "BH1750"
    device_pin: "VCC"
"""
        )

        diagram = load_diagram(config_file)
        assert diagram.theme == Theme.DARK

        # Test mixed case
        config_file2 = tmp_path / "test2.yaml"
        config_file2.write_text(
            """
title: "Test Diagram"
board: "raspberry_pi_5"
theme: "Light"
devices:
  - type: "bh1750"
connections:
  - board_pin: 1
    device: "BH1750"
    device_pin: "VCC"
"""
        )

        diagram2 = load_diagram(config_file2)
        assert diagram2.theme == Theme.LIGHT

    def test_invalid_theme_defaults_to_light(self, tmp_path):
        """Test invalid theme defaults to light with warning."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            """
title: "Test Diagram"
board: "raspberry_pi_5"
theme: "invalid"
devices:
  - type: "bh1750"
connections:
  - board_pin: 1
    device: "BH1750"
    device_pin: "VCC"
"""
        )

        diagram = load_diagram(config_file)
        assert diagram.theme == Theme.LIGHT  # Should default to light


class TestThemeRendering:
    """Tests for theme in SVG rendering."""

    def test_render_with_light_theme(self, tmp_path):
        """Test rendering diagram with light theme produces valid SVG."""
        from pinviz import boards, devices
        from pinviz.model import Connection

        board = boards.raspberry_pi_5()
        sensor = devices.get_registry().create("bh1750")
        sensor.name = "BH1750"

        diagram = Diagram(
            title="Test Light Theme",
            board=board,
            devices=[sensor],
            connections=[Connection(1, "BH1750", "VCC")],
            theme=Theme.LIGHT,
        )

        output_file = tmp_path / "light.svg"
        renderer = SVGRenderer()
        renderer.render(diagram, output_file)

        # Verify file was created and has content
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 0
        assert "<svg" in content
        assert "</svg>" in content

    def test_render_with_dark_theme(self, tmp_path):
        """Test rendering diagram with dark theme produces valid SVG."""
        from pinviz import boards, devices
        from pinviz.model import Connection

        board = boards.raspberry_pi_5()
        sensor = devices.get_registry().create("bh1750")
        sensor.name = "BH1750"

        diagram = Diagram(
            title="Test Dark Theme",
            board=board,
            devices=[sensor],
            connections=[Connection(1, "BH1750", "VCC")],
            theme=Theme.DARK,
        )

        output_file = tmp_path / "dark.svg"
        renderer = SVGRenderer()
        renderer.render(diagram, output_file)

        # Verify file was created and has content
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 0
        assert "<svg" in content
        assert "</svg>" in content

    def test_dark_theme_has_dark_background(self, tmp_path):
        """Test dark theme SVG has dark background."""
        from pinviz import boards, devices
        from pinviz.model import Connection

        board = boards.raspberry_pi_5()
        sensor = devices.get_registry().create("bh1750")
        sensor.name = "BH1750"

        diagram = Diagram(
            title="Test Dark Theme",
            board=board,
            devices=[sensor],
            connections=[Connection(1, "BH1750", "VCC")],
            theme=Theme.DARK,
        )

        output_file = tmp_path / "dark.svg"
        renderer = SVGRenderer()
        renderer.render(diagram, output_file)

        content = output_file.read_text()
        # Dark theme should have #1E1E1E background
        assert "#1E1E1E" in content or "#1e1e1e" in content.lower()

    def test_light_theme_has_white_background(self, tmp_path):
        """Test light theme SVG has white background."""
        from pinviz import boards, devices
        from pinviz.model import Connection

        board = boards.raspberry_pi_5()
        sensor = devices.get_registry().create("bh1750")
        sensor.name = "BH1750"

        diagram = Diagram(
            title="Test Light Theme",
            board=board,
            devices=[sensor],
            connections=[Connection(1, "BH1750", "VCC")],
            theme=Theme.LIGHT,
        )

        output_file = tmp_path / "light.svg"
        renderer = SVGRenderer()
        renderer.render(diagram, output_file)

        content = output_file.read_text()
        # Light theme should have white background
        assert 'fill="white"' in content


class TestThemeProgrammaticAPI:
    """Tests for theme in programmatic Python API."""

    def test_create_diagram_with_light_theme(self):
        """Test creating diagram with light theme via Python API."""
        from pinviz import boards, devices
        from pinviz.model import Connection

        board = boards.raspberry_pi_5()
        sensor = devices.get_registry().create("bh1750")
        sensor.name = "BH1750"

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[sensor],
            connections=[Connection(1, "BH1750", "VCC")],
            theme=Theme.LIGHT,
        )

        assert diagram.theme == Theme.LIGHT

    def test_create_diagram_with_dark_theme(self):
        """Test creating diagram with dark theme via Python API."""
        from pinviz import boards, devices
        from pinviz.model import Connection

        board = boards.raspberry_pi_5()
        sensor = devices.get_registry().create("bh1750")
        sensor.name = "BH1750"

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[sensor],
            connections=[Connection(1, "BH1750", "VCC")],
            theme=Theme.DARK,
        )

        assert diagram.theme == Theme.DARK

    def test_diagram_defaults_to_light_theme(self):
        """Test diagram defaults to light theme when not specified."""
        from pinviz import boards, devices
        from pinviz.model import Connection

        board = boards.raspberry_pi_5()
        sensor = devices.get_registry().create("bh1750")
        sensor.name = "BH1750"

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[sensor],
            connections=[Connection(1, "BH1750", "VCC")],
        )

        assert diagram.theme == Theme.LIGHT

    def test_override_theme_after_creation(self):
        """Test overriding theme after diagram creation."""
        from pinviz import boards, devices
        from pinviz.model import Connection

        board = boards.raspberry_pi_5()
        sensor = devices.get_registry().create("bh1750")
        sensor.name = "BH1750"

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[sensor],
            connections=[Connection(1, "BH1750", "VCC")],
            theme=Theme.LIGHT,
        )

        assert diagram.theme == Theme.LIGHT

        # Override to dark
        diagram.theme = Theme.DARK
        assert diagram.theme == Theme.DARK
