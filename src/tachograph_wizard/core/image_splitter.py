"""Image splitting module for tachograph charts.

Provides functionality to split scanned images containing multiple
tachograph charts into individual images.
"""

from __future__ import annotations

import datetime
import math
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import gi

gi.require_version("Gegl", "0.4")
gi.require_version("Gimp", "3.0")

import os

from gi.repository import Gegl, Gimp, GObject

from tachograph_wizard.core.pdb_runner import run_pdb_procedure

if TYPE_CHECKING:
    from tachograph_wizard.utils.types import SplitResult


@dataclass
class _Component:
    min_x: int
    min_y: int
    max_x: int
    max_y: int
    area: int

    @property
    def width(self) -> int:
        return self.max_x - self.min_x + 1

    @property
    def height(self) -> int:
        return self.max_y - self.min_y + 1

    @property
    def diameter(self) -> int:
        return max(self.width, self.height)


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
        max_dim = max(width, height)
        if max_dim <= 0:
            return 1.0
        return min(1.0, ImageSplitter._ANALYSIS_MAX_SIZE / max_dim)

    @staticmethod
    def _get_image_dpi(image: Gimp.Image) -> float | None:
        try:
            resolution = image.get_resolution()
        except Exception:
            resolution = None

        if isinstance(resolution, (tuple, list)) and len(resolution) >= 2:
            try:
                x_res = float(resolution[0])
                y_res = float(resolution[1])
                dpi = y_res if y_res > 0 else x_res
                if 50.0 <= dpi <= 1200.0:
                    return dpi
            except (TypeError, ValueError):
                return None

        return None

    @staticmethod
    def _get_analysis_drawable(image: Gimp.Image) -> Gimp.Drawable:
        try:
            drawable = image.get_active_drawable()
            if drawable is not None:
                return drawable
        except Exception:
            pass

        layers = image.get_layers()
        if not layers:
            msg = "No layers available for analysis"
            raise RuntimeError(msg)
        return layers[0]

    @staticmethod
    def _buffer_get_bytes(
        buffer: Gegl.Buffer,
        rect: Gegl.Rectangle,
        scale: float,
        fmt: str,
    ) -> bytes:
        attempts = [
            (rect, scale, fmt, Gegl.AbyssPolicy.CLAMP),
            (rect, scale, fmt),
            (rect, fmt, Gegl.AbyssPolicy.CLAMP),
            (rect, fmt),
        ]
        last_error: Exception | None = None
        for args in attempts:
            try:
                data = buffer.get(*args)
                if isinstance(data, (bytes, bytearray)):
                    return bytes(data)
                get_data = getattr(data, "get_data", None)
                if callable(get_data):
                    return bytes(get_data())
                return bytes(data)
            except Exception as exc:
                last_error = exc
                continue
        msg = f"Failed to read buffer data ({type(last_error).__name__}: {last_error})"
        raise RuntimeError(msg)

    @staticmethod
    def _otsu_threshold(hist: list[int], total: int) -> int:
        if total <= 0:
            return 255
        sum_total = sum(i * hist[i] for i in range(256))
        sum_back = 0
        weight_back = 0
        max_var = -1.0
        threshold = 200

        for t in range(256):
            weight_back += hist[t]
            if weight_back == 0:
                continue
            weight_fore = total - weight_back
            if weight_fore == 0:
                break
            sum_back += t * hist[t]
            mean_back = sum_back / weight_back
            mean_fore = (sum_total - sum_back) / weight_fore
            between_var = weight_back * weight_fore * (mean_back - mean_fore) ** 2
            if between_var > max_var:
                max_var = between_var
                threshold = t

        return threshold

    @staticmethod
    def _find_components(mask: bytearray, width: int, height: int) -> list[_Component]:
        visited = bytearray(len(mask))
        components: list[_Component] = []

        for idx, value in enumerate(mask):
            if value == 0 or visited[idx]:
                continue

            stack = [idx]
            visited[idx] = 1
            min_x = max_x = idx % width
            min_y = max_y = idx // width
            area = 0

            while stack:
                current = stack.pop()
                x = current % width
                y = current // width
                area += 1
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

                left = current - 1
                right = current + 1
                up = current - width
                down = current + width

                if x > 0 and mask[left] and not visited[left]:
                    visited[left] = 1
                    stack.append(left)
                if x < width - 1 and mask[right] and not visited[right]:
                    visited[right] = 1
                    stack.append(right)
                if y > 0 and mask[up] and not visited[up]:
                    visited[up] = 1
                    stack.append(up)
                if y < height - 1 and mask[down] and not visited[down]:
                    visited[down] = 1
                    stack.append(down)

            components.append(_Component(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y, area=area))

        return components

    @staticmethod
    def _duplicate_image(image: Gimp.Image) -> Gimp.Image:
        dup_fn = getattr(image, "duplicate", None)
        if callable(dup_fn):
            return dup_fn()

        result = run_pdb_procedure(
            "gimp-image-duplicate",
            [GObject.Value(Gimp.Image, image)],
            debug_log=ImageSplitter._debug_log,
        )
        return result.index(1)

    @staticmethod
    def _crop_image(image: Gimp.Image, x: int, y: int, width: int, height: int) -> None:
        crop_fn = getattr(image, "crop", None)
        if callable(crop_fn):
            crop_fn(width, height, x, y)
            return

        run_pdb_procedure(
            "gimp-image-crop",
            [
                GObject.Value(Gimp.Image, image),
                GObject.Value(GObject.TYPE_INT, width),
                GObject.Value(GObject.TYPE_INT, height),
                GObject.Value(GObject.TYPE_INT, x),
                GObject.Value(GObject.TYPE_INT, y),
            ],
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
        threshold_bias: int | None = None,
        edge_trim_left: int = 0,
        edge_trim_right: int = 0,
        edge_trim_top: int = 0,
        edge_trim_bottom: int = 0,
    ) -> list[Gimp.Image]:
        """Auto-detect tachograph charts and split into separate images.

        Uses a downsampled mask + connected components to locate large
        circular regions, then crops each region from the source image.

        Args:
            image: The image to analyze.
            threshold_bias: Optional threshold bias (0-255, added to auto threshold).
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

        drawable = ImageSplitter._get_analysis_drawable(image)
        buffer = drawable.get_buffer()
        scale = ImageSplitter._analysis_scale(drawable.get_width(), drawable.get_height())

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

        data = ImageSplitter._buffer_get_bytes(buffer, rect, scale, "R'G'B'A u8")
        out_width = max(1, round(src_width * scale))
        out_height = max(1, round(src_height * scale))
        pixel_count = len(data) // 4
        if pixel_count <= 0:
            msg = "Auto split failed: empty buffer"
            raise ValueError(msg)

        expected_pixels = out_width * out_height
        if expected_pixels != pixel_count:
            ratio = src_width / src_height if src_height > 0 else 1.0
            out_width = max(1, round(math.sqrt(pixel_count * ratio)))
            out_height = max(1, math.ceil(pixel_count / out_width))
            expected_pixels = out_width * out_height
            ImageSplitter._debug_log(
                "auto_split: resized mask to match buffer "
                f"(pixels={pixel_count} width={out_width} height={out_height})",
            )

        buffer_width = out_width
        buffer_height = out_height
        buffer_scale_x = buffer_width / src_width if src_width > 0 else 1.0
        buffer_scale_y = buffer_height / src_height if src_height > 0 else 1.0

        analysis_scale = ImageSplitter._analysis_scale(buffer_width, buffer_height)
        analysis_width = max(1, round(buffer_width * analysis_scale))
        analysis_height = max(1, round(buffer_height * analysis_scale))

        analysis_scale_x = analysis_width / src_width if src_width > 0 else analysis_scale
        analysis_scale_y = analysis_height / src_height if src_height > 0 else analysis_scale

        left_trim_scaled = max(0, round(edge_trim_left * analysis_scale_x))
        right_trim_scaled = max(0, round(edge_trim_right * analysis_scale_x))
        top_trim_scaled = max(0, round(edge_trim_top * analysis_scale_y))
        bottom_trim_scaled = max(0, round(edge_trim_bottom * analysis_scale_y))

        x_min = left_trim_scaled
        x_max = analysis_width - right_trim_scaled
        y_min = top_trim_scaled
        y_max = analysis_height - bottom_trim_scaled

        if x_min >= x_max or y_min >= y_max:
            msg = "Auto split failed: edge trim too large"
            raise ValueError(msg)

        mv = memoryview(data)
        hist_luma = [0] * 256
        hist_nonwhite = [0] * 256
        total_pixels = 0

        x_ranges: list[tuple[int, int]] = []
        for x in range(analysis_width):
            x0 = int(x * buffer_width / analysis_width)
            x1 = int((x + 1) * buffer_width / analysis_width)
            if x1 <= x0:
                x1 = min(buffer_width, x0 + 1)
            x_ranges.append((x0, x1))

        y_ranges: list[tuple[int, int]] = []
        for y in range(analysis_height):
            y0 = int(y * buffer_height / analysis_height)
            y1 = int((y + 1) * buffer_height / analysis_height)
            if y1 <= y0:
                y1 = min(buffer_height, y0 + 1)
            y_ranges.append((y0, y1))

        def _rgba_at(x: int, y: int) -> tuple[int, int, int, int]:
            offset = (y * buffer_width + x) * 4
            r = mv[offset]
            g = mv[offset + 1]
            b = mv[offset + 2]
            a = mv[offset + 3]
            return r, g, b, a

        def _luma_from_rgba(r: int, g: int, b: int, a: int) -> int:
            if a < 10:
                return 255
            return (r * 2126 + g * 7152 + b * 722) // 10000

        def _nonwhite_from_rgba(r: int, g: int, b: int, a: int) -> int:
            if a < 10:
                return 0
            return 255 - min(r, g, b)

        def _sample_metrics(x0: int, x1m: int, y0: int, y1m: int, xc: int, yc: int) -> tuple[int, int]:
            coords = ((x0, y0), (x1m, y0), (x0, y1m), (x1m, y1m), (xc, yc))
            luma_sum = 0
            nonwhite_sum = 0
            for sx, sy in coords:
                r, g, b, a = _rgba_at(sx, sy)
                luma_sum += _luma_from_rgba(r, g, b, a)
                nonwhite_sum += _nonwhite_from_rgba(r, g, b, a)
            return luma_sum // 5, nonwhite_sum // 5

        for y in range(analysis_height):
            if y < y_min or y >= y_max:
                continue
            y0, y1 = y_ranges[y]
            y1m = y1 - 1
            yc = (y0 + y1m) // 2
            for x in range(analysis_width):
                if x < x_min or x >= x_max:
                    continue
                x0, x1 = x_ranges[x]
                x1m = x1 - 1
                xc = (x0 + x1m) // 2
                luma, nonwhite = _sample_metrics(x0, x1m, y0, y1m, xc, yc)
                hist_luma[int(luma)] += 1
                hist_nonwhite[int(nonwhite)] += 1
                total_pixels += 1

        luma_threshold = ImageSplitter._otsu_threshold(hist_luma, total_pixels)
        nonwhite_threshold = ImageSplitter._otsu_threshold(hist_nonwhite, total_pixels)
        nonwhite_threshold = max(1, nonwhite_threshold)
        if threshold_bias is not None:
            luma_threshold = min(255, luma_threshold + threshold_bias)
            nonwhite_threshold = max(1, nonwhite_threshold - threshold_bias)

        ImageSplitter._debug_log(
            "auto_split: threshold="
            f"{luma_threshold} bias={threshold_bias or 0} "
            f"nonwhite_threshold={nonwhite_threshold} "
            f"scale=({analysis_scale_x:.3f},{analysis_scale_y:.3f}) "
            f"buffer_scale=({buffer_scale_x:.3f},{buffer_scale_y:.3f}) "
            f"trim=({edge_trim_left},{edge_trim_right},{edge_trim_top},{edge_trim_bottom}) "
            f"analysis=({analysis_width}x{analysis_height})",
        )

        mask_luma = bytearray(analysis_width * analysis_height)
        mask_nonwhite = bytearray(analysis_width * analysis_height)
        foreground_count = 0
        foreground_count_nonwhite = 0
        for y in range(analysis_height):
            if y < y_min or y >= y_max:
                continue
            y0, y1 = y_ranges[y]
            y1m = y1 - 1
            yc = (y0 + y1m) // 2
            row_offset = y * analysis_width
            for x in range(analysis_width):
                if x < x_min or x >= x_max:
                    continue
                x0, x1 = x_ranges[x]
                x1m = x1 - 1
                xc = (x0 + x1m) // 2
                luma, nonwhite = _sample_metrics(x0, x1m, y0, y1m, xc, yc)
                idx = row_offset + x
                if luma < luma_threshold:
                    mask_luma[idx] = 1
                    foreground_count += 1
                if nonwhite >= nonwhite_threshold:
                    mask_nonwhite[idx] = 1
                    foreground_count_nonwhite += 1

        if foreground_count == 0 and foreground_count_nonwhite == 0:
            msg = "Auto split failed: no foreground regions detected"
            raise ValueError(msg)

        components_luma = (
            ImageSplitter._find_components(mask_luma, analysis_width, analysis_height)
            if foreground_count > 0
            else []
        )
        components_nonwhite = (
            ImageSplitter._find_components(mask_nonwhite, analysis_width, analysis_height)
            if foreground_count_nonwhite > 0
            else []
        )

        def _select_candidates(
            components: list[_Component],
            metric_label: str,
        ) -> tuple[list[_Component], float]:
            if not components:
                ImageSplitter._debug_log(
                    f"auto_split: {metric_label} components=0 candidates=0",
                )
                return [], 0.0

            non_edge_components = [
                comp
                for comp in components
                if comp.min_x > x_min
                and comp.max_x < x_max - 1
                and comp.min_y > y_min
                and comp.max_y < y_max - 1
            ]

            max_component = max(non_edge_components or components, key=lambda comp: comp.area)
            min_dim = min(analysis_width, analysis_height)
            min_roundish = max(8.0, min_dim * 0.08)
            roundish = []
            for comp in non_edge_components:
                if comp.width <= 0 or comp.height <= 0:
                    continue
                ratio = comp.width / comp.height if comp.height else 0.0
                ratio = max(ratio, 1.0 / ratio) if ratio > 0 else 999.0
                if ratio > 1.6:
                    continue
                if comp.diameter < min_roundish:
                    continue
                roundish.append(comp)

            expected_diameter_components = None
            if roundish:
                diameters = sorted(comp.diameter for comp in roundish)
                median = diameters[len(diameters) // 2]
                expected_diameter_components = median / min(analysis_scale_x, analysis_scale_y)

            dpi = ImageSplitter._get_image_dpi(image)
            expected_diameter_dpi = None
            if dpi is not None:
                expected_diameter_dpi = ImageSplitter._DEFAULT_DIAMETER_MM / 25.4 * dpi

            if expected_diameter_components is not None:
                if expected_diameter_dpi is None:
                    expected_diameter = expected_diameter_components
                    ImageSplitter._debug_log(
                        f"auto_split: {metric_label} median diameter="
                        f"{expected_diameter:.1f} from {len(roundish)} comps",
                    )
                else:
                    ratio = expected_diameter_dpi / expected_diameter_components
                    if ratio > 1.4 or ratio < 0.7:
                        expected_diameter = expected_diameter_components
                        ImageSplitter._debug_log(
                            f"auto_split: {metric_label} dpi mismatch, using median diameter="
                            f"{expected_diameter:.1f} (dpi={expected_diameter_dpi:.1f})",
                        )
                    else:
                        expected_diameter = expected_diameter_dpi
            elif expected_diameter_dpi is not None:
                expected_diameter = expected_diameter_dpi
            else:
                expected_diameter = max_component.diameter / min(analysis_scale_x, analysis_scale_y)
                ImageSplitter._debug_log(
                    f"auto_split: {metric_label} fallback diameter="
                    f"{expected_diameter:.1f}",
                )

            min_diameter = expected_diameter * ImageSplitter._MIN_DIAMETER_RATIO
            min_diameter_scaled_x = min_diameter * analysis_scale_x
            min_diameter_scaled_y = min_diameter * analysis_scale_y
            min_box_scaled_x = min_diameter_scaled_x * 0.8
            min_box_scaled_y = min_diameter_scaled_y * 0.8

            candidates = []
            for comp in components:
                if comp.width < min_box_scaled_x or comp.height < min_box_scaled_y:
                    continue
                if comp.min_x < x_min or comp.max_x >= x_max:
                    continue
                if comp.min_y < y_min or comp.max_y >= y_max:
                    continue
                ratio = comp.width / comp.height if comp.height else 0.0
                ratio = max(ratio, 1.0 / ratio) if ratio > 0 else 999.0
                if ratio > 1.6:
                    continue
                coverage = comp.area / (comp.width * comp.height)
                if coverage < 0.2:
                    continue
                candidates.append(comp)

            avg_coverage = 0.0
            if candidates:
                avg_coverage = sum(comp.area / (comp.width * comp.height) for comp in candidates) / len(candidates)
            ImageSplitter._debug_log(
                f"auto_split: {metric_label} components={len(components)} "
                f"candidates={len(candidates)} coverage={avg_coverage:.3f}",
            )
            return candidates, expected_diameter

        candidates_luma, diameter_luma = _select_candidates(components_luma, "luma")
        candidates_nonwhite, diameter_nonwhite = _select_candidates(components_nonwhite, "nonwhite")

        def _score(candidates: list[_Component]) -> tuple[int, float]:
            if not candidates:
                return (0, 0.0)
            avg_coverage = sum(comp.area / (comp.width * comp.height) for comp in candidates) / len(candidates)
            return (len(candidates), avg_coverage)

        score_luma = _score(candidates_luma)
        score_nonwhite = _score(candidates_nonwhite)

        if score_nonwhite > score_luma:
            candidates = candidates_nonwhite
            expected_diameter = diameter_nonwhite
            metric = "nonwhite"
        else:
            candidates = candidates_luma
            expected_diameter = diameter_luma
            metric = "luma"

        if candidates:
            ImageSplitter._debug_log(f"auto_split: selected metric={metric}")
        if not candidates:
            msg = "Auto split failed: no chart-sized regions detected"
            raise ValueError(msg)

        candidates.sort(key=lambda comp: (comp.min_y, comp.min_x))

        pad_px = max(2, int(expected_diameter * 0.02))
        created: list[Gimp.Image] = []
        for comp in candidates:
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

            dup = ImageSplitter._duplicate_image(image)
            ImageSplitter._crop_image(dup, x0, y0, width, height)
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
