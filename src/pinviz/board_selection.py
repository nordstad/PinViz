"""Board selection strategies shared across config and MCP flows."""

from dataclasses import dataclass
from typing import Protocol

from . import boards
from .model import Board

BOARD_LOADERS = {
    # Raspberry Pi 5
    "raspberry_pi_5": boards.raspberry_pi_5,
    "rpi5": boards.raspberry_pi_5,
    # Raspberry Pi 4
    "raspberry_pi_4": boards.raspberry_pi_4,
    "rpi4": boards.raspberry_pi_4,
    "pi4": boards.raspberry_pi_4,
    # Raspberry Pi Pico
    "raspberry_pi_pico": boards.raspberry_pi_pico,
    "pico": boards.raspberry_pi_pico,
    # ESP32 DevKit V1
    "esp32_devkit_v1": boards.esp32_devkit_v1,
    "esp32": boards.esp32_devkit_v1,
    "esp32dev": boards.esp32_devkit_v1,
    "esp32_devkit": boards.esp32_devkit_v1,
    # Wemos D1 Mini
    "wemos_d1_mini": boards.wemos_d1_mini,
    "d1mini": boards.wemos_d1_mini,
    "d1_mini": boards.wemos_d1_mini,
    "wemos": boards.wemos_d1_mini,
    # ESP8266 NodeMCU
    "esp8266_nodemcu": boards.esp8266_nodemcu,
    "esp8266": boards.esp8266_nodemcu,
    "nodemcu": boards.esp8266_nodemcu,
    # Aliases
    "raspberry_pi": boards.raspberry_pi,
    "rpi": boards.raspberry_pi,
}


class BoardSelectionStrategy(Protocol):
    """Strategy interface for resolving board names to board instances."""

    def select_board(self, board_name: str) -> Board:
        """Resolve a board name to a board instance."""


@dataclass(frozen=True)
class AliasBoardSelectionStrategy:
    """Resolve boards from a shared alias table.

    When ``fallback_board_name`` is set, unknown names fall back to that board.
    Otherwise an unknown board raises ``ValueError``.
    """

    fallback_board_name: str | None = None

    def select_board(self, board_name: str) -> Board:
        normalized = board_name.lower()
        loader = BOARD_LOADERS.get(normalized)

        if loader is None:
            if self.fallback_board_name is None:
                raise ValueError(f"Unknown board: {board_name}")

            loader = BOARD_LOADERS[self.fallback_board_name.lower()]

        return loader()
