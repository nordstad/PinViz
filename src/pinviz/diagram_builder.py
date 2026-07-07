"""Shared builder for assembling Diagram objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from .board_selection import AliasBoardSelectionStrategy, BoardSelectionStrategy
from .model import Board, Connection, Device, Diagram
from .theme import Theme


@dataclass(frozen=True)
class DiagramOptions:
    """Presentation options applied when constructing a diagram."""

    show_legend: bool = False
    show_gpio_diagram: bool = False
    show_title: bool = True
    show_board_name: bool = True
    theme: Theme = Theme.LIGHT


class DiagramBuilder:
    """Small step-by-step builder shared by config and MCP flows."""

    def __init__(self, board_selection_strategy: BoardSelectionStrategy | None = None):
        self._board_selection_strategy = board_selection_strategy or AliasBoardSelectionStrategy()
        self._reset()

    def _reset(self) -> None:
        self._title = "GPIO Diagram"
        self._board: Board | None = None
        self._devices: list[Device] = []
        self._connections: list[Connection] = []
        self._options = DiagramOptions()

    def with_title(self, title: str) -> Self:
        self._title = title
        return self

    def with_board(self, board: Board) -> Self:
        self._board = board
        return self

    def with_board_name(self, board_name: str) -> Self:
        self._board = self._board_selection_strategy.select_board(board_name)
        return self

    def with_devices(self, devices: list[Device]) -> Self:
        self._devices = list(devices)
        return self

    def with_connections(self, connections: list[Connection]) -> Self:
        self._connections = list(connections)
        return self

    def with_options(self, options: DiagramOptions) -> Self:
        self._options = options
        return self

    def build(self) -> Diagram:
        if self._board is None:
            raise ValueError("DiagramBuilder requires a board before build()")

        diagram = Diagram(
            title=self._title,
            board=self._board,
            devices=list(self._devices),
            connections=list(self._connections),
            show_legend=self._options.show_legend,
            show_gpio_diagram=self._options.show_gpio_diagram,
            show_title=self._options.show_title,
            show_board_name=self._options.show_board_name,
            theme=self._options.theme,
        )
        self._reset()
        return diagram
