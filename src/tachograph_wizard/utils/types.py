"""Type definitions for TachoGraphWizard.

This module contains TypedDict definitions and type aliases for use
throughout the project, ensuring strict type checking compliance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from gi.repository import Gimp


class TemplateField(TypedDict):
    """Text field configuration in a template.

    Attributes:
        name: Field identifier (e.g., 'driver', 'vehicle', 'machine')
        label: Display label for the field
        x: X coordinate for text placement
        y: Y coordinate for text placement
        font: Font family name
        size: Font size in pixels
        color: Text color in hex format (optional)
    """

    name: str
    label: str
    x: float
    y: float
    font: str
    size: float
    color: str | None


class TemplateConfig(TypedDict):
    """Template configuration structure.

    Attributes:
        id: Unique template identifier
        name: Human-readable template name
        description: Template description
        file: Path to XCF template file
        fields: List of text field configurations
    """

    id: str
    name: str
    description: str
    file: str
    fields: list[TemplateField]


class SplitResult(TypedDict):
    """Result from image splitting operation.

    Attributes:
        images: List of split images
        method: Splitting method used ('guides' or 'auto')
    """

    images: list[Gimp.Image]
    method: str


class ProcessingSettings(TypedDict):
    """User settings for processing workflow.

    Attributes:
        split_method: Method for splitting ('guides' or 'auto')
        transparency_threshold: Threshold for color-to-alpha (0-100)
        rotation_angle: Rotation angle in degrees
        template_name: Selected template ID
        driver_name: Driver name for text annotation
        vehicle_number: Vehicle number for text annotation
        machine_name: Machine name for text annotation
        output_directory: Output directory path
    """

    split_method: str
    transparency_threshold: float
    rotation_angle: float
    template_name: str
    driver_name: str
    vehicle_number: str
    machine_name: str
    output_directory: str
