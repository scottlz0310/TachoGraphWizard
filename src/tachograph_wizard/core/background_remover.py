"""Background removal module for tachograph charts.

Provides functionality to remove white background and clean up
scanned image artifacts using GEGL filters.
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")

from gi.repository import Gegl, Gimp, GObject

from tachograph_wizard.core.image_cleanup import add_center_guides, auto_cleanup_and_crop, despeckle
from tachograph_wizard.core.island_detector import remove_garbage_keep_largest_island
from tachograph_wizard.core.pdb_runner import run_pdb_procedure


def _debug_log(message: str) -> None:
    """Write debug message to log file."""
    try:
        base = os.environ.get("TEMP") or os.environ.get("TMP") or os.environ.get("LOCALAPPDATA")
        if not base:
            return
        log_path = Path(base) / "tachograph_wizard.log"
        ts = datetime.datetime.now(tz=datetime.UTC).isoformat(timespec="seconds")
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{ts}] background_remover: {message}\n")
    except Exception:
        return


class BackgroundRemover:
    """Remove background and make it transparent."""

    @staticmethod
    def color_to_alpha(
        drawable: Gimp.Drawable,
        color: Gegl.Color | None = None,
        transparency_threshold: float = 15.0,
    ) -> None:
        """Apply Color to Alpha filter to remove background.

        Converts the specified color (default: white) to transparent,
        allowing the background to be removed from scanned images.

        Args:
            drawable: Target drawable (layer) to process.
            color: Color to make transparent (default: white).
            transparency_threshold: Threshold for color matching (0-100).
                Higher values make more similar colors transparent.
        """
        _debug_log(f"color_to_alpha called: drawable={drawable}, threshold={transparency_threshold}")

        # GEGL expects thresholds in the 0.0-1.0 range. Allow 0-100 inputs for UI convenience.
        normalized_threshold = transparency_threshold
        if normalized_threshold > 1.0:
            normalized_threshold = normalized_threshold / 100.0
        normalized_threshold = max(0.0, min(1.0, normalized_threshold))

        if color is None:
            color = Gegl.Color.new("white")

        # Ensure layer has alpha channel
        if not drawable.has_alpha():
            _debug_log("Adding alpha channel to drawable")
            drawable.add_alpha()

        # Try gegl:color-to-alpha via gimp_drawable_apply_operation
        image = drawable.get_image()
        try:
            _debug_log("Trying gimp-drawable-color-to-alpha")
            result = run_pdb_procedure(
                "gimp-drawable-color-to-alpha",
                [
                    GObject.Value(Gimp.Drawable, drawable),
                    GObject.Value(Gegl.Color, color),
                ],
                debug_log=_debug_log,
            )
            status = result.index(0)
            _debug_log(f"gimp-drawable-color-to-alpha result status={status}")
            if status == Gimp.PDBStatusType.SUCCESS:
                return
        except Exception as e:
            _debug_log(f"gimp-drawable-color-to-alpha failed: {type(e).__name__}: {e}")

        # Try plug-in-colortoalpha (legacy)
        try:
            _debug_log("Trying plug-in-colortoalpha")
            result = run_pdb_procedure(
                "plug-in-colortoalpha",
                [
                    GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
                    GObject.Value(Gimp.Image, image),
                    GObject.Value(Gimp.Drawable, drawable),
                    GObject.Value(Gegl.Color, color),
                ],
                debug_log=_debug_log,
            )
            status = result.index(0)
            _debug_log(f"plug-in-colortoalpha result status={status}")
            if status == Gimp.PDBStatusType.SUCCESS:
                return
        except Exception as e:
            _debug_log(f"plug-in-colortoalpha failed: {type(e).__name__}: {e}")

        # Fallback: Try direct GEGL operation
        try:
            _debug_log("Trying direct Gegl.Node approach")
            # Use GEGL directly
            buffer = drawable.get_buffer()
            shadow = drawable.get_shadow_buffer()

            graph = Gegl.Node()
            src = graph.create_child("gegl:buffer-source")
            src.set_property("buffer", buffer)

            c2a = graph.create_child("gegl:color-to-alpha")
            c2a.set_property("color", color)
            c2a.set_property("transparency-threshold", normalized_threshold)
            c2a.set_property("opacity-threshold", normalized_threshold)

            sink = graph.create_child("gegl:write-buffer")
            sink.set_property("buffer", shadow)

            src.link(c2a)
            c2a.link(sink)

            sink.process()

            drawable.merge_shadow(True)
            drawable.update(0, 0, drawable.get_width(), drawable.get_height())
            _debug_log("Direct Gegl.Node approach succeeded")
            return
        except Exception as e:
            _debug_log(f"Direct Gegl.Node approach failed: {type(e).__name__}: {e}")

        _debug_log("All color-to-alpha methods failed")

    @staticmethod
    def despeckle(drawable: Gimp.Drawable, radius: int = 2) -> None:
        """Remove small noise/specks from scanned image.

        Uses median filter to clean up scan artifacts and small specks
        that may appear in scanned tachograph charts.

        Args:
            drawable: Target drawable (layer) to process.
            radius: Median blur radius (default: 2). Larger values remove
                more noise but may blur details.
        """
        despeckle(drawable, radius=radius)

    @staticmethod
    def auto_cleanup_and_crop(
        drawable: Gimp.Drawable,
        ellipse_padding: int = 20,
    ) -> None:
        """Auto cleanup and crop using simple ellipse selection.

        Simple algorithm:
        1. Create ellipse selection accounting for padding
        2. Invert to select everything outside ellipse
        3. Delete selected area (make transparent)
        4. Crop to content

        Args:
            drawable: Target drawable (layer) to process.
            ellipse_padding: Padding (inset) from image edge for ellipse selection.
        """

        auto_cleanup_and_crop(drawable, ellipse_padding=ellipse_padding)

    @staticmethod
    def remove_garbage_keep_largest_island(
        drawable: Gimp.Drawable,
        threshold: float = 15.0,
    ) -> None:
        """Remove garbage by keeping only the largest non-white island.

        Simplified algorithm:
        1. Apply color-to-alpha to remove white background
        2. Use select-by-alpha to select non-transparent areas
        3. Shrink+grow to remove small islands
        4. Invert and delete garbage

        Args:
            drawable: Target drawable (layer) to process.
            threshold: Color matching threshold for background removal.
        """
        remove_garbage_keep_largest_island(drawable, threshold=threshold)

    @staticmethod
    def add_center_guides(image: Gimp.Image) -> None:
        """Add horizontal and vertical guides at 50% position.

        Adds guides at the center of the image to assist with
        rotation alignment in GIMP's arbitrary rotation tool.

        Args:
            image: Target image to add guides to.
        """
        add_center_guides(image)

    @staticmethod
    def process_background(
        drawable: Gimp.Drawable,
        ellipse_padding: int = 20,
        remove_color: Gegl.Color | None = None,  # noqa: ARG004 - kept for API compatibility
        apply_despeckle: bool = True,  # noqa: ARG004 - kept for API compatibility
        despeckle_radius: int = 2,  # noqa: ARG004 - kept for API compatibility
        use_island_method: bool = False,  # noqa: ARG004 - kept for API compatibility
    ) -> None:
        """Complete background removal process using ellipse selection.

        Creates an ellipse selection based on padding, inverts it, and deletes
        everything outside the disc area. After cleanup, adds center guides
        at 50% position to assist with rotation alignment.

        Args:
            drawable: Target drawable (layer) to process.
            ellipse_padding: Padding (inset) from image edge for ellipse selection.
            remove_color: Unused, kept for API compatibility.
            apply_despeckle: Unused, kept for API compatibility.
            despeckle_radius: Unused, kept for API compatibility.
            use_island_method: Unused, kept for API compatibility.
        """
        _debug_log(f"process_background called: ellipse_padding={ellipse_padding}")

        # Use ellipse-based cleanup method
        BackgroundRemover.auto_cleanup_and_crop(drawable, ellipse_padding=ellipse_padding)

        # Add center guides for rotation assist
        image = drawable.get_image()
        BackgroundRemover.add_center_guides(image)

        _debug_log("process_background completed")
