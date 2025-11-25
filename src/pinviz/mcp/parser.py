"""
Natural Language Prompt Parser for PinViz MCP Server.

This module parses natural language prompts to extract structured data needed for
generating wiring diagrams using regex patterns for common prompt formats.

The client's LLM handles complex interpretation - this parser just extracts
device names and board types from structured prompts.
"""

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ParsedPrompt:
    """Structured data extracted from a natural language prompt."""

    devices: list[str]  # List of device names/IDs
    board: str = "raspberry_pi_5"  # Default board type
    requirements: dict[str, Any] | None = None  # Special requirements (pull-ups, etc.)
    confidence: float = 1.0  # Confidence score (0.0-1.0)
    parsing_method: str = "regex"  # "regex" or "llm"


class PromptParser:
    """
    Hybrid parser for natural language prompts.

    Uses regex patterns for 80% of common cases, falls back to Claude API
    for complex/ambiguous prompts.
    """

    # Regex patterns for common prompt formats
    PATTERNS = [
        # Pattern: "connect device1 and device2 [to my pi]"
        (
            re.compile(
                r"connect\s+(?:a\s+)?(?:an\s+)?(.+?)\s+and\s+(?:a\s+)?(?:an\s+)?([^,\s]+(?:\s+[^,\s]+)*?)(?:\s+to\s+(?:my\s+)?(?:raspberry\s+)?pi.*?)?$",
                re.IGNORECASE,
            ),
            "connect_and",
        ),
        # Pattern: "wire device to my pi"
        (
            re.compile(
                r"wire\s+(?:a\s+)?(?:an\s+)?(.+?)\s+to\s+(?:my\s+)?(?:raspberry\s+)?pi",
                re.IGNORECASE,
            ),
            "wire_to",
        ),
        # Pattern: "device1, device2, and device3"
        (
            re.compile(
                r"^(.+?),\s*(.+?)(?:,?\s+and\s+(.+?))?$",
                re.IGNORECASE,
            ),
            "comma_separated",
        ),
        # Pattern: "add device1 and device2"
        (
            re.compile(
                r"add\s+(?:a\s+)?(?:an\s+)?(.+?)\s+and\s+(?:a\s+)?(?:an\s+)?(.+?)$",
                re.IGNORECASE,
            ),
            "add_and",
        ),
        # Pattern: "show me device1 with device2"
        (
            re.compile(
                r"show\s+(?:me\s+)?(?:a\s+)?(.+?)\s+with\s+(?:a\s+)?(.+?)$",
                re.IGNORECASE,
            ),
            "show_with",
        ),
        # Pattern: "diagram for device1 and device2"
        (
            re.compile(
                r"diagram\s+for\s+(?:a\s+)?(.+?)\s+and\s+(?:a\s+)?(.+?)$",
                re.IGNORECASE,
            ),
            "diagram_for",
        ),
        # Pattern: single device mention
        # (must start with known action word or be simple device name)
        (
            re.compile(
                r"^(?:connect|wire|add|show)\s+(?:a\s+)?(?:an\s+)?([A-Za-z0-9_-]+(?:\s+[A-Za-z0-9_-]+){0,3})(?:\s+to\s+(?:my\s+)?(?:raspberry\s+)?pi.*?)?$",
                re.IGNORECASE,
            ),
            "single_device_action",
        ),
        # Pattern: bare device name (simple alphanumeric, max 4 words)
        (
            re.compile(
                r"^([A-Za-z0-9_-]+(?:\s+[A-Za-z0-9_-]+){0,3})$",
                re.IGNORECASE,
            ),
            "single_device",
        ),
    ]

    # Board aliases mapping
    BOARD_ALIASES = {
        # Raspberry Pi 5
        "rpi5": "raspberry_pi_5",
        "rpi 5": "raspberry_pi_5",
        "raspberry pi 5": "raspberry_pi_5",
        "raspberry_pi_5": "raspberry_pi_5",
        "pi 5": "raspberry_pi_5",
        "pi5": "raspberry_pi_5",
        # Raspberry Pi Zero / Zero 2 W
        "raspberry_pi_zero_2w": "raspberry_pi_zero_2w",
        "raspberry_pi_zero": "raspberry_pi_zero_2w",
        "raspberry pi zero": "raspberry_pi_zero_2w",
        "raspberry pi zero 2": "raspberry_pi_zero_2w",
        "raspberry pi zero 2w": "raspberry_pi_zero_2w",
        "pizero": "raspberry_pi_zero_2w",
        "pi zero": "raspberry_pi_zero_2w",
        "zero2w": "raspberry_pi_zero_2w",
        "zero 2w": "raspberry_pi_zero_2w",
        "zero": "raspberry_pi_zero_2w",
        "rpizero": "raspberry_pi_zero_2w",
        "rpi zero": "raspberry_pi_zero_2w",
    }

    def __init__(self, use_llm: bool = False):
        """
        Initialize the parser.

        Args:
            use_llm: Whether to use LLM fallback for complex prompts (not yet implemented)
        """
        self.use_llm = use_llm

    def parse(self, prompt: str) -> ParsedPrompt:
        """
        Parse a natural language prompt to extract structured data.

        Args:
            prompt: Natural language prompt from user

        Returns:
            ParsedPrompt object with extracted data
        """
        # Clean the prompt
        prompt = prompt.strip()

        # Try regex patterns
        for pattern, pattern_type in self.PATTERNS:
            match = pattern.match(prompt)
            if match:
                return self._parse_with_regex(match, pattern_type)

        # If no regex match, return empty result
        # The client's LLM can handle interpretation if needed
        return ParsedPrompt(
            devices=[],
            confidence=0.0,
            parsing_method="no_match",
        )

    def _parse_with_regex(self, match: re.Match, pattern_type: str) -> ParsedPrompt:
        """Parse prompt using regex match."""
        devices = []

        if pattern_type in ("connect_and", "add_and", "wire_to", "show_with", "diagram_for"):
            # Extract device names from groups
            devices = [self._clean_device_name(match.group(1))]
            if match.lastindex >= 2 and match.group(2):
                devices.append(self._clean_device_name(match.group(2)))

        elif pattern_type == "comma_separated":
            # Extract all comma-separated devices
            for i in range(1, match.lastindex + 1):
                device = match.group(i)
                if device:
                    devices.append(self._clean_device_name(device))

        elif pattern_type in ("single_device", "single_device_action"):
            devices = [self._clean_device_name(match.group(1))]

        # Extract board type from prompt if mentioned
        board = self._extract_board_type(match.string)

        return ParsedPrompt(
            devices=devices,
            board=board,
            confidence=0.9,  # High confidence for regex matches
            parsing_method="regex",
        )

    def _clean_device_name(self, name: str) -> str:
        """Clean and normalize device name."""
        # Remove articles
        name = re.sub(r"^(a|an|the)\s+", "", name, flags=re.IGNORECASE)
        # Remove trailing words like "sensor", "module"
        # (but keep them if they're part of the device name)
        name = name.strip()
        return name

    def _extract_board_type(self, prompt: str) -> str:
        """Extract board type from prompt, return default if not found."""
        prompt_lower = prompt.lower()

        for alias, board_name in self.BOARD_ALIASES.items():
            if alias in prompt_lower:
                return board_name

        return "raspberry_pi_5"  # Default


def parse_prompt(prompt: str) -> ParsedPrompt:
    """
    Convenience function to parse a prompt using regex patterns.

    Args:
        prompt: Natural language prompt

    Returns:
        ParsedPrompt object
    """
    parser = PromptParser()
    return parser.parse(prompt)
