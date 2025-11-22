"""Unit tests for the prompt parser module."""

import pytest
from pinviz_mcp.parser import ParsedPrompt, PromptParser, parse_prompt


class TestPromptParser:
    """Test suite for PromptParser class."""

    def test_connect_and_pattern(self):
        """Test 'connect X and Y' pattern."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("connect a BME280 and an LED")

        assert result.devices == ["BME280", "LED"]
        assert result.board == "raspberry_pi_5"
        assert result.parsing_method == "regex"
        assert result.confidence == 0.9

    def test_connect_and_pattern_with_board(self):
        """Test 'connect X and Y' pattern with board mention."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("connect BME280 and LED to my Raspberry Pi 5")

        assert result.devices == ["BME280", "LED"]
        assert result.board == "raspberry_pi_5"
        assert result.parsing_method == "regex"

    def test_wire_to_pattern(self):
        """Test 'wire X to my pi' pattern."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("wire a BH1750 sensor to my pi")

        assert "BH1750 sensor" in result.devices
        assert result.board == "raspberry_pi_5"
        assert result.parsing_method == "regex"

    def test_comma_separated_pattern_two_devices(self):
        """Test 'X, Y' comma-separated pattern."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("DHT22, BME280")

        assert "DHT22" in result.devices
        assert "BME280" in result.devices
        assert len(result.devices) == 2
        assert result.parsing_method == "regex"

    def test_comma_separated_pattern_three_devices(self):
        """Test 'X, Y, and Z' comma-separated pattern."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("LED, button, and buzzer")

        assert "LED" in result.devices
        assert "button" in result.devices
        assert "buzzer" in result.devices
        assert len(result.devices) == 3
        assert result.parsing_method == "regex"

    def test_add_and_pattern(self):
        """Test 'add X and Y' pattern."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("add an OLED and a temperature sensor")

        assert "OLED" in result.devices
        assert "temperature sensor" in result.devices
        assert result.parsing_method == "regex"

    def test_show_with_pattern(self):
        """Test 'show me X with Y' pattern."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("show me a display with a sensor")

        assert "display" in result.devices
        assert "sensor" in result.devices
        assert result.parsing_method == "regex"

    def test_diagram_for_pattern(self):
        """Test 'diagram for X and Y' pattern."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("diagram for DHT22 and relay")

        assert "DHT22" in result.devices
        assert "relay" in result.devices
        assert result.parsing_method == "regex"

    def test_single_device_pattern(self):
        """Test single device mention."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("BME280")

        assert result.devices == ["BME280"]
        assert result.parsing_method == "regex"

    def test_single_device_with_connect(self):
        """Test 'connect X' pattern."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("connect LED")

        assert result.devices == ["LED"]
        assert result.parsing_method == "regex"

    def test_board_alias_pi5(self):
        """Test board alias 'pi5' recognition."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("connect LED to pi5")

        assert result.board == "raspberry_pi_5"

    def test_board_alias_rpi5(self):
        """Test board alias 'rpi5' recognition."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("wire BME280 to rpi5")

        assert result.board == "raspberry_pi_5"

    def test_clean_device_name_removes_articles(self):
        """Test that articles are removed from device names."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("connect the BME280 and an LED")

        assert "BME280" in result.devices
        assert "LED" in result.devices

    def test_case_insensitive_parsing(self):
        """Test that parsing is case-insensitive."""
        parser = PromptParser(use_llm=False)

        result1 = parser.parse("CONNECT BME280 AND LED")
        result2 = parser.parse("Connect BME280 and LED")
        result3 = parser.parse("connect bme280 and led")

        # Compare case-insensitively
        assert len(result1.devices) == len(result2.devices) == len(result3.devices)
        assert result1.devices[0].lower() == result2.devices[0].lower() == result3.devices[0].lower()
        assert result1.devices[1].lower() == result2.devices[1].lower() == result3.devices[1].lower()

    def test_no_match_without_llm(self):
        """Test that unrecognized prompts return empty result without LLM."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("This is a completely unrelated sentence")

        assert result.devices == []
        assert result.confidence == 0.0
        assert result.parsing_method == "failed"

    def test_convenience_function(self):
        """Test the convenience parse_prompt function."""
        result = parse_prompt("connect LED and button", use_llm=False)

        assert isinstance(result, ParsedPrompt)
        assert "LED" in result.devices
        assert "button" in result.devices

    def test_parser_requires_api_key_when_llm_enabled(self):
        """Test that API key is required when LLM is enabled."""
        import os

        # Save original env var
        original_key = os.environ.get("ANTHROPIC_API_KEY")

        try:
            # Remove API key
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]

            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                PromptParser(use_llm=True)

        finally:
            # Restore original env var
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key

    def test_parser_with_explicit_api_key(self):
        """Test parser initialization with explicit API key."""
        parser = PromptParser(use_llm=True, api_key="test-key")
        assert parser.api_key == "test-key"

    def test_complex_device_names(self):
        """Test parsing of complex device names."""
        parser = PromptParser(use_llm=False)
        result = parser.parse("connect HC-SR04 ultrasonic sensor and DS18B20")

        assert any("HC-SR04" in device for device in result.devices)
        assert any("DS18B20" in device for device in result.devices)

    def test_whitespace_handling(self):
        """Test that extra whitespace is handled correctly."""
        parser = PromptParser(use_llm=False)
        result1 = parser.parse("  connect   LED   and   button  ")
        result2 = parser.parse("connect LED and button")

        assert result1.devices == result2.devices

    @pytest.mark.parametrize(
        "prompt,expected_devices",
        [
            ("connect BME280 and LED", ["BME280", "LED"]),
            ("wire DHT22 to my pi", ["DHT22"]),
            ("LED, button, and buzzer", ["LED", "button", "buzzer"]),
            ("add OLED and relay", ["OLED", "relay"]),
            ("show me a display with a sensor", ["display", "sensor"]),
            ("diagram for motor and driver", ["motor", "driver"]),
            ("BH1750", ["BH1750"]),
        ],
    )
    def test_various_prompts(self, prompt, expected_devices):
        """Test various prompt formats with expected outputs."""
        parser = PromptParser(use_llm=False)
        result = parser.parse(prompt)

        for device in expected_devices:
            assert any(
                device.lower() in d.lower() for d in result.devices
            ), f"Expected {device} in {result.devices}"


class TestParsedPrompt:
    """Test suite for ParsedPrompt dataclass."""

    def test_parsed_prompt_creation(self):
        """Test creating a ParsedPrompt object."""
        prompt = ParsedPrompt(
            devices=["BME280", "LED"],
            board="raspberry_pi_5",
            requirements={"pull_ups": True},
            confidence=0.9,
            parsing_method="regex",
        )

        assert prompt.devices == ["BME280", "LED"]
        assert prompt.board == "raspberry_pi_5"
        assert prompt.requirements == {"pull_ups": True}
        assert prompt.confidence == 0.9
        assert prompt.parsing_method == "regex"

    def test_parsed_prompt_defaults(self):
        """Test default values for ParsedPrompt."""
        prompt = ParsedPrompt(devices=["LED"])

        assert prompt.board == "raspberry_pi_5"
        assert prompt.requirements is None
        assert prompt.confidence == 1.0
        assert prompt.parsing_method == "regex"
