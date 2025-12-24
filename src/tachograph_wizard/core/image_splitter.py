"""Image splitting module for tachograph charts.

Provides functionality to split scanned images containing multiple
tachograph charts into individual images.
"""

from __future__ import annotations

import os
import datetime
from typing import TYPE_CHECKING

import gi

gi.require_version("Gimp", "3.0")

from gi.repository import Gimp, GObject

from tachograph_wizard.core.pdb_runner import run_pdb_procedure

if TYPE_CHECKING:
    from tachograph_wizard.utils.types import SplitResult


class ImageSplitter:
    """Split scanned images into individual tachograph charts."""

    _SPLIT_BY_GUIDES_LOG_VERSION = "2025-12-24.1"

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
                log_path = os.path.join(base, "tachograph_wizard.log")
                ts = datetime.datetime.now().isoformat(timespec="seconds")
                with open(log_path, "a", encoding="utf-8") as fp:
                    fp.write(f"[{ts}] image_splitter: {message}\n")
            except Exception:
                return

        def _safe_attr(obj: object, name: str) -> str:
            try:
                value = getattr(obj, name)  # noqa: B009
                if callable(value):
                    value = value()
                return str(value)
            except Exception:
                return "?"

        def _image_key(img_or_id: object) -> tuple[str, object]:
            """Return a hashable identity for either a Gimp.Image or an image-id."""
            try:
                if isinstance(img_or_id, int):
                    return ("id", int(img_or_id))
                get_id = getattr(img_or_id, "get_id", None)
                if callable(get_id):
                    return ("id", int(get_id()))
            except Exception:
                pass

            return ("repr", repr(img_or_id))

        def _try_list_images() -> list[object] | None:
            """Best-effort image enumeration across GIMP 3 binding variants."""
            # In many GIMP 3 Python builds, Gimp.get_images() exists but Gimp.list_images() does not.
            for candidate in ("get_images", "list_images", "images"):
                fn = getattr(Gimp, candidate, None)
                if callable(fn):
                    try:
                        images = list(fn())
                        _debug_log(f"images_enum via Gimp.{candidate}() count={len(images)}")
                        return images
                    except Exception as e:
                        _debug_log(f"images_enum via Gimp.{candidate}() raised {type(e).__name__}: {e}")
                        continue
            _debug_log("images_enum: no supported Gimp.*images* API found")
            return None

        def _iter_values(value: object, max_depth: int = 3, _depth: int = 0):
            """Walk nested result containers (ValueArray / lists) to find images."""
            yield value
            if _depth >= max_depth:
                return

            try:
                # Gimp.ValueArray / GLib containers often expose length() + index(i)
                length = getattr(value, "length", None)
                index = getattr(value, "index", None)
                if callable(length) and callable(index):
                    for i in range(int(length())):
                        try:
                            yield from _iter_values(index(i), max_depth=max_depth, _depth=_depth + 1)
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

                if hasattr(guide, "get_id"):
                    guide_id = guide.get_id()  # type: ignore[assignment]
                else:
                    guide_id = int(guide)

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
                ]
            )
        )

        # Best-effort list of images before splitting (not available in all bindings)
        images_before_list = _try_list_images()
        images_before = {_image_key(i) for i in images_before_list} if images_before_list is not None else None
        if images_before_list is not None:
            _debug_log(
                f"images_before count={len(images_before_list)} sample_type="
                f"{type(images_before_list[0]).__name__ if images_before_list else 'n/a'}"
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
            length = getattr(result, "length", None)
            if callable(length):
                n = int(length())
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
                f"{type(images_after_list[0]).__name__ if images_after_list else 'n/a'}"
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
        min_radius: int = 500,
        max_radius: int = 800,
    ) -> list[tuple[int, int, int]]:
        """Auto-detect circular tachograph charts.

        This feature will be implemented in Phase 5. It will use edge
        detection and Hough circle transform to automatically locate
        circular tachograph charts in the scanned image.

        Args:
            image: The image to analyze.
            min_radius: Minimum circle radius to detect.
            max_radius: Maximum circle radius to detect.

        Returns:
            List of (x, y, radius) tuples representing detected circles.

        Raises:
            NotImplementedError: This feature is planned for Phase 5.
        """
        msg = "Auto-detection will be implemented in Phase 5"
        raise NotImplementedError(msg)

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
            msg = "Auto-detection not yet implemented"
            raise NotImplementedError(msg)
        else:
            msg = f"Unknown splitting method: {method}"
            raise ValueError(msg)

        return {"images": images, "method": method}
