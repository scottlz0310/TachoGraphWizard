"""Template exporter dialog for the Tachograph plugin."""

from __future__ import annotations

import datetime
import os
from pathlib import Path

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gimp, GimpUi, Gtk

from tachograph_wizard.core.template_exporter import TemplateExporter, TemplateExportError
from tachograph_wizard.core.template_manager import TemplateManager


def _debug_log(message: str) -> None:
    """Write debug message to log file."""
    base = os.environ.get("TEMP") or os.environ.get("TMP") or os.environ.get("LOCALAPPDATA")
    if not base:
        return
    log_path = Path(base) / "tachograph_wizard.log"
    try:
        ts = datetime.datetime.now(tz=datetime.UTC).isoformat(timespec="seconds")
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{ts}] template_exporter_dialog: {message}\n")
    except Exception:
        return


class TemplateExporterDialog(GimpUi.Dialog):
    """Dialog for exporting text layer templates."""

    def __init__(self, image: Gimp.Image) -> None:
        super().__init__(
            title="Tachograph Template Exporter",
            role="tachograph-template-exporter",
        )

        self.image = image
        self.exporter = TemplateExporter(image)
        self.template_manager = TemplateManager()

        self.set_default_size(520, 420)
        self.set_border_width(12)

        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("_OK", Gtk.ResponseType.OK)

        self._create_ui()

    def _create_ui(self) -> None:
        content_area = self.get_content_area()
        content_area.set_spacing(12)

        welcome_label = Gtk.Label()
        welcome_label.set_markup(
            "<b>Tachograph Template Exporter</b>\n\nExport text layer layout into a JSON template.",
        )
        welcome_label.set_line_wrap(True)
        content_area.pack_start(welcome_label, False, False, 0)

        name_frame = self._create_name_section()
        content_area.pack_start(name_frame, False, False, 0)

        save_frame = self._create_save_section()
        content_area.pack_start(save_frame, False, False, 0)

        preview_frame = self._create_preview_section()
        content_area.pack_start(preview_frame, True, True, 0)

        export_button = Gtk.Button(label="Export Template")
        export_button.connect("clicked", self._on_export_clicked)
        content_area.pack_start(export_button, False, False, 0)

        self.status_label = Gtk.Label()
        self.status_label.set_text("Ready")
        self.status_label.set_xalign(0.0)
        content_area.pack_start(self.status_label, False, False, 0)

        self._update_preview()
        self.show_all()

    def _create_name_section(self) -> Gtk.Frame:
        frame = Gtk.Frame(label="Template Details")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        name_label = Gtk.Label(label="Template Name:")
        name_label.set_xalign(0.0)
        name_box.pack_start(name_label, False, False, 0)

        self.name_entry = Gtk.Entry()
        self.name_entry.set_placeholder_text("template-name")
        name_box.pack_start(self.name_entry, True, True, 0)
        box.pack_start(name_box, False, False, 0)

        desc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        desc_label = Gtk.Label(label="Description:")
        desc_label.set_xalign(0.0)
        desc_box.pack_start(desc_label, False, False, 0)

        self.description_entry = Gtk.Entry()
        self.description_entry.set_placeholder_text("Optional description")
        desc_box.pack_start(self.description_entry, True, True, 0)
        box.pack_start(desc_box, False, False, 0)

        return frame

    def _create_save_section(self) -> Gtk.Frame:
        frame = Gtk.Frame(label="Save Location")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dir_label = Gtk.Label(label="Output Directory:")
        dir_label.set_xalign(0.0)
        dir_box.pack_start(dir_label, False, False, 0)

        self.output_dir_button = Gtk.FileChooserButton(
            title="Select Output Directory",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )

        default_dir = self.template_manager.get_templates_dir()
        if default_dir.exists():
            self.output_dir_button.set_current_folder(str(default_dir))
        else:
            self.output_dir_button.set_current_folder(str(Path.home()))

        dir_box.pack_start(self.output_dir_button, True, True, 0)
        box.pack_start(dir_box, False, False, 0)

        return frame

    def _create_preview_section(self) -> Gtk.Frame:
        frame = Gtk.Frame(label="Detected Fields")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(150)

        self.preview_text = Gtk.TextView()
        self.preview_text.set_editable(False)
        self.preview_text.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(self.preview_text)

        box.pack_start(scrolled, True, True, 0)
        return frame

    def _update_preview(self) -> None:
        names = self.exporter.list_field_names()
        if not names:
            self.preview_text.get_buffer().set_text("No text layers detected.")
            return

        preview_text = "\n".join(f"- {name}" for name in names)
        self.preview_text.get_buffer().set_text(preview_text)

    def _on_export_clicked(self, button: Gtk.Button) -> None:
        template_name = self.name_entry.get_text().strip()
        if not template_name:
            self._show_error("Please enter a template name")
            return
        if template_name.lower().endswith(".json"):
            template_name = template_name[:-5]

        output_dir = self.output_dir_button.get_filename()
        if not output_dir:
            self._show_error("Please select an output directory")
            return

        output_path = Path(output_dir) / f"{template_name}.json"

        if output_path.exists():
            if not self._confirm_overwrite(output_path):
                return

        try:
            description = self.description_entry.get_text().strip()
            self.exporter.export_template(
                template_name,
                output_path,
                description=description,
            )
            self.status_label.set_text(f"Exported template to {output_path}")
        except TemplateExportError as exc:
            _debug_log(f"Export failed: {exc}")
            self._show_error(str(exc))
        except Exception as exc:
            _debug_log(f"Unexpected export error: {exc}")
            self._show_error(f"Failed to export template: {exc}")

    def _confirm_overwrite(self, path: Path) -> bool:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Overwrite existing template?\n{path}",
        )
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.YES

    def _show_error(self, message: str) -> None:
        error_dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        error_dialog.run()
        error_dialog.destroy()

        self.status_label.set_text(f"Error: {message}")
