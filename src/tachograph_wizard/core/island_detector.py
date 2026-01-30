"""島検出モジュール.

背景除去時のノイズ除去・最大連結成分抽出に関する処理を提供する。
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path

import gi

gi.require_version("Gegl", "0.4")
gi.require_version("Gimp", "3.0")

from gi.repository import Gegl, Gimp, GObject

from tachograph_wizard.core.image_analysis import buffer_get_bytes
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
            log_file.write(f"[{ts}] island_detector: {message}\n")
    except Exception:
        return


_ELLIPSE_MARGIN = 50
_SELECTION_SHRINK_AMOUNT = 10
_SELECTION_MASK_THRESHOLD = 127


def remove_garbage_keep_largest_island(
    drawable: Gimp.Drawable,
    threshold: float = 15.0,
) -> None:
    """Remove garbage by keeping only the largest non-white island.

    Simplified algorithm:
    1. Convert working layer to grayscale and apply thresholding.
    2. Select background pixels based on the threshold result.
    3. Intersect with a large ellipse to focus on the disc area.
    4. Shrink+grow selection to remove small islands.
    5. Invert selection and clear garbage on the original layer.

    Args:
        drawable: Target drawable (layer) to process.
        threshold: Color matching threshold for background removal.
    """
    image = drawable.get_image()

    # Ensure layer has alpha channel
    if not drawable.has_alpha():
        drawable.add_alpha()

    # 1. Create working layer copy (for analysis only)
    _debug_log("Creating working layer copy")
    work_layer = drawable.copy()
    image.insert_layer(work_layer, None, 0)

    # 2. Convert working layer to grayscale
    _debug_log("Converting working layer to grayscale")
    run_pdb_procedure(
        "gimp-drawable-desaturate",
        [
            GObject.Value(Gimp.Drawable, work_layer),
            GObject.Value(Gimp.DesaturateMode, Gimp.DesaturateMode.LIGHTNESS),
        ],
        debug_log=_debug_log,
    )

    # 3. Apply median blur to remove noise (skip if not available in GIMP 3.0)
    try:
        run_pdb_procedure(
            "plug-in-median-blur",
            [
                GObject.Value(Gimp.Drawable, work_layer),
                GObject.Value(GObject.TYPE_DOUBLE, 4.0),
                GObject.Value(GObject.TYPE_DOUBLE, 50.0),
            ],
        )
    except Exception:
        pass  # Median blur not available in GIMP 3.0, skip silently

    # 4. Apply threshold using GEGL (PDB version is broken in GIMP 3.0)
    # UI threshold (0-100) means "tolerance from white"
    # threshold=15 → white(255) ± 15 → 225-255 should be white (background)
    lower_threshold = max(0, 255 - threshold * 2)  # Scale UI range appropriately
    _debug_log(f"Applying GEGL threshold: {lower_threshold}-255 (background becomes white)")

    try:
        # Use GEGL threshold operation
        # Get work_layer's buffer
        buffer = work_layer.get_buffer()

        # Create GEGL graph with threshold operation
        graph = Gegl.Node()
        src = graph.create_child("gegl:buffer-source")
        src.set_property("buffer", buffer)

        threshold_node = graph.create_child("gimp:threshold")
        threshold_node.set_property("low", float(lower_threshold) / 255.0)
        threshold_node.set_property("high", 1.0)

        sink = graph.create_child("gegl:buffer-sink")
        sink.set_property("buffer", buffer)

        # Connect nodes
        src.connect_to("output", threshold_node, "input")
        threshold_node.connect_to("output", sink, "input")

        # Process
        sink.process()

        _debug_log("GEGL threshold processing completed")

        # Update the layer
        work_layer.update(0, 0, work_layer.get_width(), work_layer.get_height())

    except Exception as e:
        _debug_log(f"GEGL threshold failed: {e}, trying manual buffer approach")

        # Fallback: Manual threshold via GeglBuffer
        try:
            buffer = work_layer.get_buffer()
            rect = buffer.get_extent()
            width = int(rect.width)
            height = int(rect.height)

            # Read pixel data
            full_rect = Gegl.Rectangle()
            full_rect.x = 0
            full_rect.y = 0
            full_rect.width = width
            full_rect.height = height

            pixel_data = buffer_get_bytes(buffer, full_rect, 1.0, "R'G'B'A u8")

            if pixel_data:
                # Manual threshold: convert to bytearray for modification
                pixels = bytearray(pixel_data)

                for i in range(0, len(pixels), 4):
                    # Get grayscale value (R=G=B for grayscale)
                    gray = pixels[i]

                    # Apply threshold: if gray >= lower_threshold -> white (255), else black (0)
                    if gray >= lower_threshold:
                        pixels[i] = 255  # R
                        pixels[i + 1] = 255  # G
                        pixels[i + 2] = 255  # B
                    else:
                        pixels[i] = 0
                        pixels[i + 1] = 0
                        pixels[i + 2] = 0
                    # Keep alpha as is

                # Write back to buffer
                buffer.set(full_rect, "R'G'B'A u8", bytes(pixels))
                work_layer.update(0, 0, width, height)

                _debug_log("Manual threshold via GeglBuffer completed")
            else:
                _debug_log("ERROR: Failed to read pixel data from buffer")

        except Exception as e2:
            _debug_log(f"Manual threshold also failed: {e2}")

    # 5. Select background (white) using threshold-based color selection
    # This selects ALL white pixels, not just contiguous ones
    _debug_log("Selecting background using color range (threshold-based)")
    width = image.get_width()
    height = image.get_height()

    try:
        # Select by color range instead of contiguous selection
        # This will select ALL pixels in the white range, regardless of connectivity
        run_pdb_procedure(
            "gimp-image-select-color",
            [
                GObject.Value(Gimp.Image, image),
                GObject.Value(Gimp.ChannelOps, Gimp.ChannelOps.REPLACE),
                GObject.Value(Gimp.Drawable, work_layer),
                GObject.Value(Gegl.Color, Gegl.Color.new("white")),
            ],
            debug_log=_debug_log,
        )
        _debug_log("Selected all white pixels using color selection")
    except Exception as e:
        _debug_log(f"Color selection failed: {e}, trying contiguous fallback")
        # Fallback to corner selection if color selection fails
        corners = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
        selected = False
        for x, y in corners:
            try:
                run_pdb_procedure(
                    "gimp-image-select-contiguous-color",
                    [
                        GObject.Value(Gimp.Image, image),
                        GObject.Value(Gimp.ChannelOps, Gimp.ChannelOps.ADD),
                        GObject.Value(Gimp.Drawable, work_layer),
                        GObject.Value(GObject.TYPE_DOUBLE, float(x)),
                        GObject.Value(GObject.TYPE_DOUBLE, float(y)),
                    ],
                    debug_log=_debug_log,
                )
                selected = True
                _debug_log(f"Selected background from corner ({x}, {y})")
            except Exception as e2:
                _debug_log(f"Failed to select from corner ({x}, {y}): {e2}")  # nosec B608

        if not selected:
            _debug_log("Failed to select background")
            image.remove_layer(work_layer)
            return

    # 6. Invert selection to select disc + noise
    _debug_log("Inverting selection to select disc + noise")
    run_pdb_procedure(
        "gimp-selection-invert",
        [GObject.Value(Gimp.Image, image)],
        debug_log=_debug_log,
    )

    # Check if selection is empty BEFORE intersection
    result_before = run_pdb_procedure(
        "gimp-selection-is-empty",
        [GObject.Value(Gimp.Image, image)],
        debug_log=_debug_log,
    )
    is_empty_before = result_before.index(1)
    _debug_log(f"Selection empty before intersection: {is_empty_before}")

    # 7. Create ellipse selection for the disc area and INTERSECT
    # This removes noise outside the disc area, keeping only the main disc
    # The disc should be centered in the cropped image
    _debug_log("Creating ellipse selection to isolate disc")

    # Use a large ellipse that covers most of the image (disc area)
    ellipse_x = _ELLIPSE_MARGIN
    ellipse_y = _ELLIPSE_MARGIN
    ellipse_w = max(1, width - _ELLIPSE_MARGIN * 2)
    ellipse_h = max(1, height - _ELLIPSE_MARGIN * 2)

    run_pdb_procedure(
        "gimp-image-select-ellipse",
        [
            GObject.Value(Gimp.Image, image),
            GObject.Value(Gimp.ChannelOps, Gimp.ChannelOps.INTERSECT),  # INTERSECT!
            GObject.Value(GObject.TYPE_DOUBLE, float(ellipse_x)),
            GObject.Value(GObject.TYPE_DOUBLE, float(ellipse_y)),
            GObject.Value(GObject.TYPE_DOUBLE, float(ellipse_w)),
            GObject.Value(GObject.TYPE_DOUBLE, float(ellipse_h)),
        ],
        debug_log=_debug_log,
    )
    _debug_log(f"Intersected with ellipse at ({ellipse_x},{ellipse_y}) size {ellipse_w}x{ellipse_h}")

    # 8. Check if selection is empty
    result = run_pdb_procedure(
        "gimp-selection-is-empty",
        [GObject.Value(Gimp.Image, image)],
        debug_log=_debug_log,
    )
    is_empty = result.index(1)

    if is_empty:
        _debug_log("Selection is empty after intersection - threshold may need adjustment")
        image.remove_layer(work_layer)
        return

    # Log selection bounds after intersection
    try:
        bounds = run_pdb_procedure(
            "gimp-selection-bounds",
            [GObject.Value(Gimp.Image, image)],
        )
        has_selection = bounds.index(1)
        if has_selection:
            x1, y1, x2, y2 = bounds.index(2), bounds.index(3), bounds.index(4), bounds.index(5)
            _debug_log(f"Selection after intersection: ({x1},{y1})-({x2},{y2}) size={x2 - x1}x{y2 - y1}")
    except Exception as e:
        _debug_log(f"Failed to get selection bounds: {e}")

    # 8.5. Remove small noise islands by shrinking then growing the selection
    # This keeps only the largest connected component (the disc)
    _debug_log("Removing small noise islands with shrink+grow")
    shrink_amount = _SELECTION_SHRINK_AMOUNT

    run_pdb_procedure(
        "gimp-selection-shrink",
        [
            GObject.Value(Gimp.Image, image),
            GObject.Value(GObject.TYPE_INT, shrink_amount),
        ],
        debug_log=_debug_log,
    )
    _debug_log(f"Selection shrunk by {shrink_amount}px")

    # Log selection bounds after shrink
    try:
        bounds = run_pdb_procedure(
            "gimp-selection-bounds",
            [GObject.Value(Gimp.Image, image)],
        )
        has_selection = bounds.index(1)
        if has_selection:
            x1, y1, x2, y2 = bounds.index(2), bounds.index(3), bounds.index(4), bounds.index(5)
            _debug_log(f"Selection after shrink: ({x1},{y1})-({x2},{y2}) size={x2 - x1}x{y2 - y1}")
        else:
            _debug_log("WARNING: Selection became empty after shrink!")
    except Exception as e:
        _debug_log(f"Failed to get selection bounds: {e}")

    run_pdb_procedure(
        "gimp-selection-grow",
        [
            GObject.Value(Gimp.Image, image),
            GObject.Value(GObject.TYPE_INT, shrink_amount),
        ],
        debug_log=_debug_log,
    )
    _debug_log(f"Selection grown back by {shrink_amount}px")

    # Log selection bounds after grow
    try:
        bounds = run_pdb_procedure(
            "gimp-selection-bounds",
            [GObject.Value(Gimp.Image, image)],
        )
        has_selection = bounds.index(1)
        if has_selection:
            x1, y1, x2, y2 = bounds.index(2), bounds.index(3), bounds.index(4), bounds.index(5)
            _debug_log(f"Selection after grow: ({x1},{y1})-({x2},{y2}) size={x2 - x1}x{y2 - y1}")
        else:
            _debug_log("WARNING: Selection is empty after grow!")
    except Exception as e:
        _debug_log(f"Failed to get selection bounds: {e}")

    # 9. Invert again to select garbage (everything outside disc)
    _debug_log("Inverting selection again to select garbage")
    run_pdb_procedure(
        "gimp-selection-invert",
        [GObject.Value(Gimp.Image, image)],
        debug_log=_debug_log,
    )

    # Log selection bounds after final invert
    try:
        bounds = run_pdb_procedure(
            "gimp-selection-bounds",
            [GObject.Value(Gimp.Image, image)],
        )
        has_selection = bounds.index(1)
        if has_selection:
            x1, y1, x2, y2 = bounds.index(2), bounds.index(3), bounds.index(4), bounds.index(5)
            _debug_log(f"Selection after final invert (garbage): ({x1},{y1})-({x2},{y2}) size={x2 - x1}x{y2 - y1}")
        else:
            _debug_log("WARNING: No garbage selected after final invert!")
    except Exception as e:
        _debug_log(f"Failed to get selection bounds: {e}")

    # DEBUG: Save selection to channel for visualization
    try:
        selection_channel = run_pdb_procedure(
            "gimp-selection-save",
            [GObject.Value(Gimp.Image, image)],
        )
        if selection_channel:
            channel = selection_channel.index(1)
            if hasattr(channel, "set_name"):
                channel.set_name("DEBUG_garbage_selection")
            _debug_log(f"Saved selection to channel for debugging: {channel}")
    except Exception as e:
        _debug_log(f"Failed to save selection to channel: {e}")

    # 10. Clear garbage on original drawable
    _debug_log(f"Clearing garbage on original layer (drawable={drawable}, has_alpha={drawable.has_alpha()})")

    # Verify which layer we're clearing
    layer_name = drawable.get_name() if hasattr(drawable, "get_name") else "unknown"
    _debug_log(f"Layer name: {layer_name}")

    # Make sure we're clearing on the correct image
    drawable_image = drawable.get_image()
    _debug_log(f"Image from drawable: {drawable_image}, current image: {image}, same={drawable_image == image}")

    # Verify the selection is on the correct image
    try:
        sel_empty = run_pdb_procedure(
            "gimp-selection-is-empty",
            [GObject.Value(Gimp.Image, drawable_image)],
        )
        _debug_log(f"Selection on drawable's image is empty: {sel_empty.index(1)}")
    except Exception as e:
        _debug_log(f"Failed to check selection on drawable's image: {e}")

    # Clear by directly manipulating pixel buffer
    try:
        _debug_log("Attempting direct buffer manipulation to set alpha=0 for selected pixels")

        # Get the layer's buffer
        buffer = drawable.get_buffer()
        width = drawable.get_width()
        height = drawable.get_height()

        # Get the selection mask as a GeglBuffer
        selection = image.get_selection()
        selection_buffer = selection.get_buffer()

        # Define the region to process
        rect = Gegl.Rectangle()
        rect.x = 0
        rect.y = 0
        rect.width = width
        rect.height = height

        # Read current pixels (RGBA)
        pixel_data = buffer_get_bytes(buffer, rect, 1.0, "R'G'B'A u8")

        # Read selection mask (single channel, 0-255)
        selection_data = buffer_get_bytes(selection_buffer, rect, 1.0, "Y u8")

        if pixel_data and selection_data:
            pixels = bytearray(pixel_data)
            mask = bytearray(selection_data)

            _debug_log(f"Processing {len(pixels) // 4} pixels, mask size={len(mask)}")

            # For each pixel, if it's selected (mask > 127), set alpha to 0
            modified_count = 0
            for i in range(len(mask)):
                if mask[i] > _SELECTION_MASK_THRESHOLD:  # Pixel is selected
                    pixel_idx = i * 4
                    if pixel_idx + 3 < len(pixels):
                        pixels[pixel_idx + 3] = 0  # Set alpha to 0 (transparent)
                        modified_count += 1

            _debug_log(f"Set alpha=0 for {modified_count} pixels")

            # Write modified pixels back
            buffer.set(rect, "R'G'B'A u8", bytes(pixels))
            drawable.update(0, 0, width, height)
            Gimp.displays_flush()
            _debug_log("Buffer updated successfully")

        else:
            _debug_log("ERROR: Failed to read pixel or selection data")

    except Exception as e:
        _debug_log(f"ERROR: Direct buffer manipulation failed: {e}")
        import traceback

        _debug_log(f"Traceback: {traceback.format_exc()}")

    # 11. Remove selection
    _debug_log("Removing selection")
    run_pdb_procedure(
        "gimp-selection-none",
        [GObject.Value(Gimp.Image, image)],
        debug_log=_debug_log,
    )

    # 12. Remove working layer
    _debug_log("Removing working layer")
    image.remove_layer(work_layer)

    # 13. Crop to content
    _debug_log("Cropping to content")
    try:
        # Try autocrop method first
        if hasattr(image, "autocrop"):
            image.autocrop()
            _debug_log("Autocrop via image.autocrop() succeeded")
        else:
            # Fallback to PDB
            run_pdb_procedure(
                "gimp-image-crop",
                [
                    GObject.Value(Gimp.Image, image),
                    GObject.Value(GObject.TYPE_INT, image.get_width()),
                    GObject.Value(GObject.TYPE_INT, image.get_height()),
                    GObject.Value(GObject.TYPE_INT, 0),
                    GObject.Value(GObject.TYPE_INT, 0),
                ],
                debug_log=_debug_log,
            )
            _debug_log("Fallback crop attempted (autocrop not available)")
    except Exception as e:
        _debug_log(f"Autocrop failed (non-critical): {e}")

    _debug_log("remove_garbage_keep_largest_island completed")
