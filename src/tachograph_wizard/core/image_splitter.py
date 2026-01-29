"""Image splitting module for tachograph charts.

Provides functionality to split scanned images containing multiple
tachograph charts into individual images.
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import gi

gi.require_version("Gegl", "0.4")
gi.require_version("Gimp", "3.0")

from gi.repository import Gegl, Gimp, GObject

from tachograph_wizard.core.image_analysis import (
    Component,
    buffer_get_bytes,
    find_components,
    get_analysis_drawable,
    get_analysis_scale,
    get_image_dpi,
    otsu_threshold,
)
from tachograph_wizard.core.image_operations import (
    apply_component_mask,
    crop_image,
    duplicate_image,
)
from tachograph_wizard.core.pdb_runner import run_pdb_procedure

if TYPE_CHECKING:
    from tachograph_wizard.utils.types import SplitResult


# 後方互換性のためのエイリアス
_Component = Component


class ImageSplitter:
    """Split scanned images into individual tachograph charts."""

    _SPLIT_BY_GUIDES_LOG_VERSION = "2025-12-24.1"
    _DEFAULT_DIAMETER_MM = 123.5
    _MIN_DIAMETER_RATIO = 0.7
    _ANALYSIS_MAX_SIZE = 1200

    @staticmethod
    def _debug_log(message: str) -> None:
        try:
            base = os.environ.get("TEMP") or os.environ.get("TMP") or os.environ.get("LOCALAPPDATA")
            if not base:
                return
            log_path = Path(base) / "tachograph_wizard.log"
            ts = datetime.datetime.now(tz=datetime.UTC).isoformat(timespec="seconds")
            with log_path.open("a", encoding="utf-8") as log_file:
                log_file.write(f"[{ts}] image_splitter: {message}\n")
        except Exception:
            return

    @staticmethod
    def _analysis_scale(width: int, height: int) -> float:
        """後方互換性のためのラッパー."""
        return get_analysis_scale(width, height)

    @staticmethod
    def _get_image_dpi(image: Gimp.Image) -> float | None:
        """後方互換性のためのラッパー."""
        return get_image_dpi(image)

    @staticmethod
    def _get_analysis_drawable(image: Gimp.Image) -> Gimp.Drawable:
        """後方互換性のためのラッパー."""
        return get_analysis_drawable(image)

    @staticmethod
    def _buffer_get_bytes(
        buffer: Any,  # Gegl.Buffer - use Any to avoid import
        rect: Any,  # Gegl.Rectangle
        scale: float,
        fmt: str,
    ) -> bytes:
        """後方互換性のためのラッパー."""
        return buffer_get_bytes(buffer, rect, scale, fmt)

    @staticmethod
    def _otsu_threshold(hist: list[int], total: int) -> int:
        """後方互換性のためのラッパー."""
        return otsu_threshold(hist, total)

    @staticmethod
    def _find_components(mask: bytearray, width: int, height: int) -> list[_Component]:
        """後方互換性のためのラッパー."""
        return find_components(mask, width, height)

    @staticmethod
    def _duplicate_image(image: Gimp.Image) -> Gimp.Image:
        """後方互換性のためのラッパー."""
        return duplicate_image(image, debug_log=ImageSplitter._debug_log)

    @staticmethod
    def _crop_image(image: Gimp.Image, x: int, y: int, width: int, height: int) -> None:
        """後方互換性のためのラッパー."""
        crop_image(image, x, y, width, height, debug_log=ImageSplitter._debug_log)

    @staticmethod
    def _apply_component_mask(
        image: Gimp.Image,
        comp_mask: bytearray,
        mask_width: int,
        mask_height: int,
        crop_x: int,
        crop_y: int,
        scale_x: float,
        scale_y: float,
        threshold: int,
    ) -> None:
        """後方互換性のためのラッパー."""
        apply_component_mask(
            image,
            comp_mask,
            mask_width,
            mask_height,
            crop_x,
            crop_y,
            scale_x,
            scale_y,
            threshold,
            debug_log=ImageSplitter._debug_log,
        )

    @staticmethod
    def split_by_guides(image: Gimp.Image) -> list[Gimp.Image]:
        """Split image using existing guides.

        Uses GIMP's built-in guillotine functionality to slice the image
        along guide lines. The image must have guides already placed.

        Args:
            image: The image to split.

        Returns:
            List of newly created images from the split operation.

        Raises:
            ValueError: If no guides are found in the image.
        """
        # Check if image has guides.
        # In GIMP 3 Python bindings, find_next_guide() may return either a guide ID (int)
        # or a guide object depending on the build/bindings.
        # Additionally, some bindings expect the "start" id to be 0, others -1.

        def _debug_log(message: str) -> None:
            try:
                base = os.environ.get("TEMP") or os.environ.get("TMP") or os.environ.get("LOCALAPPDATA")
                if not base:
                    return
                log_path = Path(base) / "tachograph_wizard.log"
                ts = datetime.datetime.now(tz=datetime.UTC).isoformat(timespec="seconds")
                log_path.open("a", encoding="utf-8").write(f"[{ts}] image_splitter: {message}\n")
            except Exception:
                return

        def _safe_attr(obj: object, name: str) -> str:
            try:
                value = getattr(obj, name)
                if callable(value):
                    value = value()
                return str(value)
            except Exception:
                return "?"

        def _image_key(img_or_id: Any) -> tuple[str, object]:
            """Return a hashable identity for either a Gimp.Image or an image-id."""
            try:
                if isinstance(img_or_id, int):
                    return ("id", img_or_id)
                get_id = getattr(img_or_id, "get_id", None)
                if callable(get_id):
                    result = get_id()
                    return ("id", int(result) if isinstance(result, (int, float, str)) else result)
            except Exception:
                pass

            return ("repr", repr(img_or_id))

        def _try_list_images() -> list[Any] | None:
            """Best-effort image enumeration across GIMP 3 binding variants."""
            # In many GIMP 3 Python builds, Gimp.get_images() exists but Gimp.list_images() does not.
            for candidate in ("get_images", "list_images", "images"):
                fn = getattr(Gimp, candidate, None)
                if callable(fn):
                    try:
                        result: Any = fn()
                        images: list[Any] = list(result) if hasattr(result, "__iter__") else []
                        _debug_log(f"images_enum via Gimp.{candidate}() count={len(images)}")
                        return images
                    except Exception as e:
                        _debug_log(f"images_enum via Gimp.{candidate}() raised {type(e).__name__}: {e}")
                        continue
            _debug_log("images_enum: no supported Gimp.*images* API found")
            return None

        def _iter_values(value: Any, max_depth: int = 3, _depth: int = 0):
            """Walk nested result containers (ValueArray / lists) to find images."""
            yield value
            if _depth >= max_depth:
                return

            try:
                # Gimp.ValueArray / GLib containers often expose length() + index(i)
                length_fn = getattr(value, "length", None)
                index_fn = getattr(value, "index", None)
                if callable(length_fn) and callable(index_fn):
                    n = length_fn()
                    for i in range(int(n) if isinstance(n, (int, float)) else 0):
                        try:
                            yield from _iter_values(index_fn(i), max_depth=max_depth, _depth=_depth + 1)
                        except Exception:
                            continue
                    return
            except Exception:
                pass

            if isinstance(value, (list, tuple, set)):
                for item in value:
                    yield from _iter_values(item, max_depth=max_depth, _depth=_depth + 1)

        def _extract_images_from_result(result_obj: object) -> list[object]:
            images: list[object] = []
            seen: set[tuple[str, object]] = set()

            for v in _iter_values(result_obj):
                try:
                    # Prefer explicit Gimp.Image instances
                    if isinstance(v, Gimp.Image):
                        key = _image_key(v)
                        if key not in seen:
                            seen.add(key)
                            images.append(v)
                        continue

                    # Some bindings return images as objects with get_id()
                    if hasattr(v, "get_id"):
                        key = _image_key(v)
                        if key not in seen:
                            seen.add(key)
                            images.append(v)
                        continue
                except Exception:
                    continue

            return images

        def _has_any_guides(start_id: int) -> bool:
            guide_id = start_id
            while True:
                try:
                    guide = image.find_next_guide(guide_id)
                except Exception as e:
                    # Some GIMP 3 bindings raise if start_id is not a valid existing guide id
                    _debug_log(f"find_next_guide({guide_id}) raised {type(e).__name__}: {e}")
                    return False
                if guide in (None, 0, -1):
                    return False

                guide_id = guide.get_id() if hasattr(guide, "get_id") else int(guide)

                # Found at least one guide.
                return True

        has_guides_0 = _has_any_guides(0)
        # Only try -1 if 0 didn't work; some bindings error on -1.
        has_guides_m1 = _has_any_guides(-1) if not has_guides_0 else False
        has_guides = has_guides_0 or has_guides_m1

        _debug_log(
            " ".join(
                [
                    f"v={ImageSplitter._SPLIT_BY_GUIDES_LOG_VERSION}",
                    f"image_id={_safe_attr(image, 'get_id')}",
                    f"image_name={_safe_attr(image, 'get_name')}",
                    f"guide_scan start0={has_guides_0} start-1={has_guides_m1} => has_guides={has_guides}",
                ],
            ),
        )

        # Best-effort list of images before splitting (not available in all bindings)
        images_before_list = _try_list_images()
        images_before = {_image_key(i) for i in images_before_list} if images_before_list is not None else None
        if images_before_list is not None:
            _debug_log(
                f"images_before count={len(images_before_list)} sample_type="
                f"{type(images_before_list[0]).__name__ if images_before_list else 'n/a'}",
            )

        # Call guillotine procedure to split along guides
        try:
            result = run_pdb_procedure(
                "plug-in-guillotine",
                [
                    GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
                    GObject.Value(Gimp.Image, image),
                ],
                debug_log=_debug_log,
            )
        except Exception as e:
            _debug_log(f"guillotine: procedure call failed ({type(e).__name__}: {e})")
            msg = "Failed to run plug-in-guillotine (see %TEMP%\\tachograph_wizard.log)"
            raise RuntimeError(msg) from e

        try:
            length = getattr(result, "length", None)
            if callable(length):
                _debug_log(f"guillotine: result.length={length()}")
        except Exception as e:
            _debug_log(f"guillotine: unable to read result length ({type(e).__name__}: {e})")

        try:
            status = result.index(0)
        except Exception as e:
            _debug_log(f"guillotine: unable to read status from result ({type(e).__name__}: {e})")
            raise

        _debug_log(f"guillotine: status={status}")

        # Log a small preview of the returned ValueArray to learn the signature
        try:
            length_fn = getattr(result, "length", None)
            if callable(length_fn):
                n_raw = length_fn()
                n = int(n_raw) if isinstance(n_raw, (int, float)) else 0
                preview = []
                for i in range(min(n, 8)):
                    try:
                        item = result.index(i)
                        preview.append(f"{i}:{type(item).__name__}={repr(item)[:80]}")
                    except Exception as e:
                        preview.append(f"{i}:<err {type(e).__name__}> {e}")
                _debug_log("guillotine: result_preview " + " | ".join(preview))
        except Exception as e:
            _debug_log(f"guillotine: unable to preview result ({type(e).__name__}: {e})")

        # Check if procedure succeeded
        if status != Gimp.PDBStatusType.SUCCESS:
            # If we also couldn't detect guides, the likely cause is "no guides".
            if not has_guides:
                msg = "No guides found in image. Please add guides before splitting."
                raise ValueError(msg)

            msg = "Failed to split image using guides"
            raise RuntimeError(msg)

        # Try to detect created images.
        new_images: list[object] = []

        images_after_list = _try_list_images()
        if images_before is not None and images_after_list is not None:
            images_after = {_image_key(i) for i in images_after_list}
            _debug_log(
                f"images_after count={len(images_after_list)} sample_type="
                f"{type(images_after_list[0]).__name__ if images_after_list else 'n/a'}",
            )

            new_keys = list(images_after - images_before)
            after_by_key = {_image_key(i): i for i in images_after_list}
            new_images = [after_by_key[k] for k in new_keys if k in after_by_key]
        else:
            # Fallback: extract any returned images from the procedure result
            extracted = _extract_images_from_result(result)
            _debug_log(f"extracted_images_from_result count={len(extracted)}")
            new_images = extracted

        # Remove original image from list if it's still there (handle object vs id differences)
        original_key = _image_key(image)
        new_images = [img for img in new_images if _image_key(img) != original_key]

        _debug_log(f"new_images count={len(new_images)}")

        if not new_images:
            msg = "No guides found in image. Please add guides before splitting."
            raise ValueError(msg)

        # Narrow to Gimp.Image objects if possible (callers expect list[Gimp.Image])
        only_images: list[Gimp.Image] = []
        for img in new_images:
            try:
                if isinstance(img, Gimp.Image):
                    only_images.append(img)
            except Exception:
                continue

        if only_images:
            return only_images

        # As a last resort, return an empty list to avoid type confusion.
        msg = "Split produced results, but could not resolve created images in this binding"
        raise RuntimeError(msg)

    @staticmethod
    def split_by_auto_detect(
        image: Gimp.Image,
        pad_px: int = 20,
        threshold_bias: int | None = None,
        edge_trim_left: int = 0,  # noqa: ARG004 - kept for API compatibility
        edge_trim_right: int = 0,  # noqa: ARG004 - kept for API compatibility
        edge_trim_top: int = 0,  # noqa: ARG004 - kept for API compatibility
        edge_trim_bottom: int = 0,  # noqa: ARG004 - kept for API compatibility
    ) -> list[Gimp.Image]:
        """Auto-detect tachograph charts and split into separate images.

        Simple algorithm:
        1. Detect non-white regions using threshold (default 15)
        2. Find connected components
        3. Filter out small regions (< 1000px in either dimension)
        4. Crop each remaining region

        Args:
            image: The image to analyze.
            pad_px: Padding pixels to add around each detected disc (default 20).
            threshold_bias: Threshold for non-white detection (default 15).
                          Higher = more selective (only darker regions).
            edge_trim_left: Pixels trimmed from left edge (full-res).
            edge_trim_right: Pixels trimmed from right edge (full-res).
            edge_trim_top: Pixels trimmed from top edge (full-res).
            edge_trim_bottom: Pixels trimmed from bottom edge (full-res).

        Returns:
            List of newly created images from the split operation.

        Raises:
            ValueError: If no suitable chart regions are detected.
        """
        ImageSplitter._debug_log("auto_split: start")

        # Simple threshold for detecting light gray discs on white background
        # Default 15 works well for light gray (RGB ~240) on white (RGB 255)
        detection_threshold = threshold_bias if threshold_bias is not None else 15

        drawable = ImageSplitter._get_analysis_drawable(image)
        buffer = drawable.get_buffer()

        # Get image dimensions
        try:
            rect = buffer.get_extent()
            src_width = int(rect.width)
            src_height = int(rect.height)
        except Exception:
            src_width = drawable.get_width()
            src_height = drawable.get_height()
            try:
                rect = Gegl.Rectangle(x=0, y=0, width=src_width, height=src_height)
            except Exception:
                rect = Gegl.Rectangle()
                rect.x = 0
                rect.y = 0
                rect.width = src_width
                rect.height = src_height

        # Calculate minimum size for valid discs
        # 125mm disc at 300dpi is ~1476px, use 2/3 of that as minimum = ~984px
        # Default to 1000px, or calculate from DPI if available
        dpi = ImageSplitter._get_image_dpi(image)
        if dpi is not None and 50.0 <= dpi <= 1200.0:
            min_size = int(ImageSplitter._DEFAULT_DIAMETER_MM / 25.4 * dpi * 2 / 3)
        else:
            min_size = 1000  # Default for ~300dpi scans

        # Read full resolution data first (GIMP buffer doesn't support scaling in all versions)
        data_full = ImageSplitter._buffer_get_bytes(buffer, rect, 1.0, "R'G'B'A u8")

        # Calculate target analysis dimensions
        analysis_scale = ImageSplitter._analysis_scale(src_width, src_height)
        analysis_width = max(1, round(src_width * analysis_scale))
        analysis_height = max(1, round(src_height * analysis_scale))

        # Manual downsampling: sample every Nth pixel
        # This smooths noise and reduces processing time
        data = bytearray(analysis_width * analysis_height * 4)
        mv_full = memoryview(data_full)

        for ay in range(analysis_height):
            # Map analysis y to source y
            sy = int(ay * src_height / analysis_height)
            if sy >= src_height:
                sy = src_height - 1

            for ax in range(analysis_width):
                # Map analysis x to source x
                sx = int(ax * src_width / analysis_width)
                if sx >= src_width:
                    sx = src_width - 1

                # Copy pixel from source to downsampled
                src_offset = (sy * src_width + sx) * 4
                dst_offset = (ay * analysis_width + ax) * 4
                data[dst_offset : dst_offset + 4] = mv_full[src_offset : src_offset + 4]
        analysis_scale_x = analysis_width / src_width if src_width > 0 else 1.0
        analysis_scale_y = analysis_height / src_height if src_height > 0 else 1.0

        # Log configuration
        ImageSplitter._debug_log(
            f"auto_split: threshold={detection_threshold} min_size={min_size}px "
            f"dpi={dpi if dpi else 'unknown'} scale=({analysis_scale_x:.3f},{analysis_scale_y:.3f}) "
            f"analysis=({analysis_width}x{analysis_height})",
        )

        # Create simple binary mask: nonwhite >= threshold
        # For light gray discs on white background, this detects non-white regions
        mask = bytearray(analysis_width * analysis_height)
        foreground_count = 0

        mv = memoryview(data)

        # Simple threshold-based detection
        # nonwhite = 255 - min(R,G,B), so for light gray (240,240,240) nonwhite=15
        for y in range(analysis_height):
            row_offset = y * analysis_width
            for x in range(analysis_width):
                offset = (y * analysis_width + x) * 4
                r = mv[offset]
                g = mv[offset + 1]
                b = mv[offset + 2]
                a = mv[offset + 3]

                # Skip transparent pixels
                if a < 10:
                    continue

                # Calculate nonwhite: how far from pure white
                nonwhite = 255 - min(r, g, b)

                # Mark as foreground if nonwhite exceeds threshold
                if nonwhite >= detection_threshold:
                    mask[row_offset + x] = 1
                    foreground_count += 1

        if foreground_count == 0:
            msg = f"Auto split failed: no regions detected with threshold={detection_threshold}"
            raise ValueError(msg)

        # Find connected components in the mask
        components = ImageSplitter._find_components(mask, analysis_width, analysis_height)

        ImageSplitter._debug_log(f"auto_split: found {len(components)} components")

        # Simple size filter: keep only components where BOTH width AND height >= min_size
        # This filters out noise and small artifacts
        candidates: list[_Component] = []
        for comp in components:
            # Convert component dimensions to full resolution
            comp_width_full = int(comp.width / analysis_scale_x)
            comp_height_full = int(comp.height / analysis_scale_y)

            # Filter: keep only if BOTH width AND height >= min_size
            if comp_width_full >= min_size and comp_height_full >= min_size:
                candidates.append(comp)

        if not candidates:
            msg = f"Auto split failed: no regions >= {min_size}px found (found {len(components)} total components)"
            raise ValueError(msg)

        ImageSplitter._debug_log(f"auto_split: {len(candidates)} candidates after size filter (>={min_size}px)")

        # Sort candidates by position (top-to-bottom, left-to-right)
        candidates.sort(key=lambda comp: (comp.min_y, comp.min_x))

        # Add padding around detected components for better background removal
        # pad_px is now a parameter passed from the UI
        created: list[Gimp.Image] = []

        # Create a full-size mask to identify each component's pixels
        # We'll use this to remove garbage from cropped images
        component_masks: list[bytearray] = []
        for _comp_idx, comp in enumerate(candidates):
            # Create a mask for just this component
            comp_mask = bytearray(analysis_width * analysis_height)

            # Fill the mask by checking which pixels belong to this component
            # We need to re-run connected component detection to isolate this component
            # For efficiency, we'll mark all pixels within the component's bounding box
            # that are foreground pixels in the original mask
            for y in range(comp.min_y, comp.max_y + 1):
                row_offset = y * analysis_width
                for x in range(comp.min_x, comp.max_x + 1):
                    idx = row_offset + x
                    if mask[idx] == 1:  # Foreground pixel
                        # Check if this pixel is connected to the component
                        # For now, just include all foreground pixels in the bounding box
                        comp_mask[idx] = 1

            component_masks.append(comp_mask)

        # Crop each component
        for _comp_idx, comp in enumerate(candidates):
            x0 = int(comp.min_x / analysis_scale_x) - pad_px
            y0 = int(comp.min_y / analysis_scale_y) - pad_px
            x1 = int((comp.max_x + 1) / analysis_scale_x) + pad_px
            y1 = int((comp.max_y + 1) / analysis_scale_y) + pad_px

            x0 = max(0, x0)
            y0 = max(0, y0)
            x1 = min(image.get_width(), x1)
            y1 = min(image.get_height(), y1)

            width = max(1, x1 - x0)
            height = max(1, y1 - y0)

            # Duplicate and crop
            dup = ImageSplitter._duplicate_image(image)
            ImageSplitter._crop_image(dup, x0, y0, width, height)

            # NOTE: Auto garbage removal within Auto Split is disabled
            # Background removal is now handled by the separate Remove Background step

            created.append(dup)

        if not created:
            msg = "Auto split failed: no regions matched the size criteria"
            raise ValueError(msg)

        ImageSplitter._debug_log(f"auto_split: created={len(created)} images")
        return created

    @staticmethod
    def get_split_result(
        image: Gimp.Image,
        method: str = "guides",
    ) -> SplitResult:
        """Get split result with metadata.

        Args:
            image: The image to split.
            method: Splitting method ('guides' or 'auto').

        Returns:
            SplitResult dictionary containing images and method used.

        Raises:
            ValueError: If method is not recognized.
        """
        if method == "guides":
            images = ImageSplitter.split_by_guides(image)
        elif method == "auto":
            images = ImageSplitter.split_by_auto_detect(image)
        else:
            msg = f"Unknown splitting method: {method}"
            raise ValueError(msg)

        return {"images": images, "method": method}
