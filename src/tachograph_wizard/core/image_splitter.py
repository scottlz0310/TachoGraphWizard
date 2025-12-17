"""Image splitting module for tachograph charts.

Provides functionality to split scanned images containing multiple
tachograph charts into individual images.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gimp", "3.0")

from gi.repository import Gimp, GObject

if TYPE_CHECKING:
    from tachograph_wizard.utils.types import SplitResult


class ImageSplitter:
    """Split scanned images into individual tachograph charts."""

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
        # Check if image has guides
        has_guides = False
        guide_id = 0

        # Iterate through guides to check if any exist
        while True:
            guide = image.find_next_guide(guide_id)
            if guide is None:
                break
            has_guides = True
            guide_id = guide.get_id()

        if not has_guides:
            msg = "No guides found in image. Please add guides before splitting."
            raise ValueError(msg)

        # Get list of images before splitting
        images_before = set(Gimp.list_images())

        # Call guillotine procedure to split along guides
        pdb = Gimp.get_pdb()
        result = pdb.run_procedure(
            "plug-in-guillotine",
            [
                GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
                GObject.Value(Gimp.Image, image),
            ],
        )

        # Check if procedure succeeded
        if result.index(0) != Gimp.PDBStatusType.SUCCESS:
            msg = "Failed to split image using guides"
            raise RuntimeError(msg)

        # Get list of images after splitting
        images_after = set(Gimp.list_images())

        # Return newly created images
        new_images = list(images_after - images_before)

        # Remove original image from list if it's still there
        if image in new_images:
            new_images.remove(image)

        return new_images

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
