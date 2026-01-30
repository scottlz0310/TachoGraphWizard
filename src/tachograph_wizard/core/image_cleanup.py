"""画像クリーンアップモジュール.

背景除去の前処理として、ノイズ除去や楕円選択による切り抜き、
中心ガイドの追加などの機能を提供する。
"""

from __future__ import annotations

import gi

gi.require_version("Gimp", "3.0")

from gi.repository import Gimp, GObject

from tachograph_wizard.core.logging_util import debug_log
from tachograph_wizard.core.pdb_runner import run_pdb_procedure


def _debug_log(message: str) -> None:
    """Write debug message to log file."""
    debug_log(message, module="image_cleanup")


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

    _debug_log(f"auto_cleanup_and_crop called: ellipse_padding={ellipse_padding}")

    image = drawable.get_image()
    _debug_log(f"Working on image: {image}, drawable: {drawable}")
    _debug_log(f"Image size: {image.get_width()}x{image.get_height()}")
    _debug_log(f"Drawable name: {drawable.get_name() if hasattr(drawable, 'get_name') else 'unknown'}")

    # Ensure layer has alpha channel
    if not drawable.has_alpha():
        drawable.add_alpha()

    width = image.get_width()
    height = image.get_height()

    # 1. Create ellipse selection accounting for padding
    # Image size = disc + (2 * ellipse_padding)
    # So ellipse should start at (ellipse_padding, ellipse_padding) with size (width - 2*ellipse_padding, height - 2*ellipse_padding)
    ellipse_x = ellipse_padding
    ellipse_y = ellipse_padding
    ellipse_w = max(1, width - ellipse_padding * 2)
    ellipse_h = max(1, height - ellipse_padding * 2)

    _debug_log(
        f"Creating ellipse selection at ({ellipse_x},{ellipse_y}) size {ellipse_w}x{ellipse_h} (padding={ellipse_padding}px)",
    )

    # GIMP 3 Python: Use image.select_ellipse() method instead of PDB
    Gimp.context_push()
    try:
        # Set context for smooth selection edges
        Gimp.context_set_antialias(True)
        Gimp.context_set_feather(False)  # No feathering for sharp edges

        # Clear any existing selection
        Gimp.Selection.none(image)
        _debug_log("Cleared existing selection")

        # Create ellipse selection using GIMP 3 method
        image.select_ellipse(
            Gimp.ChannelOps.REPLACE,
            ellipse_x,
            ellipse_y,
            ellipse_w,
            ellipse_h,
        )
        _debug_log("Created ellipse selection")

        # Invert selection to select everything outside the disc
        Gimp.Selection.invert(image)
        _debug_log("Inverted selection to select garbage outside disc")

        # Delete selected area (make transparent)
        drawable.edit_clear()
        _debug_log("Deleted garbage outside disc")

        # Remove selection
        Gimp.Selection.none(image)
        _debug_log("Removed selection")

    except Exception as e:
        _debug_log(f"Ellipse selection failed: {e}")
        import traceback

        _debug_log(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        Gimp.context_pop()

    # 5. Crop to content
    _debug_log("Cropping to content")
    try:
        if hasattr(image, "autocrop"):
            image.autocrop()
            _debug_log("Autocrop succeeded")
    except Exception as e:
        _debug_log(f"Autocrop failed (non-critical): {e}")

    Gimp.displays_flush()
    _debug_log("auto_cleanup_and_crop completed")


def add_center_guides(image: Gimp.Image) -> None:
    """Add horizontal and vertical guides at 50% position.

    Adds guides at the center of the image to assist with
    rotation alignment in GIMP's arbitrary rotation tool.

    Args:
        image: Target image to add guides to.
    """
    _debug_log("add_center_guides called")

    width = image.get_width()
    height = image.get_height()

    # Calculate 50% positions
    center_x = width // 2
    center_y = height // 2

    _debug_log(f"Image size: {width}x{height}, center: ({center_x}, {center_y})")

    # Add vertical guide at 50% horizontal position
    try:
        image.add_vguide(center_x)
        _debug_log(f"Added vertical guide at x={center_x}")
    except Exception as e:
        _debug_log(f"Failed to add vertical guide: {e}")

    # Add horizontal guide at 50% vertical position
    try:
        image.add_hguide(center_y)
        _debug_log(f"Added horizontal guide at y={center_y}")
    except Exception as e:
        _debug_log(f"Failed to add horizontal guide: {e}")

    _debug_log("add_center_guides completed")
