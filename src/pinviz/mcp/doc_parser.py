"""
URL-Based Device Documentation Parser for PinViz MCP Server.

This module fetches device documentation from URLs (datasheets, product pages)
and extracts device specifications using Claude API for automatic device registration.
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

import httpx
from anthropic import Anthropic
from bs4 import BeautifulSoup


@dataclass
class ExtractedDevice:
    """Device specification extracted from documentation."""

    # Required fields
    name: str
    category: str
    description: str
    pins: list[dict[str, Any]]
    protocols: list[str]
    voltage: str

    # Optional fields
    manufacturer: str | None = None
    datasheet_url: str | None = None
    i2c_address: str | None = None
    i2c_addresses: list[str] = field(default_factory=list)
    current_draw: str | None = None
    dimensions: dict[str, Any] | None = None
    tags: list[str] = field(default_factory=list)
    notes: str | None = None
    requires_pullup: bool = False

    # Metadata
    confidence: float = 0.8
    extraction_method: str = "llm"
    missing_fields: list[str] = field(default_factory=list)


class DocumentationParser:
    """
    Parser for device documentation from URLs.

    Fetches content from URLs and uses Claude API to extract device specifications
    from datasheets, product pages, and technical documentation.
    """

    # Supported URL patterns
    SUPPORTED_DOMAINS = [
        "adafruit.com",
        "sparkfun.com",
        "waveshare.com",
        "pimoroni.com",
        "raspberrypi.com",
        "seeedstudio.com",
    ]

    # Default timeout for HTTP requests (seconds)
    TIMEOUT = 30.0

    # Max content length to send to Claude (characters)
    MAX_CONTENT_LENGTH = 50000

    def __init__(self, api_key: str | None = None):
        """
        Initialize the documentation parser.

        Args:
            api_key: Anthropic API key (if None, uses ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

        self.client = Anthropic(api_key=self.api_key)

    async def parse_url(self, url: str) -> ExtractedDevice:
        """
        Parse device documentation from a URL.

        Args:
            url: URL to device documentation (datasheet, product page, etc.)

        Returns:
            ExtractedDevice with specifications extracted from the documentation

        Raises:
            ValueError: If URL is not supported or content cannot be fetched
        """
        # Validate URL
        if not self._is_supported_url(url):
            raise ValueError(
                f"URL domain not in supported list: {', '.join(self.SUPPORTED_DOMAINS)}"
            )

        # Fetch content
        content = await self._fetch_url_content(url)

        # Extract device specs using Claude
        device = await self._extract_device_specs(content, url)

        return device

    def parse_url_sync(self, url: str) -> ExtractedDevice:
        """
        Synchronous version of parse_url.

        Args:
            url: URL to device documentation

        Returns:
            ExtractedDevice with specifications
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.parse_url(url))

    def _is_supported_url(self, url: str) -> bool:
        """Check if URL is from a supported domain."""
        url_lower = url.lower()
        return any(domain in url_lower for domain in self.SUPPORTED_DOMAINS)

    async def _fetch_url_content(self, url: str) -> str:
        """
        Fetch and extract text content from a URL.

        Args:
            url: URL to fetch

        Returns:
            Extracted text content from the page

        Raises:
            ValueError: If content cannot be fetched
        """
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")

                # Remove script and style elements
                for element in soup(["script", "style", "nav", "footer", "header"]):
                    element.decompose()

                # Get text content
                text = soup.get_text(separator="\n", strip=True)

                # Clean up whitespace
                text = re.sub(r"\n\s*\n+", "\n\n", text)

                # Truncate if too long
                if len(text) > self.MAX_CONTENT_LENGTH:
                    text = text[: self.MAX_CONTENT_LENGTH] + "\n\n[Content truncated...]"

                return text

        except httpx.HTTPStatusError as e:
            raise ValueError(f"HTTP error fetching URL: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ValueError(f"Error fetching URL: {e!s}") from e
        except Exception as e:
            raise ValueError(f"Error parsing HTML: {e!s}") from e

    async def _extract_device_specs(self, content: str, source_url: str) -> ExtractedDevice:
        """
        Extract device specifications from documentation content using Claude.

        Args:
            content: Text content from documentation
            source_url: Original URL for reference

        Returns:
            ExtractedDevice with extracted specifications
        """
        # Create structured prompt for Claude
        system_prompt = """You are an expert at extracting device specifications from \
datasheets and product documentation.

Extract the following information about the electronic device/module from the documentation:

REQUIRED FIELDS:
1. name: Device/module name (e.g., "BME280", "SSD1306 OLED Display")
2. category: One of: display, sensor, hat, component, actuator, breakout
3. description: Brief description (1-2 sentences)
4. pins: Array of pin definitions with:
   - name: Pin label (VCC, GND, SDA, SCL, etc.)
   - role: One of: 3V3, 5V, GND, I2C_SDA, I2C_SCL, SPI_MOSI, SPI_MISO, SPI_SCLK, SPI_CS, \
UART_TX, UART_RX, GPIO, PWM, 1-Wire, SIGNAL, DATA
   - position: Integer (0-based index, left to right or top to bottom)
   - optional: Boolean (is this pin optional?)
5. protocols: Array of protocols (I2C, SPI, UART, GPIO, 1-Wire, PWM)
6. voltage: One of: "3.3V", "5V", "3.3V-5V"

OPTIONAL FIELDS:
7. manufacturer: Company name
8. i2c_address: Hex format (e.g., "0x23") if device uses I2C
9. i2c_addresses: Array of alternate I2C addresses if configurable
10. current_draw: Typical current (e.g., "50mA", "3.5mA")
11. dimensions: {width: number, height: number, unit: "mm" or "in"}
12. tags: Array of search keywords
13. notes: Important notes, requirements, or warnings
14. requires_pullup: Boolean (true if I2C device needs external pull-ups)

Respond ONLY with valid JSON in this exact format:
{
  "name": "Device Name",
  "category": "sensor",
  "description": "Brief description",
  "manufacturer": "Company Name",
  "pins": [
    {"name": "VCC", "role": "3V3", "position": 0},
    {"name": "GND", "role": "GND", "position": 1},
    {"name": "SDA", "role": "I2C_SDA", "position": 2},
    {"name": "SCL", "role": "I2C_SCL", "position": 3}
  ],
  "protocols": ["I2C"],
  "i2c_address": "0x23",
  "voltage": "3.3V",
  "current_draw": "50mA",
  "tags": ["light", "ambient", "lux"],
  "requires_pullup": false,
  "notes": "Any important notes"
}

If information is missing, omit the optional field from your response.
Be precise with pin roles - use the exact enum values listed above."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Extract device specifications from this documentation:\n\n{content}"
                        ),
                    }
                ],
                system=system_prompt,
            )

            # Extract text content from response
            content_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content_text += block.text

            # Parse JSON response
            specs = json.loads(content_text)

            # Validate required fields
            required_fields = ["name", "category", "description", "pins", "protocols", "voltage"]
            missing_fields = [field for field in required_fields if field not in specs]

            # Create ExtractedDevice
            device = ExtractedDevice(
                name=specs.get("name", "Unknown Device"),
                category=specs.get("category", "component"),
                description=specs.get("description", ""),
                pins=specs.get("pins", []),
                protocols=specs.get("protocols", ["GPIO"]),
                voltage=specs.get("voltage", "3.3V"),
                manufacturer=specs.get("manufacturer"),
                datasheet_url=source_url,
                i2c_address=specs.get("i2c_address"),
                i2c_addresses=specs.get("i2c_addresses", []),
                current_draw=specs.get("current_draw"),
                dimensions=specs.get("dimensions"),
                tags=specs.get("tags", []),
                notes=specs.get("notes"),
                requires_pullup=specs.get("requires_pullup", False),
                confidence=0.85 if not missing_fields else 0.6,
                extraction_method="llm",
                missing_fields=missing_fields,
            )

            return device

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Claude response as JSON: {e!s}") from e
        except Exception as e:
            raise ValueError(f"Error extracting device specs: {e!s}") from e

    def _generate_device_id(self, name: str) -> str:
        """Generate a device ID from the device name."""
        # Convert to lowercase, replace spaces/underscores with hyphens
        device_id = name.lower()
        device_id = re.sub(r"[\s_]+", "-", device_id)
        # Remove non-alphanumeric characters except hyphens
        device_id = re.sub(r"[^a-z0-9-]", "", device_id)
        # Remove multiple consecutive hyphens
        device_id = re.sub(r"-+", "-", device_id)
        # Remove leading/trailing hyphens
        device_id = device_id.strip("-")
        return device_id

    def to_device_entry(self, extracted: ExtractedDevice) -> dict[str, Any]:
        """
        Convert ExtractedDevice to a device database entry.

        Args:
            extracted: Extracted device specifications

        Returns:
            Dictionary in the format expected by device database schema
        """
        device_id = self._generate_device_id(extracted.name)

        entry = {
            "id": device_id,
            "name": extracted.name,
            "category": extracted.category,
            "description": extracted.description,
            "pins": extracted.pins,
            "protocols": extracted.protocols,
            "voltage": extracted.voltage,
        }

        # Add optional fields if present
        if extracted.manufacturer:
            entry["manufacturer"] = extracted.manufacturer
        if extracted.datasheet_url:
            entry["datasheet_url"] = extracted.datasheet_url
        if extracted.i2c_address:
            entry["i2c_address"] = extracted.i2c_address
        if extracted.i2c_addresses:
            entry["i2c_addresses"] = extracted.i2c_addresses
        if extracted.current_draw:
            entry["current_draw"] = extracted.current_draw
        if extracted.dimensions:
            entry["dimensions"] = extracted.dimensions
        if extracted.tags:
            entry["tags"] = extracted.tags
        if extracted.notes:
            entry["notes"] = extracted.notes
        if extracted.requires_pullup:
            entry["requires_pullup"] = extracted.requires_pullup

        return entry

    def validate_device_entry(self, device_entry: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate a device entry against the JSON schema.

        Args:
            device_entry: Device entry dictionary to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Validate required fields
        required_fields = ["id", "name", "category", "description", "pins", "protocols", "voltage"]
        for field_name in required_fields:
            if field_name not in device_entry:
                errors.append(f"Missing required field: {field_name}")

        # Validate ID format (lowercase, hyphenated)
        if "id" in device_entry:
            device_id = device_entry["id"]
            if not re.match(r"^[a-z0-9-]+$", device_id):
                errors.append(f"Invalid ID format: {device_id} (must be lowercase, hyphenated)")

        # Validate category
        valid_categories = ["display", "sensor", "hat", "component", "actuator", "breakout"]
        if "category" in device_entry and device_entry["category"] not in valid_categories:
            errors.append(
                f"Invalid category: {device_entry['category']} "
                f"(must be one of {', '.join(valid_categories)})"
            )

        # Validate pins
        if "pins" in device_entry:
            pins = device_entry["pins"]
            if not isinstance(pins, list):
                errors.append("Pins must be an array")
            else:
                valid_roles = [
                    "3V3",
                    "5V",
                    "GND",
                    "I2C_SDA",
                    "I2C_SCL",
                    "SPI_MOSI",
                    "SPI_MISO",
                    "SPI_SCLK",
                    "SPI_CS",
                    "UART_TX",
                    "UART_RX",
                    "GPIO",
                    "PWM",
                    "1-Wire",
                    "SIGNAL",
                    "DATA",
                ]
                for i, pin in enumerate(pins):
                    if not isinstance(pin, dict):
                        errors.append(f"Pin {i} must be an object")
                        continue
                    if "name" not in pin:
                        errors.append(f"Pin {i} missing required field: name")
                    if "role" not in pin:
                        errors.append(f"Pin {i} missing required field: role")
                    elif pin["role"] not in valid_roles:
                        errors.append(
                            f"Pin {i} has invalid role: {pin['role']} "
                            f"(must be one of {', '.join(valid_roles)})"
                        )
                    if "position" not in pin:
                        errors.append(f"Pin {i} missing required field: position")
                    elif not isinstance(pin["position"], int) or pin["position"] < 0:
                        errors.append(f"Pin {i} position must be a non-negative integer")

        # Validate protocols
        valid_protocols = ["I2C", "SPI", "UART", "GPIO", "1-Wire", "PWM"]
        if "protocols" in device_entry:
            protocols = device_entry["protocols"]
            if not isinstance(protocols, list) or not protocols:
                errors.append("Protocols must be a non-empty array")
            else:
                for protocol in protocols:
                    if protocol not in valid_protocols:
                        errors.append(
                            f"Invalid protocol: {protocol} "
                            f"(must be one of {', '.join(valid_protocols)})"
                        )

        # Validate voltage
        valid_voltages = ["3.3V", "5V", "3.3V-5V"]
        if "voltage" in device_entry and device_entry["voltage"] not in valid_voltages:
            errors.append(
                f"Invalid voltage: {device_entry['voltage']} "
                f"(must be one of {', '.join(valid_voltages)})"
            )

        # Validate I2C address format
        if "i2c_address" in device_entry and not re.match(
            r"^0x[0-9A-Fa-f]{2}$", device_entry["i2c_address"]
        ):
            errors.append(
                f"Invalid I2C address format: {device_entry['i2c_address']} "
                "(must be in format 0xNN)"
            )

        # Validate I2C addresses array
        if "i2c_addresses" in device_entry:
            for addr in device_entry["i2c_addresses"]:
                if not re.match(r"^0x[0-9A-Fa-f]{2}$", addr):
                    errors.append(f"Invalid I2C address format in array: {addr} (must be 0xNN)")

        return (len(errors) == 0, errors)


def parse_device_from_url(url: str, api_key: str | None = None) -> ExtractedDevice:
    """
    Convenience function to parse device from a URL.

    Args:
        url: URL to device documentation
        api_key: Anthropic API key (optional)

    Returns:
        ExtractedDevice with specifications
    """
    parser = DocumentationParser(api_key=api_key)
    return parser.parse_url_sync(url)
