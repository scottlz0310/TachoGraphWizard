"""Text inserter dialog for the Tachograph Text Inserter plugin."""

from __future__ import annotations

import datetime
import os
from pathlib import Path
from typing import ClassVar

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GLib", "2.0")

from gi.repository import Gimp, GimpUi, GLib, Gtk

from tachograph_wizard.core.settings_manager import (
    load_csv_path,
    load_filename_fields,
    load_last_used_date,
    load_output_dir,
    load_template_dir,
    load_window_size,
    save_filename_fields,
    save_last_used_date,
    save_template_dir,
    save_window_size,
)
from tachograph_wizard.core.template_manager import TemplateManager
from tachograph_wizard.core.text_insert_usecase import CsvDateError, TextInsertUseCase


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

    # Available filename fields for user selection
    FILENAME_FIELD_OPTIONS: ClassVar[list[tuple[str, str]]] = [
        ("date", "Date (from calendar)"),
        ("vehicle_no", "Vehicle Number"),
        ("driver", "Driver Name"),
    ]

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
        self.default_templates_dir = self.template_manager.get_templates_dir()
        self.template_dir = load_template_dir(self.default_templates_dir)
        self.template_paths: dict[str, Path] = {}
        self.csv_data: list[dict[str, str]] = []
        self.current_row_index = 0
        self.default_date = load_last_used_date() or datetime.date.today()
        self.last_csv_path = load_csv_path()
        self.output_dir = load_output_dir() or Path.home()
        self.filename_field_checks: dict[str, Gtk.CheckButton] = {}
        self._resize_save_timeout_id: int | None = None
        self._inserted_layers: list[Gimp.Layer] = []  # Track layers added during session

        # Load and set window size
        width, height = load_window_size()
        self.set_default_size(width, height)
        self.set_border_width(12)

        # Connect to configure-event to save size changes
        self.connect("configure-event", self._on_configure_event)

        # Add action buttons
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("_OK", Gtk.ResponseType.OK)

        # Create UI
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the dialog UI."""
        content_area = self.get_content_area()
        content_area.set_spacing(12)

        # Create a scrolled window for the entire content
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(500)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_border_width(6)

        # Welcome label
        welcome_label = Gtk.Label()
        welcome_label.set_markup(
            "<b>Tachograph Text Inserter</b>\n\nInsert text from CSV files using templates.",
        )
        welcome_label.set_line_wrap(True)
        main_box.pack_start(welcome_label, False, False, 0)

        # Template selection section
        template_frame = self._create_template_section()
        main_box.pack_start(template_frame, False, False, 0)

        # CSV file selection section
        csv_frame = self._create_csv_section()
        main_box.pack_start(csv_frame, False, False, 0)

        # Date selection section
        date_frame = self._create_date_section()
        main_box.pack_start(date_frame, False, False, 0)

        # Row selection section
        row_frame = self._create_row_section()
        main_box.pack_start(row_frame, False, False, 0)

        # Preview section
        preview_frame = self._create_preview_section()
        main_box.pack_start(preview_frame, False, False, 0)

        # Insert button
        insert_button = Gtk.Button(label="Insert Text")
        insert_button.connect("clicked", self._on_insert_clicked)
        main_box.pack_start(insert_button, False, False, 0)

        # Save section
        save_frame = self._create_save_section()
        main_box.pack_start(save_frame, False, False, 0)

        scrolled_window.add(main_box)
        content_area.pack_start(scrolled_window, True, True, 0)

        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_text("Ready")
        self.status_label.set_xalign(0.0)
        content_area.pack_start(self.status_label, False, False, 0)

        self._refresh_template_list(self.template_dir)
        self.show_all()

    def _create_template_section(self) -> Gtk.Frame:
        """Create the template selection section."""
        frame = Gtk.Frame(label="Step 1: Select Template")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dir_label = Gtk.Label(label="Template Folder:")
        dir_box.pack_start(dir_label, False, False, 0)

        self.template_dir_button = Gtk.FileChooserButton(
            title="Select Template Folder",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        if self.template_dir.exists():
            self.template_dir_button.set_current_folder(str(self.template_dir))
        elif self.default_templates_dir.exists():
            self.template_dir_button.set_current_folder(str(self.default_templates_dir))
        else:
            self.template_dir_button.set_current_folder(str(Path.home()))
        dir_box.pack_start(self.template_dir_button, True, True, 0)
        box.pack_start(dir_box, False, False, 0)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        load_button = Gtk.Button(label="Load Templates")
        load_button.connect("clicked", self._on_load_templates_clicked)
        button_box.pack_start(load_button, False, False, 0)

        default_button = Gtk.Button(label="Use Default Templates")
        default_button.connect("clicked", self._on_use_default_templates_clicked)
        button_box.pack_start(default_button, False, False, 0)
        box.pack_start(button_box, False, False, 0)

        # Template combo box
        combo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label(label="Template:")
        combo_box.pack_start(label, False, False, 0)

        self.template_combo = Gtk.ComboBoxText()
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

        # Pre-populate with last used CSV file if available
        if self.last_csv_path and self.last_csv_path.exists():
            self.csv_chooser.set_filename(str(self.last_csv_path))

        file_box.pack_start(self.csv_chooser, True, True, 0)
        box.pack_start(file_box, False, False, 0)

        # Load button
        load_button = Gtk.Button(label="Load CSV")
        load_button.connect("clicked", self._on_load_csv_clicked)
        box.pack_start(load_button, False, False, 0)

        return frame

    def _create_date_section(self) -> Gtk.Frame:
        """Create the date selection section."""
        frame = Gtk.Frame(label="Step 3: Select Date")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        self.date_calendar = Gtk.Calendar()
        self._set_calendar_date(self.default_date)
        self.date_calendar.connect("day-selected", self._on_date_changed)
        self.date_calendar.connect("month-changed", self._on_date_changed)
        box.pack_start(self.date_calendar, False, False, 0)

        return frame

    def _create_row_section(self) -> Gtk.Frame:
        """Create the row selection section."""
        frame = Gtk.Frame(label="Step 4: Select Row")
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

    def _create_save_section(self) -> Gtk.Frame:
        """Create the save section with output folder and filename field selection."""
        frame = Gtk.Frame(label="Step 6: Save Image")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        # Output folder selection
        folder_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        folder_label = Gtk.Label(label="Output Folder:")
        folder_box.pack_start(folder_label, False, False, 0)

        self.output_folder_button = Gtk.FileChooserButton(
            title="Select Output Folder",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        if self.output_dir.exists():
            self.output_folder_button.set_filename(str(self.output_dir))
        else:
            self.output_folder_button.set_filename(str(Path.home()))
        folder_box.pack_start(self.output_folder_button, True, True, 0)
        box.pack_start(folder_box, False, False, 0)

        # Filename field selection
        fields_label = Gtk.Label()
        fields_label.set_markup("<b>Select fields for filename:</b>")
        fields_label.set_xalign(0.0)
        box.pack_start(fields_label, False, False, 0)

        # Load saved filename field selections
        saved_fields = load_filename_fields()

        fields_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        for field_key, field_label in self.FILENAME_FIELD_OPTIONS:
            check = Gtk.CheckButton(label=field_label)
            # Date is always included (mandatory), other fields are optional
            if field_key == "date":
                check.set_active(True)
                check.set_sensitive(False)  # Disable date checkbox - always included
            else:
                # Set checkbox state based on saved settings
                check.set_active(field_key in saved_fields)
            check.connect("toggled", self._on_filename_field_toggled)
            self.filename_field_checks[field_key] = check
            fields_box.pack_start(check, False, False, 0)
        box.pack_start(fields_box, False, False, 0)

        # Filename preview
        preview_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        preview_label = Gtk.Label(label="Filename:")
        preview_box.pack_start(preview_label, False, False, 0)

        self.filename_preview_label = Gtk.Label()
        self.filename_preview_label.set_xalign(0.0)
        self.filename_preview_label.set_text("(load CSV to preview)")
        preview_box.pack_start(self.filename_preview_label, True, True, 0)
        box.pack_start(preview_box, False, False, 0)

        # Save button
        save_button = Gtk.Button(label="Save Image")
        save_button.connect("clicked", self._on_save_clicked)
        box.pack_start(save_button, False, False, 0)

        return frame

    def _refresh_template_list(self, templates_dir: Path) -> bool:
        """Load templates from the specified directory."""
        if not templates_dir.exists() or not templates_dir.is_dir():
            self.template_combo.remove_all()
            self.template_paths = {}
            if hasattr(self, "status_label"):
                self.status_label.set_text(f"Template folder not found: {templates_dir}")
            return False

        template_paths = self.template_manager.list_template_paths(templates_dir)
        self.template_combo.remove_all()
        self.template_paths = {}

        if not template_paths:
            if hasattr(self, "status_label"):
                self.status_label.set_text(f"No templates found in {templates_dir}")
            return False

        names: list[str] = []
        for path in template_paths:
            name = path.stem
            if name in self.template_paths:
                suffix = 2
                while f"{name} ({suffix})" in self.template_paths:
                    suffix += 1
                name = f"{name} ({suffix})"
            self.template_combo.append_text(name)
            self.template_paths[name] = path
            names.append(name)

        if "standard" in names:
            self.template_combo.set_active(names.index("standard"))
        else:
            self.template_combo.set_active(0)

        self.template_dir = templates_dir
        return True

    def _on_load_templates_clicked(self, button: Gtk.Button) -> None:
        """Handle loading templates from the selected folder."""
        folder = self.template_dir_button.get_filename()
        if not folder:
            self._show_error("Please select a template folder")
            return

        templates_dir = Path(folder)
        if not self._refresh_template_list(templates_dir):
            self._show_error(f"No templates found in {templates_dir}")
            return

        save_template_dir(templates_dir)
        self.status_label.set_text(f"Loaded {len(self.template_paths)} templates")

    def _on_use_default_templates_clicked(self, button: Gtk.Button) -> None:
        """Reset templates to the built-in default folder."""
        if self.default_templates_dir.exists():
            self.template_dir_button.set_current_folder(str(self.default_templates_dir))
        if not self._refresh_template_list(self.default_templates_dir):
            self._show_error("Default templates folder is missing")
            return

        save_template_dir(self.default_templates_dir)
        self.status_label.set_text("Loaded default templates")

    def _set_calendar_date(self, date_value: datetime.date) -> None:
        """Set the calendar selection to a specific date."""
        # Gtk.Calendar months are 0-based.
        self.date_calendar.select_month(date_value.month - 1, date_value.year)
        self.date_calendar.select_day(date_value.day)

    def _get_selected_date(self) -> datetime.date:
        """Get the currently selected date from the calendar."""
        year, month, day = self.date_calendar.get_date()
        return datetime.date(year, month + 1, day)

    def _on_date_changed(self, _calendar: Gtk.Calendar) -> None:
        """Handle date selection changes."""
        self._update_preview()
        self._update_filename_preview()

    def _on_load_csv_clicked(self, button: Gtk.Button) -> None:
        """Handle load CSV button click."""
        csv_path_str = self.csv_chooser.get_filename()
        if not csv_path_str:
            self._show_error("Please select a CSV file")
            return

        try:
            csv_path = Path(csv_path_str)
            self.csv_data = TextInsertUseCase.load_csv(csv_path)
            self.last_csv_path = csv_path

            # Update row spinner
            row_count = len(self.csv_data)
            self.row_adjustment.set_upper(row_count)
            self.row_adjustment.set_value(1)
            self.row_count_label.set_text(f"of {row_count}")

            # Update preview
            self._update_preview()

            # Update filename preview
            self._update_filename_preview()

            self.status_label.set_text(f"Loaded {row_count} rows from CSV")

        except (FileNotFoundError, ValueError) as e:
            self._show_error(f"Failed to load CSV: {e}")

    def _on_row_changed(self, spinner: Gtk.SpinButton) -> None:
        """Handle row spinner value change."""
        self.current_row_index = int(spinner.get_value()) - 1
        self._update_preview()
        self._update_filename_preview()

    def _update_preview(self) -> None:
        """Update the preview text view."""
        if not self.csv_data or self.current_row_index >= len(self.csv_data):
            self.preview_text.get_buffer().set_text("No data to preview")
            return

        row = self.csv_data[self.current_row_index]
        try:
            row = TextInsertUseCase.build_row_data(row, self._get_selected_date(), strict=True)
        except CsvDateError as exc:
            self.preview_text.get_buffer().set_text(f"Invalid date in CSV: {exc}")
            return
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

            template_path = self.template_paths.get(template_name)
            if template_path is None:
                self._show_error("Selected template not found")
                return

            # Insert text using UseCase
            layers = TextInsertUseCase.insert_text_from_csv(
                self.image,
                template_path,
                self.csv_data[self.current_row_index],
                self._get_selected_date(),
            )

            # Track that changes were made
            if layers:
                self._inserted_layers.extend(layers)

            # Flush displays
            Gimp.displays_flush()

            save_last_used_date(self._get_selected_date())
            self.status_label.set_text(f"Inserted {len(layers)} text layers")

        except Exception as e:
            _debug_log(f"ERROR: Insert failed: {e}")
            self._show_error(f"Failed to insert text: {e}")

    def _on_filename_field_toggled(self, check: Gtk.CheckButton) -> None:
        """Handle filename field checkbox toggle."""
        # Save the selected fields to settings
        selected_fields = self._get_selected_filename_fields()
        save_filename_fields(selected_fields)
        self._update_filename_preview()

    def _get_selected_filename_fields(self) -> list[str]:
        """Get the list of selected filename fields."""
        return [key for key, check in self.filename_field_checks.items() if check.get_active()]

    def _update_filename_preview(self) -> None:
        """Update the filename preview label."""
        if not hasattr(self, "filename_preview_label"):
            return

        if not self.csv_data or self.current_row_index >= len(self.csv_data):
            self.filename_preview_label.set_text("(load CSV to preview)")
            return

        try:
            selected_date = self._get_selected_date()
            row_data = TextInsertUseCase.build_row_data(
                self.csv_data[self.current_row_index],
                selected_date,
                strict=False,
            )
            selected_fields = self._get_selected_filename_fields()
            filename = TextInsertUseCase.generate_filename_from_row(
                row_data,
                selected_date,
                selected_fields,
            )
            self.filename_preview_label.set_text(filename)
        except Exception:
            self.filename_preview_label.set_text("(unable to generate preview)")

    def _on_save_clicked(self, button: Gtk.Button) -> None:
        """Handle save button click."""
        if not self.csv_data:
            self._show_error("Please load a CSV file first")
            return

        if self.current_row_index >= len(self.csv_data):
            self._show_error("Invalid row selected")
            return

        folder_path_str = self.output_folder_button.get_filename()
        if not folder_path_str:
            self._show_error("Please select an output folder")
            return

        try:
            output_folder = Path(folder_path_str)
            selected_fields = self._get_selected_filename_fields()

            # Save image using UseCase
            output_path = TextInsertUseCase.save_image_with_metadata(
                self.image,
                output_folder,
                self.csv_data[self.current_row_index],
                self._get_selected_date(),
                selected_fields,
            )

            save_last_used_date(self._get_selected_date())
            self.status_label.set_text(f"Saved: {output_path}")

        except Exception as e:
            _debug_log(f"ERROR: Save failed: {e}")
            self._show_error(f"Failed to save image: {e}")

    def _on_configure_event(self, widget: Gtk.Widget, event: object) -> bool:
        """Save window size when it changes (with debouncing).

        This method is called frequently during window resizing. To avoid
        excessive file I/O, we use a debouncing mechanism that delays the
        actual save operation until 500ms after the last resize event.

        Args:
            widget: The widget that received the event.
            event: The configure event.

        Returns:
            False to allow the event to propagate.
        """
        # Cancel any pending save operation
        if self._resize_save_timeout_id is not None:
            GLib.source_remove(self._resize_save_timeout_id)

        # Schedule a new save operation after 500ms of inactivity
        self._resize_save_timeout_id = GLib.timeout_add(
            500,  # milliseconds
            self._save_window_size_delayed,
        )
        return False

    def _save_window_size_delayed(self) -> bool:
        """Callback to save window size after debounce delay.

        Returns:
            False to prevent the timeout from repeating.
        """
        width, height = self.get_size()
        save_window_size(width, height)
        self._resize_save_timeout_id = None
        return False  # Return False to stop the timeout from repeating

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

    def finalize_response(self, response: Gtk.ResponseType) -> None:
        """Finalize the dialog response by handling inserted layers.

        Call this method after dialog.run() returns and before destroy().
        If the user clicked Cancel, this removes all layers added during the session.
        If the user clicked OK, changes are committed.

        Args:
            response: The dialog response type (OK, CANCEL, etc.)
        """
        # If cancelled, remove all inserted layers
        if response != Gtk.ResponseType.OK and self._inserted_layers:
            for layer in self._inserted_layers:
                try:
                    if layer.is_valid():
                        self.image.remove_layer(layer)
                except Exception as e:
                    _debug_log(f"WARNING: Failed to remove layer during finalize_response: {e}")
            Gimp.displays_flush()
