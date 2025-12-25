"""Data models for text field templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class FontConfig:
    """Font configuration for a text field."""

    family: str = "Arial"
    size_ratio: float = 0.03  # Font size as ratio of image's shorter side
    color: str = "#000000"  # Hex color
    bold: bool = False
    italic: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FontConfig:
        """Create FontConfig from dictionary.

        Args:
            data: Dictionary containing font configuration.

        Returns:
            FontConfig instance.
        """
        return cls(
            family=data.get("family", "Arial"),
            size_ratio=float(data.get("size_ratio", 0.03)),
            color=data.get("color", "#000000"),
            bold=bool(data.get("bold", False)),
            italic=bool(data.get("italic", False)),
        )


@dataclass
class PositionConfig:
    """Position configuration for a text field."""

    x_ratio: float = 0.0  # X position as ratio of image width (0.0-1.0)
    y_ratio: float = 0.0  # Y position as ratio of image height (0.0-1.0)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PositionConfig:
        """Create PositionConfig from dictionary.

        Args:
            data: Dictionary containing position configuration.

        Returns:
            PositionConfig instance.
        """
        return cls(
            x_ratio=float(data.get("x_ratio", 0.0)),
            y_ratio=float(data.get("y_ratio", 0.0)),
        )


@dataclass
class TextField:
    """Configuration for a single text field."""

    position: PositionConfig
    font: FontConfig
    align: Literal["left", "center", "right"] = "left"
    vertical_align: Literal["top", "middle", "bottom"] = "top"
    visible: bool = True
    required: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TextField:
        """Create TextField from dictionary.

        Args:
            data: Dictionary containing field configuration.

        Returns:
            TextField instance.
        """
        return cls(
            position=PositionConfig.from_dict(data.get("position", {})),
            font=FontConfig.from_dict(data.get("font", {})),
            align=data.get("align", "left"),  # type: ignore[arg-type]
            vertical_align=data.get("vertical_align", "top"),  # type: ignore[arg-type]
            visible=bool(data.get("visible", True)),
            required=bool(data.get("required", False)),
        )


@dataclass
class Template:
    """Template containing all field configurations."""

    name: str
    version: str
    description: str
    reference_width: int
    reference_height: int
    fields: dict[str, TextField] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Template:
        """Create Template from dictionary.

        Args:
            data: Dictionary containing template configuration.

        Returns:
            Template instance.
        """
        fields_data = data.get("fields", {})
        fields = {name: TextField.from_dict(field_data) for name, field_data in fields_data.items()}

        return cls(
            name=data.get("name", "Untitled"),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            reference_width=int(data.get("reference_width", 1000)),
            reference_height=int(data.get("reference_height", 1000)),
            fields=fields,
        )
