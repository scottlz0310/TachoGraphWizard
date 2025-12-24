"""Export module for saving processed tachograph charts.

Provides functionality to export processed images as PNG with alpha channel
and generate appropriate filenames following naming conventions.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gimp, Gio, GObject

from tachograph_wizard.core.pdb_runner import run_pdb_procedure


class Exporter:
    """Export processed images to PNG with alpha channel."""

    @staticmethod
    def save_png(
        image: Gimp.Image,
        output_path: Path,
        flatten: bool = False,
    ) -> bool:
        """Save image as PNG with alpha channel.

        Args:
            image: Image to save.
            output_path: Output file path.
            flatten: Whether to flatten layers before saving.
                If False, merges visible layers instead.

        Returns:
            True if save was successful.

        Raises:
            RuntimeError: If save operation fails.
        """
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Flatten or merge layers
        if flatten:
            image.flatten()
        else:
            # Merge visible layers while preserving transparency
            image.merge_visible_layers(Gimp.MergeType.EXPAND_AS_NECESSARY)

        # Get the active drawable (layer)
        drawable = image.get_active_drawable()

        # Ensure alpha channel exists
        if not drawable.has_alpha():
            drawable.add_alpha()

        # Create Gio.File for the output path
        # IMPORTANT: Use forward slashes for cross-platform compatibility
        file_path_str = str(output_path).replace("\\", "/")
        file = Gio.File.new_for_path(file_path_str)

        # Save as PNG using GIMP 3 file save procedure
        try:
            # Get all drawables to export
            num_drawables, drawables = image.get_selected_drawables()

            result = run_pdb_procedure(
                "file-png-save",
                [
                    GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
                    GObject.Value(Gimp.Image, image),
                    GObject.Value(GObject.TYPE_INT, num_drawables),
                    Gimp.ValueArray.new_from_values(
                        [GObject.Value(Gimp.Drawable, d) for d in drawables],
                    ),
                    GObject.Value(Gio.File, file),
                ],
            )

            if result.index(0) != Gimp.PDBStatusType.SUCCESS:
                msg = f"Failed to save PNG: {output_path}"
                raise RuntimeError(msg)

            return True

        except Exception as e:
            msg = f"Error saving PNG: {e}"
            raise RuntimeError(msg) from e

    @staticmethod
    def generate_filename(
        date: datetime.date | None = None,
        vehicle_number: str = "",
        driver_name: str = "",
        extension: str = "png",
    ) -> str:
        """Generate filename following naming convention.

        Format: YYYYMMDD_車番_運転手.png
        Example: 20250101_123_TaroYamada.png

        Args:
            date: Date for the filename (default: today).
            vehicle_number: Vehicle number to include.
            driver_name: Driver name to include.
            extension: File extension (default: 'png').

        Returns:
            Generated filename string.
        """
        if date is None:
            date = datetime.date.today()

        date_str = date.strftime("%Y%m%d")
        parts = [date_str]

        if vehicle_number:
            # Sanitize vehicle number (replace spaces with underscores)
            vehicle_clean = vehicle_number.replace(" ", "_").replace("/", "-")
            parts.append(vehicle_clean)

        if driver_name:
            # Sanitize driver name (remove spaces and special characters)
            driver_clean = (
                driver_name.replace(" ", "")
                .replace("　", "")  # Remove full-width space
                .replace("/", "-")
                .replace("\\", "-")
            )
            parts.append(driver_clean)

        filename = "_".join(parts) + f".{extension}"
        return filename

    @staticmethod
    def save_with_naming_convention(
        image: Gimp.Image,
        output_directory: Path,
        date: datetime.date | None = None,
        vehicle_number: str = "",
        driver_name: str = "",
        flatten: bool = False,
    ) -> Path:
        """Save image with automatic filename generation.

        Combines filename generation and save operations for convenience.

        Args:
            image: Image to save.
            output_directory: Directory to save the file in.
            date: Date for filename (default: today).
            vehicle_number: Vehicle number for filename.
            driver_name: Driver name for filename.
            flatten: Whether to flatten layers before saving.

        Returns:
            Path to the saved file.

        Raises:
            RuntimeError: If save operation fails.
        """
        filename = Exporter.generate_filename(
            date=date,
            vehicle_number=vehicle_number,
            driver_name=driver_name,
        )

        output_path = output_directory / filename

        Exporter.save_png(image, output_path, flatten)

        return output_path
