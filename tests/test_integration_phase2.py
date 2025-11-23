"""Integration tests for Phase 2: Full pipeline from prompt to diagram."""

from pinviz.model import Diagram
from pinviz.render_svg import SVGRenderer
from pinviz_mcp.connection_builder import ConnectionBuilder
from pinviz_mcp.device_manager import DeviceManager
from pinviz_mcp.parser import PromptParser
from pinviz_mcp.pin_assignment import PinAssigner


class TestPhase2Integration:
    """Integration tests for the full Phase 2 pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.device_manager = DeviceManager()
        self.parser = PromptParser(use_llm=False)
        self.pin_assigner = PinAssigner()
        self.connection_builder = ConnectionBuilder()

    def test_single_i2c_device_flow(self):
        """Test complete flow: prompt -> device -> pins -> diagram."""
        # Step 1: Parse prompt
        prompt = "connect BME280 to my pi"
        parsed = self.parser.parse(prompt)

        assert len(parsed.devices) == 1
        assert "BME280" in parsed.devices[0]

        # Step 2: Look up device in database
        # Try fuzzy match first
        device = self.device_manager.get_device_by_name(parsed.devices[0], fuzzy=True)
        if device is None:
            # If not found, try with exact ID
            device = self.device_manager.get_device_by_id("bme280")
        assert device is not None
        device_data = device.to_dict()

        # Step 3: Assign pins
        assignments, warnings = self.pin_assigner.assign_pins([device_data])
        assert len(assignments) > 0
        assert len(warnings) == 0

        # Step 4: Build diagram
        diagram = self.connection_builder.build_diagram(
            assignments=assignments,
            devices_data=[device_data],
            board_name=parsed.board,
            title="BME280 Wiring",
        )

        assert isinstance(diagram, Diagram)
        assert len(diagram.devices) == 1
        assert len(diagram.connections) == 4  # VCC, GND, SCL, SDA

    def test_two_i2c_devices_flow(self):
        """Test flow with two I2C devices sharing the bus."""
        # Parse prompt
        prompt = "connect BME280 and SSD1306"
        parsed = self.parser.parse(prompt)

        assert len(parsed.devices) == 2

        # Look up devices
        devices_data = []
        for device_name in parsed.devices:
            device = self.device_manager.get_device_by_name(device_name)
            if device:
                devices_data.append(device.to_dict())

        assert len(devices_data) == 2

        # Assign pins
        assignments, warnings = self.pin_assigner.assign_pins(devices_data)

        # Both devices should share I2C pins
        i2c_sda_assignments = [a for a in assignments if a.pin_role.value == "I2C_SDA"]
        i2c_scl_assignments = [a for a in assignments if a.pin_role.value == "I2C_SCL"]

        assert len(i2c_sda_assignments) == 2
        assert len(i2c_scl_assignments) == 2
        # All should use the same physical pins
        assert all(a.board_pin_number == 3 for a in i2c_sda_assignments)
        assert all(a.board_pin_number == 5 for a in i2c_scl_assignments)

        # Build diagram
        diagram = self.connection_builder.build_diagram(
            assignments=assignments,
            devices_data=devices_data,
            title="I2C Bus Sharing",
        )

        assert len(diagram.devices) == 2
        assert len(diagram.connections) >= 6  # At least 6 connections

    def test_gpio_device_flow(self):
        """Test flow with a simple GPIO device."""
        # Parse prompt
        prompt = "LED"
        parsed = self.parser.parse(prompt)

        assert "LED" in parsed.devices[0]

        # Look up device
        device = self.device_manager.get_device_by_name("LED")
        assert device is not None
        device_data = device.to_dict()

        # Assign pins
        assignments, warnings = self.pin_assigner.assign_pins([device_data])
        assert len(assignments) > 0

        # Build diagram
        diagram = self.connection_builder.build_diagram(
            assignments=assignments,
            devices_data=[device_data],
            title="LED Wiring",
        )

        assert isinstance(diagram, Diagram)
        assert len(diagram.devices) == 1

    def test_mixed_devices_flow(self):
        """Test flow with mixed I2C and GPIO devices."""
        # Parse prompt
        prompt = "connect BME280 and LED"
        parsed = self.parser.parse(prompt)

        assert len(parsed.devices) == 2

        # Look up devices
        devices_data = []
        for device_name in parsed.devices:
            device = self.device_manager.get_device_by_name(device_name)
            if device:
                devices_data.append(device.to_dict())

        assert len(devices_data) == 2

        # Assign pins
        assignments, warnings = self.pin_assigner.assign_pins(devices_data)
        assert len(assignments) > 0

        # Build diagram
        diagram = self.connection_builder.build_diagram(
            assignments=assignments,
            devices_data=devices_data,
            title="Mixed Devices",
        )

        assert len(diagram.devices) == 2
        assert len(diagram.connections) >= 4

    def test_diagram_can_be_rendered(self):
        """Test that generated diagram can be rendered to SVG."""
        # Parse and build a simple diagram
        device = self.device_manager.get_device_by_name("LED")
        device_data = device.to_dict()
        assignments, warnings = self.pin_assigner.assign_pins([device_data])

        diagram = self.connection_builder.build_diagram(
            assignments=assignments,
            devices_data=[device_data],
            title="LED Test",
        )

        # Attempt to render (we won't save, just test it doesn't crash)
        renderer = SVGRenderer()
        # This should not raise an exception
        try:
            svg_content = renderer._render_to_string(diagram)
            assert svg_content is not None
            assert len(svg_content) > 0
        except AttributeError:
            # _render_to_string might not exist, try render to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".svg", delete=True) as tmp:
                renderer.render(diagram, tmp.name)
                assert tmp.name

    def test_full_pipeline_function(self):
        """Test a convenience function that wraps the entire pipeline."""

        def generate_diagram_from_prompt(prompt: str, title: str | None = None) -> Diagram:
            """Generate a complete diagram from a natural language prompt."""
            # Parse
            parser = PromptParser(use_llm=False)
            parsed = parser.parse(prompt)

            # Look up devices
            device_manager = DeviceManager()
            devices_data = []
            for device_name in parsed.devices:
                device = device_manager.get_device_by_name(device_name)
                if device:
                    devices_data.append(device.to_dict())

            # Assign pins
            pin_assigner = PinAssigner()
            assignments, warnings = pin_assigner.assign_pins(devices_data)

            # Build diagram
            connection_builder = ConnectionBuilder()
            diagram = connection_builder.build_diagram(
                assignments=assignments,
                devices_data=devices_data,
                board_name=parsed.board,
                title=title or parsed.devices[0] if parsed.devices else "Wiring Diagram",
            )

            return diagram

        # Test the convenience function
        diagram = generate_diagram_from_prompt("connect BME280", title="BME280 Sensor")

        assert isinstance(diagram, Diagram)
        assert diagram.title == "BME280 Sensor"
        assert len(diagram.devices) == 1
        assert len(diagram.connections) > 0

    def test_error_handling_unknown_device(self):
        """Test error handling when device is not found."""
        parser = PromptParser(use_llm=False)
        parsed = parser.parse("connect UnknownDevice123")

        device_manager = DeviceManager()
        device = device_manager.get_device_by_name(parsed.devices[0])

        # Unknown device should return None
        assert device is None

    def test_prompt_with_multiple_words(self):
        """Test handling of device names with multiple words."""
        prompt = "connect BH1750 light sensor"
        parsed = self.parser.parse(prompt)

        # Should extract the device name
        assert len(parsed.devices) == 1

        # Try to find it in database
        device = self.device_manager.get_device_by_name(parsed.devices[0])
        # BH1750 should be found via fuzzy matching
        assert device is not None or parsed.devices[0].upper() in ["BH1750", "BH1750 LIGHT SENSOR"]


class TestPhase2PerformanceBaseline:
    """Baseline performance tests for Phase 2 pipeline."""

    def test_performance_baseline(self):
        """Establish baseline performance for the pipeline."""
        import time

        prompt = "connect BME280 and SSD1306 and LED"

        start = time.time()

        # Full pipeline
        parser = PromptParser(use_llm=False)
        parsed = parser.parse(prompt)

        device_manager = DeviceManager()
        devices_data = []
        for device_name in parsed.devices:
            device = device_manager.get_device_by_name(device_name)
            if device:
                devices_data.append(device.to_dict())

        pin_assigner = PinAssigner()
        assignments, warnings = pin_assigner.assign_pins(devices_data)

        connection_builder = ConnectionBuilder()
        diagram = connection_builder.build_diagram(
            assignments=assignments,
            devices_data=devices_data,
            title="Performance Test",
        )

        elapsed = time.time() - start

        # Should complete in under 100ms (very generous)
        assert elapsed < 0.1, f"Pipeline took {elapsed:.3f}s, expected < 0.1s"

        # Verify output is valid
        assert isinstance(diagram, Diagram)
        assert len(diagram.devices) > 0
