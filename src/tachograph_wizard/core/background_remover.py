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

from tachograph_wizard.core.pdb_runner import run_pdb_procedure


def _debug_log(message: str) -> None:
    """Write debug message to log file."""
    try:
        base = os.environ.get("TEMP") or os.environ.get("TMP") or os.environ.get("LOCALAPPDATA")
        if not base:
            return
        log_path = Path(base) / "tachograph_wizard.log"
        ts = datetime.datetime.now(tz=datetime.UTC).isoformat(timespec="seconds")
        log_path.open("a", encoding="utf-8").write(f"[{ts}] background_remover: {message}\n")
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
        _debug_log(f"despeckle called: drawable={drawable}, radius={radius}")

        # Try plug-in-despeckle first
        try:
            _debug_log("Trying plug-in-despeckle")
            result = run_pdb_procedure(
                "plug-in-despeckle",
                [
                    GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
                    GObject.Value(Gimp.Image, drawable.get_image()),
                    GObject.Value(Gimp.Drawable, drawable),
                    GObject.Value(GObject.TYPE_INT, radius),
                ],
                debug_log=_debug_log,
            )
            status = result.index(0)
            _debug_log(f"plug-in-despeckle result status={status}")
            if status == Gimp.PDBStatusType.SUCCESS:
                return
        except Exception as e:
            _debug_log(f"plug-in-despeckle failed: {type(e).__name__}: {e}")

        # Try plug-in-median-noise (alternative despeckle)
        try:
            _debug_log("Trying plug-in-median-noise")
            result = run_pdb_procedure(
                "plug-in-median-noise",
                [
                    GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
                    GObject.Value(Gimp.Image, drawable.get_image()),
                    GObject.Value(Gimp.Drawable, drawable),
                    GObject.Value(GObject.TYPE_INT, radius),
                ],
                debug_log=_debug_log,
            )
            status = result.index(0)
            _debug_log(f"plug-in-median-noise result status={status}")
            if status == Gimp.PDBStatusType.SUCCESS:
                return
        except Exception as e:
            _debug_log(f"plug-in-median-noise failed: {type(e).__name__}: {e}")

        _debug_log("Despeckle skipped - no working method found (this is optional)")

    @staticmethod
    def process_background(
        drawable: Gimp.Drawable,
        remove_color: Gegl.Color | None = None,
        threshold: float = 15.0,
        apply_despeckle: bool = True,
        despeckle_radius: int = 2,
    ) -> None:
        """Complete background removal process.

        Applies both color-to-alpha and despeckle operations in sequence
        for comprehensive background cleaning.

        Args:
            drawable: Target drawable (layer) to process.
            remove_color: Color to remove (default: white).
            threshold: Color matching threshold (0-100).
            apply_despeckle: Whether to apply despeckle filter.
            despeckle_radius: Radius for despeckle operation.
        """
        _debug_log(f"process_background called: threshold={threshold}, apply_despeckle={apply_despeckle}")

        # Apply despeckle first (before making background transparent)
        if apply_despeckle:
            BackgroundRemover.despeckle(drawable, despeckle_radius)

        # Then apply color to alpha
        BackgroundRemover.color_to_alpha(drawable, remove_color, threshold)

        _debug_log("process_background completed")
