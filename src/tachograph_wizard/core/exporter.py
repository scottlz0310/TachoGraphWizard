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
    def _is_success_status(result: object) -> bool:
        if result is None:
            return False
        if isinstance(result, bool):
            return result
        try:
            success_value = int(Gimp.PDBStatusType.SUCCESS)
        except Exception:
            success_value = Gimp.PDBStatusType.SUCCESS

        if isinstance(result, int):
            return result == success_value

        if isinstance(result, (list, tuple)) and result:
            return Exporter._is_success_status(result[0])

        index = getattr(result, "index", None)
        if callable(index):
            try:
                return index(0) == Gimp.PDBStatusType.SUCCESS
            except Exception:
                return False

        return False

    @staticmethod
    def _try_file_api_save(
        image: Gimp.Image,
        drawables_list: list[Gimp.Drawable],
        file: Gio.File,
    ) -> bool:
        save_fn = getattr(Gimp, "file_save", None)
        if callable(save_fn):
            try:
                result = save_fn(
                    Gimp.RunMode.NONINTERACTIVE,
                    image,
                    drawables_list,
                    file,
                )
                if Exporter._is_success_status(result):
                    return True
            except Exception:
                # Gimp.file_save may not be available or may fail; try next fallback
                pass

        export_fn = getattr(Gimp, "file_export", None)
        if callable(export_fn):
            try:
                result = export_fn(
                    Gimp.RunMode.NONINTERACTIVE,
                    image,
                    drawables_list,
                    file,
                )
                if Exporter._is_success_status(result):
                    return True
            except Exception:
                # Gimp.file_export may not be available or may fail; continue
                pass

        return False

    @staticmethod
    def _get_fallback_drawable(image: Gimp.Image) -> Gimp.Drawable | None:
        active_getters = ("get_active_drawable", "get_active_layer")
        for method_name in active_getters:
            getter = getattr(image, method_name, None)
            if callable(getter):
                try:
                    drawable = getter()
                except Exception:
                    drawable = None
                if drawable is not None:
                    return drawable

        layers_getter = getattr(image, "get_layers", None)
        if callable(layers_getter):
            try:
                layers = layers_getter()
            except Exception:
                layers = None
            if isinstance(layers, (list, tuple)) and layers:
                return layers[0]

        return None

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
            # Flatten image; this may not preserve existing transparency depending on image mode
            merged_drawable = image.flatten()
        else:
            # Merge visible layers while preserving transparency
            merged_drawable = image.merge_visible_layers(Gimp.MergeType.EXPAND_AS_NECESSARY)

        # Create Gio.File for the output path
        # IMPORTANT: Use forward slashes for cross-platform compatibility
        file_path_str = str(output_path).replace("\\", "/")
        file = Gio.File.new_for_path(file_path_str)

        # Save as PNG using GIMP 3 file save procedure
        try:
            # Get all drawables to export
            get_selected_drawables = getattr(image, "get_selected_drawables", None)
            if callable(get_selected_drawables):
                result = get_selected_drawables()
                if isinstance(result, tuple) and len(result) == 2:
                    num_drawables, drawables = result
                else:
                    num_drawables, drawables = 0, []
            else:
                num_drawables, drawables = 0, []

            drawables_list: list[Gimp.Drawable] = []
            if isinstance(drawables, (list, tuple)):
                drawables_list = list(drawables)
            elif drawables:
                drawables_list = [drawables]

            try:
                num_drawables = int(num_drawables)
            except Exception:
                num_drawables = len(drawables_list)

            if (not drawables_list) or (num_drawables <= 0):
                drawable = merged_drawable or Exporter._get_fallback_drawable(image)
                if drawable is None:
                    msg = "No drawable available for PNG export"
                    raise RuntimeError(msg)
                drawables_list = [drawable]
                num_drawables = 1

            # Ensure alpha channel exists
            for drawable in drawables_list:
                if not drawable.has_alpha():
                    drawable.add_alpha()

            if Exporter._try_file_api_save(image, drawables_list, file):
                return True

            last_error: Exception | None = None
            for proc_name in ("file-png-save", "file-png-export"):
                try:
                    result = run_pdb_procedure(
                        proc_name,
                        [
                            GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
                            GObject.Value(Gimp.Image, image),
                            GObject.Value(GObject.TYPE_INT, num_drawables),
                            Gimp.ValueArray.new_from_values(
                                [GObject.Value(Gimp.Drawable, d) for d in drawables_list],
                            ),
                            GObject.Value(Gio.File, file),
                        ],
                    )
                    if Exporter._is_success_status(result):
                        return True
                except Exception as e:
                    last_error = e

            msg = f"Failed to save PNG: {output_path}"
            raise RuntimeError(msg) from last_error

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
