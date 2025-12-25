"""Template exporter procedure implementation."""

from __future__ import annotations

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gimp, Gtk


def run_template_exporter_dialog(image: Gimp.Image, _drawable: Gimp.Drawable | None) -> bool:
    """Run the template exporter dialog.

    Args:
        image: The image to export a template from.
        _drawable: The active drawable (unused).

    Returns:
        True if export completed, False if cancelled.
    """
    from tachograph_wizard.ui.template_exporter_dialog import TemplateExporterDialog

    dialog = TemplateExporterDialog(image)
    response = dialog.run()
    dialog.destroy()

    return response == Gtk.ResponseType.OK
