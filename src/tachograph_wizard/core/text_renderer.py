"""Text renderer for creating and positioning text layers in GIMP."""

from __future__ import annotations

import datetime
import os
from pathlib import Path
from typing import TYPE_CHECKING

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")

from gi.repository import Gegl, Gimp, GObject

from tachograph_wizard.core.pdb_runner import run_pdb_procedure

if TYPE_CHECKING:
    from tachograph_wizard.templates.models import Template, TextField


def _debug_log(message: str) -> None:
    """Write debug message to log file."""
    try:
        base = os.environ.get("TEMP") or os.environ.get("TMP") or os.environ.get("LOCALAPPDATA")
        if not base:
            return
        log_path = Path(base) / "tachograph_wizard.log"
        ts = datetime.datetime.now(tz=datetime.UTC).isoformat(timespec="seconds")
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{ts}] text_renderer: {message}\n")
    except Exception:
        return


class TextRenderer:
    """Renders text on GIMP images according to template specifications."""

    def __init__(self, image: Gimp.Image, template: Template) -> None:
        """Initialize the text renderer.

        Args:
            image: The GIMP image to render text on.
            template: The template defining text field positions and styles.
        """
        self.image = image
        self.template = template
        self.image_width = image.get_width()
        self.image_height = image.get_height()

    def _calculate_font_size(self, size_ratio: float) -> float:
        """Calculate font size in pixels from ratio.

        Args:
            size_ratio: Font size as ratio of image's shorter side.

        Returns:
            Font size in pixels.
        """
        shorter_side = min(self.image_width, self.image_height)
        return shorter_side * size_ratio

    def _calculate_position(self, field: TextField) -> tuple[float, float]:
        """Calculate pixel position from ratio.

        Args:
            field: The text field configuration.

        Returns:
            Tuple of (x, y) position in pixels.
        """
        x = self.image_width * field.position.x_ratio
        y = self.image_height * field.position.y_ratio
        return x, y

    def _parse_color(self, hex_color: str) -> Gegl.Color:
        """Parse hex color string to Gegl.Color.

        Args:
            hex_color: Hex color string (e.g., "#000000").

        Returns:
            Gegl.Color color object.
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip("#")

        # Parse RGB values (0-255)
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Create Gegl.Color and set RGB values
        color = Gegl.Color.new("black")  # Create a color object
        color.set_rgba(r / 255.0, g / 255.0, b / 255.0, 1.0)
        return color

    def render_text(self, field_name: str, text: str) -> Gimp.Layer | None:
        """Render a single text field.

        Args:
            field_name: Name of the field from the template.
            text: The text content to render.

        Returns:
            The created text layer, or None if field is not visible or text is empty.
        """
        # Get field configuration
        if field_name not in self.template.fields:
            return None

        field = self.template.fields[field_name]

        # Skip if not visible or text is empty
        if not field.visible or not text.strip():
            return None

        # Calculate position and font size
        x, y = self._calculate_position(field)
        font_size = self._calculate_font_size(field.font.size_ratio)

        # Parse color
        color = self._parse_color(field.font.color)

        # Create text layer using PDB
        try:
            # Get PDB
            pdb = Gimp.get_pdb()

            # Try gimp-image-text-fontname first (accepts font as string)
            proc_names = [
                "gimp-image-text-fontname",
                "gimp-text-fontname",
                "gimp-text-layer-new",
            ]

            proc = None
            proc_name = None
            for name in proc_names:
                proc = pdb.lookup_procedure(name)
                if proc is not None:
                    proc_name = name
                    break

            if proc is None:
                _debug_log("ERROR: No text procedure found")
                return None

            # Create config
            config = proc.create_config()

            # Set config properties based on the procedure
            try:
                config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            except Exception:
                pass  # Not all procedures have run-mode

            # Set image (required for most text procedures)
            config.set_property("image", self.image)

            # Different procedures may have different parameter names
            # Try common variations
            for x_name in ["x", "x-position", "xpos"]:
                try:
                    config.set_property(x_name, x)
                    break
                except Exception:
                    pass

            for y_name in ["y", "y-position", "ypos"]:
                try:
                    config.set_property(y_name, y)
                    break
                except Exception:
                    pass

            config.set_property("text", text)

            for size_name in ["size", "font-size", "size-pixels"]:
                try:
                    config.set_property(size_name, font_size)
                    break
                except Exception:
                    pass

            # Handle font parameter based on procedure type
            if proc_name in ["gimp-image-text-fontname", "gimp-text-fontname"]:
                # These procedures accept font name as string
                for font_name_param in ["fontname", "font-name", "font"]:
                    try:
                        config.set_property(font_name_param, field.font.family)
                        break
                    except Exception:
                        pass
            elif proc_name == "gimp-text-layer-new":
                # Get the current context font - we'll use this directly
                # Note: We're using the default context font instead of trying to
                # match the template's font family, since font lookup APIs don't work reliably
                try:
                    font_obj = Gimp.context_get_font()
                    if font_obj:
                        config.set_property("font", font_obj)
                except Exception as e:
                    _debug_log(f"WARNING: Could not set font: {e}")

            # Set unit (may be required for some procedures)
            try:
                config.set_property("unit", Gimp.Unit.pixel())
            except Exception:
                pass

            # Run the procedure
            result = proc.run(config)

            # Get the created text layer
            # Note: Status might not be SUCCESS but we can still get a valid layer
            text_layer = None
            try:
                text_layer = result.index(1)
            except Exception:
                try:
                    text_layer = result.index(2)
                except Exception:
                    pass

            if text_layer is None:
                _debug_log(f"ERROR: Failed to create text layer for {field_name}")
                return None

            # Set text color using PDB
            run_pdb_procedure(
                "gimp-text-layer-set-color",
                [
                    GObject.Value(Gimp.Layer, text_layer),
                    GObject.Value(Gegl.Color, color),
                ],
                debug_log=_debug_log,
            )

            # Position the layer based on alignment
            layer_width = text_layer.get_width()
            layer_height = text_layer.get_height()

            # Adjust X position based on horizontal alignment
            final_x = x
            if field.align == "center":
                final_x = x - layer_width / 2
            elif field.align == "right":
                final_x = x - layer_width

            # Adjust Y position based on vertical alignment
            final_y = y
            if field.vertical_align == "middle":
                final_y = y - layer_height / 2
            elif field.vertical_align == "bottom":
                final_y = y - layer_height

            # Insert the layer into the image
            # Add it at position 0 (top of the layer stack)
            self.image.insert_layer(text_layer, None, 0)

            # Set layer position
            text_layer.set_offsets(int(final_x), int(final_y))

            # Set layer name
            text_layer.set_name(f"Text: {field_name}")

            return text_layer

        except Exception as e:
            # If PDB call fails, return None
            _debug_log(f"ERROR: Failed to render text for {field_name}: {e}")
            return None

    def render_all(self, data: dict[str, str]) -> list[Gimp.Layer]:
        """Render all text fields from data.

        Args:
            data: Dictionary mapping field names to text content.

        Returns:
            List of created text layers.
        """
        layers = []

        for field_name, text in data.items():
            layer = self.render_text(field_name, text)
            if layer is not None:
                layers.append(layer)

        return layers

    def render_from_csv_row(self, row_data: dict[str, str]) -> list[Gimp.Layer]:
        """Render text fields from a CSV row.

        This is a convenience method that calls render_all() with CSV row data.

        Args:
            row_data: Dictionary from CSV row (column_name -> value).

        Returns:
            List of created text layers.
        """
        return self.render_all(row_data)
