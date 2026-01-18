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
        from gi.repository import Gegl

        from tachograph_wizard.core.pdb_runner import run_pdb_procedure

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
            from gi.repository import Gegl

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
                from gi.repository import Gegl

                from tachograph_wizard.core.image_splitter import ImageSplitter

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

                pixel_data = ImageSplitter._buffer_get_bytes(buffer, full_rect, 1.0, "R'G'B'A u8")  # pyright: ignore[reportPrivateUsage]

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
        margin = 50  # Leave some margin from edges
        ellipse_x = margin
        ellipse_y = margin
        ellipse_w = max(1, width - margin * 2)
        ellipse_h = max(1, height - margin * 2)

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
        shrink_amount = 10  # Shrink by 10px to remove small disconnected noise

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
            from gi.repository import Gegl

            from tachograph_wizard.core.image_splitter import ImageSplitter

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
            pixel_data = ImageSplitter._buffer_get_bytes(buffer, rect, 1.0, "R'G'B'A u8")  # pyright: ignore[reportPrivateUsage]

            # Read selection mask (single channel, 0-255)
            selection_data = ImageSplitter._buffer_get_bytes(selection_buffer, rect, 1.0, "Y u8")  # pyright: ignore[reportPrivateUsage]

            if pixel_data and selection_data:
                pixels = bytearray(pixel_data)
                mask = bytearray(selection_data)

                _debug_log(f"Processing {len(pixels) // 4} pixels, mask size={len(mask)}")

                # For each pixel, if it's selected (mask > 127), set alpha to 0
                modified_count = 0
                for i in range(len(mask)):
                    if mask[i] > 127:  # Pixel is selected
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
                _debug_log("Crop skipped (autocrop not available)")
        except Exception as e:
            _debug_log(f"Autocrop failed (non-critical): {e}")

        _debug_log("auto_cleanup_and_crop completed")

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
        everything outside the disc area.

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

        _debug_log("process_background completed")
