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
        threshold: int = 220,
    ) -> None:
        """Auto cleanup and crop using working layer analysis.

        Algorithm:
        1. Create working layer copy for analysis
        2. Convert to grayscale + median blur + threshold
        3. Select background (white) using flood fill from corners
        4. Invert selection to select disc
        5. Apply selection to original layer to clear garbage
        6. Crop to content
        7. Remove working layer

        Args:
            drawable: Target drawable (layer) to process.
            threshold: Threshold value (0-255) for binarization.
        """
        from tachograph_wizard.core.pdb_runner import run_pdb_procedure

        _debug_log(f"auto_cleanup_and_crop called: threshold={threshold}")

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

                pixel_data = ImageSplitter._buffer_get_bytes(buffer, full_rect, 1.0, "R'G'B'A u8")  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

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

        # 5. Select background (white) using fuzzy select from corners
        _debug_log("Selecting background from corners")
        width = image.get_width()
        height = image.get_height()
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
            except Exception as e:
                _debug_log(f"Failed to select from corner ({x}, {y}): {e}")

        if not selected:
            _debug_log("Failed to select background from any corner")
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

        # 9. Invert again to select garbage (everything outside disc)
        _debug_log("Inverting selection again to select garbage")
        run_pdb_procedure(
            "gimp-selection-invert",
            [GObject.Value(Gimp.Image, image)],
            debug_log=_debug_log,
        )

        # 10. Clear garbage on original drawable
        _debug_log("Clearing garbage on original layer")
        run_pdb_procedure(
            "gimp-drawable-edit-clear",
            [GObject.Value(Gimp.Drawable, drawable)],
            debug_log=_debug_log,
        )

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
            threshold: Color matching threshold (0-100) for selecting white.
        """
        from tachograph_wizard.core.pdb_runner import run_pdb_procedure

        _debug_log(f"remove_garbage_keep_largest_island called: threshold={threshold}")

        image = drawable.get_image()

        # Ensure layer has alpha channel
        if not drawable.has_alpha():
            drawable.add_alpha()

        # Step 1: First apply color-to-alpha to remove white background
        # This makes white areas transparent
        _debug_log("Applying color-to-alpha to remove white")
        BackgroundRemover.color_to_alpha(drawable, None, threshold)

        # Step 2: Select by alpha (select non-transparent areas = the disc and any noise)
        _debug_log("Selecting non-transparent areas")
        try:
            # Try GIMP 3.0 method: select-item
            run_pdb_procedure(
                "gimp-image-select-item",
                [
                    GObject.Value(Gimp.Image, image),
                    GObject.Value(Gimp.ChannelOps, Gimp.ChannelOps.REPLACE),
                    GObject.Value(Gimp.Item, drawable),
                ],
                debug_log=_debug_log,
            )
            _debug_log("Selected using gimp-image-select-item")
        except Exception as e:
            _debug_log(f"gimp-image-select-item failed: {e}, trying alternative")
            # Alternative: create selection from alpha
            run_pdb_procedure(
                "gimp-selection-all",
                [GObject.Value(Gimp.Image, image)],
                debug_log=_debug_log,
            )
            _debug_log("Selected all as fallback")

        # Step 3: Shrink then grow to remove small disconnected islands
        # This removes small noise while preserving the main disc
        _debug_log("Shrinking selection to remove small islands")
        run_pdb_procedure(
            "gimp-selection-shrink",
            [
                GObject.Value(Gimp.Image, image),
                GObject.Value(GObject.TYPE_INT, 10),  # Shrink by 10px
            ],
            debug_log=_debug_log,
        )

        _debug_log("Growing selection back")
        run_pdb_procedure(
            "gimp-selection-grow",
            [
                GObject.Value(Gimp.Image, image),
                GObject.Value(GObject.TYPE_INT, 10),  # Grow back by 10px
            ],
            debug_log=_debug_log,
        )

        # Step 4: Invert selection (now selecting garbage/noise)
        _debug_log("Inverting selection to select garbage")
        run_pdb_procedure(
            "gimp-selection-invert",
            [GObject.Value(Gimp.Image, image)],
            debug_log=_debug_log,
        )

        # Step 5: Clear the garbage (make it transparent)
        _debug_log("Clearing garbage")
        run_pdb_procedure(
            "gimp-drawable-edit-clear",
            [GObject.Value(Gimp.Drawable, drawable)],
            debug_log=_debug_log,
        )

        # Remove selection
        _debug_log("Removing selection")
        run_pdb_procedure(
            "gimp-selection-none",
            [GObject.Value(Gimp.Image, image)],
            debug_log=_debug_log,
        )

        _debug_log("remove_garbage_keep_largest_island completed")

    @staticmethod
    def process_background(
        drawable: Gimp.Drawable,
        remove_color: Gegl.Color | None = None,  # noqa: ARG004
        threshold: float = 15.0,
        apply_despeckle: bool = True,  # noqa: ARG004
        despeckle_radius: int = 2,  # noqa: ARG004
        use_island_method: bool = False,
    ) -> None:
        """Complete background removal process.

        Applies either island-based removal or color-to-alpha based removal.

        Args:
            drawable: Target drawable (layer) to process.
            remove_color: Color to remove (default: white).
            threshold: Color matching threshold (0-100).
            apply_despeckle: Whether to apply despeckle filter.
            despeckle_radius: Radius for despeckle operation.
            use_island_method: Use island-based removal (DISABLED - has issues).
        """
        _debug_log(f"process_background called: threshold={threshold}, use_island_method={use_island_method}")

        # Use new working-layer-based cleanup method
        # Threshold determines what's background: threshold-255 = white (background), 0-(threshold-1) = black (disc)
        # Convert float threshold (0-100) to int (0-255) if needed
        threshold_int = int(threshold) if threshold <= 100 else int(threshold * 2.55)
        threshold_int = max(0, min(255, threshold_int))  # Clamp to 0-255
        _debug_log(f"Using threshold={threshold_int} for auto_cleanup_and_crop")
        BackgroundRemover.auto_cleanup_and_crop(drawable, threshold=threshold_int)

        _debug_log("process_background completed")
