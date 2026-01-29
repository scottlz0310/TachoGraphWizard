"""Text inserter procedure implementation."""

from __future__ import annotations

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gimp, Gtk


def run_text_inserter_dialog(image: Gimp.Image, _drawable: Gimp.Drawable | None) -> bool:
    """Run the tachograph text inserter dialog.

    Args:
        image: The image to insert text into.
        drawable: The active drawable (may be None).

    Returns:
        True if text was inserted successfully, False if cancelled.
    """
    from tachograph_wizard.ui.text_inserter_dialog import TextInserterDialog

    dialog = TextInserterDialog(image)
    response = Gtk.ResponseType.CANCEL  # Default to CANCEL in case of exception
    try:
        response = dialog.run()
    finally:
        dialog.finalize_response(response)
        dialog.destroy()

    return response == Gtk.ResponseType.OK
