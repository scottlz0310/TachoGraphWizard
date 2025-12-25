"""Text inserter dialog for the Tachograph Text Inserter plugin."""

from __future__ import annotations

import datetime
import os
from pathlib import Path

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gimp, GimpUi, Gtk

from tachograph_wizard.core.csv_parser import CSVParser
from tachograph_wizard.core.template_manager import TemplateManager
from tachograph_wizard.core.text_renderer import TextRenderer


def _debug_log(message: str) -> None:
    """Write debug message to log file."""
    try:
        base = os.environ.get("TEMP") or os.environ.get("TMP") or os.environ.get("LOCALAPPDATA")
        if not base:
            return
        log_path = Path(base) / "tachograph_wizard.log"
        ts = datetime.datetime.now(tz=datetime.UTC).isoformat(timespec="seconds")
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{ts}] text_inserter_dialog: {message}\n")
    except Exception:
        return


class TextInserterDialog(GimpUi.Dialog):
    """Dialog for inserting text from CSV files using templates."""

    def __init__(self, image: Gimp.Image) -> None:
        """Initialize the dialog.

        Args:
            image: The GIMP image to insert text into.
        """
        super().__init__(
            title="Tachograph Text Inserter",
            role="tachograph-text-inserter",
        )

        self.image = image
        self.template_manager = TemplateManager()
        self.csv_data: list[dict[str, str]] = []
        self.current_row_index = 0

        # Set dialog properties
        self.set_default_size(500, 400)
        self.set_border_width(12)

        # Add action buttons
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("_OK", Gtk.ResponseType.OK)

        # Create UI
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the dialog UI."""
        content_area = self.get_content_area()
        content_area.set_spacing(12)

        # Welcome label
        welcome_label = Gtk.Label()
        welcome_label.set_markup(
            "<b>Tachograph Text Inserter</b>\n\nInsert text from CSV files using templates.",
        )
        welcome_label.set_line_wrap(True)
        content_area.pack_start(welcome_label, False, False, 0)

        # Template selection section
        template_frame = self._create_template_section()
        content_area.pack_start(template_frame, False, False, 0)

        # CSV file selection section
        csv_frame = self._create_csv_section()
        content_area.pack_start(csv_frame, False, False, 0)

        # Row selection section
        row_frame = self._create_row_section()
        content_area.pack_start(row_frame, False, False, 0)

        # Preview section
        preview_frame = self._create_preview_section()
        content_area.pack_start(preview_frame, True, True, 0)

        # Insert button
        insert_button = Gtk.Button(label="Insert Text")
        insert_button.connect("clicked", self._on_insert_clicked)
        content_area.pack_start(insert_button, False, False, 0)

        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_text("Ready")
        self.status_label.set_xalign(0.0)
        content_area.pack_start(self.status_label, False, False, 0)

        self.show_all()

    def _create_template_section(self) -> Gtk.Frame:
        """Create the template selection section."""
        frame = Gtk.Frame(label="Step 1: Select Template")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        # Template combo box
        combo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label(label="Template:")
        combo_box.pack_start(label, False, False, 0)

        self.template_combo = Gtk.ComboBoxText()
        templates = self.template_manager.list_templates()

        for template_name in templates:
            self.template_combo.append_text(template_name)

        # Select first template by default
        if templates:
            self.template_combo.set_active(0)

        combo_box.pack_start(self.template_combo, True, True, 0)
        box.pack_start(combo_box, False, False, 0)

        return frame

    def _create_csv_section(self) -> Gtk.Frame:
        """Create the CSV file selection section."""
        frame = Gtk.Frame(label="Step 2: Load CSV File")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        # CSV file chooser
        file_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label(label="CSV File:")
        file_box.pack_start(label, False, False, 0)

        self.csv_chooser = Gtk.FileChooserButton(
            title="Select CSV File",
            action=Gtk.FileChooserAction.OPEN,
        )

        # Add CSV filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        self.csv_chooser.add_filter(csv_filter)

        # Add all files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All files")
        all_filter.add_pattern("*")
        self.csv_chooser.add_filter(all_filter)

        file_box.pack_start(self.csv_chooser, True, True, 0)
        box.pack_start(file_box, False, False, 0)

        # Load button
        load_button = Gtk.Button(label="Load CSV")
        load_button.connect("clicked", self._on_load_csv_clicked)
        box.pack_start(load_button, False, False, 0)

        return frame

    def _create_row_section(self) -> Gtk.Frame:
        """Create the row selection section."""
        frame = Gtk.Frame(label="Step 3: Select Row")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        # Row spinner
        spinner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label(label="Row:")
        spinner_box.pack_start(label, False, False, 0)

        self.row_adjustment = Gtk.Adjustment(
            value=1,
            lower=1,
            upper=1,
            step_increment=1,
            page_increment=1,
        )
        self.row_spinner = Gtk.SpinButton(adjustment=self.row_adjustment, climb_rate=1, digits=0)
        self.row_spinner.connect("value-changed", self._on_row_changed)
        spinner_box.pack_start(self.row_spinner, True, True, 0)

        self.row_count_label = Gtk.Label(label="of 0")
        spinner_box.pack_start(self.row_count_label, False, False, 0)

        box.pack_start(spinner_box, False, False, 0)

        return frame

    def _create_preview_section(self) -> Gtk.Frame:
        """Create the preview section."""
        frame = Gtk.Frame(label="Preview")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        # Scrolled window for preview
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(150)

        # Preview text view
        self.preview_text = Gtk.TextView()
        self.preview_text.set_editable(False)
        self.preview_text.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(self.preview_text)

        box.pack_start(scrolled, True, True, 0)

        return frame

    def _on_load_csv_clicked(self, button: Gtk.Button) -> None:
        """Handle load CSV button click."""
        csv_path_str = self.csv_chooser.get_filename()
        if not csv_path_str:
            self._show_error("Please select a CSV file")
            return

        try:
            csv_path = Path(csv_path_str)
            self.csv_data = CSVParser.parse(csv_path)

            # Update row spinner
            row_count = len(self.csv_data)
            self.row_adjustment.set_upper(row_count)
            self.row_adjustment.set_value(1)
            self.row_count_label.set_text(f"of {row_count}")

            # Update preview
            self._update_preview()

            self.status_label.set_text(f"Loaded {row_count} rows from CSV")

        except (FileNotFoundError, ValueError) as e:
            self._show_error(f"Failed to load CSV: {e}")

    def _on_row_changed(self, spinner: Gtk.SpinButton) -> None:
        """Handle row spinner value change."""
        self.current_row_index = int(spinner.get_value()) - 1
        self._update_preview()

    def _update_preview(self) -> None:
        """Update the preview text view."""
        if not self.csv_data or self.current_row_index >= len(self.csv_data):
            self.preview_text.get_buffer().set_text("No data to preview")
            return

        row = self.csv_data[self.current_row_index]
        preview_lines = []
        for key, value in row.items():
            preview_lines.append(f"{key}: {value}")

        preview_text = "\n".join(preview_lines)
        self.preview_text.get_buffer().set_text(preview_text)

    def _on_insert_clicked(self, button: Gtk.Button) -> None:
        """Handle insert button click."""
        if not self.csv_data:
            self._show_error("Please load a CSV file first")
            return

        if self.current_row_index >= len(self.csv_data):
            self._show_error("Invalid row selected")
            return

        try:
            # Get selected template
            template_name = self.template_combo.get_active_text()

            if not template_name:
                self._show_error("Please select a template")
                return

            template_path = self.template_manager.get_template_path(template_name)
            template = self.template_manager.load_template(template_path)

            # Create text renderer
            renderer = TextRenderer(self.image, template)

            # Render text from current row
            row_data = self.csv_data[self.current_row_index]
            layers = renderer.render_from_csv_row(row_data)

            # Flush displays
            Gimp.displays_flush()

            self.status_label.set_text(f"Inserted {len(layers)} text layers")

        except Exception as e:
            _debug_log(f"ERROR: Insert failed: {e}")
            self._show_error(f"Failed to insert text: {e}")

    def _show_error(self, message: str) -> None:
        """Show error message dialog.

        Args:
            message: Error message to display.
        """
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
