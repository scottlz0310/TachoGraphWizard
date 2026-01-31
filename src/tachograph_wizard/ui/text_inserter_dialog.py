"""Text inserter dialog for the Tachograph Text Inserter plugin."""

from __future__ import annotations

import datetime
import os
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GLib", "2.0")

from gi.repository import Gimp, GimpUi, GLib, Gtk

from tachograph_wizard.core.template_manager import TemplateManager
from tachograph_wizard.core.text_insert_usecase import CsvDateError, TextInsertUseCase
from tachograph_wizard.ui.settings import Settings


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
        self.settings = Settings()
        self.template_manager = TemplateManager()
        self.default_templates_dir = self.template_manager.get_templates_dir()
        self.template_dir = self.settings.load_template_dir(self.default_templates_dir)
        self.template_paths: dict[str, Path] = {}
        self.csv_data: list[dict[str, str]] = []
        self.current_row_index = 0
        self.default_date = self.settings.load_last_used_date() or datetime.date.today()
        self.last_csv_path = self.settings.load_csv_path()
        self.output_dir = self.settings.load_output_dir() or Path.home()
        self.filename_field_checks: dict[str, Gtk.CheckButton] = {}
        self._resize_save_timeout_id: int | None = None
        self._inserted_layers: list[Gimp.Layer] = []  # Track layers added during session

        # Load and set window size
        width, height = self.settings.load_window_size()
        self.set_default_size(width, height)
        self.set_border_width(12)

        # Connect to configure-event to save size changes
        self.connect("configure-event", self._on_configure_event)

        # Add action buttons
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("_OK", Gtk.ResponseType.OK)

        # Load UI from .ui file
        self._load_ui()

    def _load_ui(self) -> None:
        """Load the dialog UI from .ui file."""
        # Load UI definition
        ui_file = Path(__file__).parent / "text_inserter_dialog.ui"
        builder = Gtk.Builder()
        builder.add_from_file(str(ui_file))

        # Get the main content box
        main_content = builder.get_object("main_content")
        if main_content is None:
            msg = "Failed to load main_content from UI file"
            raise RuntimeError(msg)

        # Add to dialog
        content_area = self.get_content_area()
        content_area.pack_start(main_content, True, True, 0)

        # Get widget references
        self.template_dir_button = builder.get_object("template_dir_button")
        self.template_combo = builder.get_object("template_combo")
        self.csv_chooser = builder.get_object("csv_chooser")
        self.date_calendar = builder.get_object("date_calendar")
        self.row_adjustment = builder.get_object("row_adjustment")
        self.row_spinner = builder.get_object("row_spinner")
        self.row_count_label = builder.get_object("row_count_label")
        self.preview_text = builder.get_object("preview_text")
        self.output_folder_button = builder.get_object("output_folder_button")
        self.filename_preview_label = builder.get_object("filename_preview_label")
        self.status_label = builder.get_object("status_label")

        # Get filename field checkboxes
        self.filename_field_checks["date"] = builder.get_object("field_date")
        self.filename_field_checks["vehicle_no"] = builder.get_object("field_vehicle_no")
        self.filename_field_checks["driver"] = builder.get_object("field_driver")

        # Verify all required widgets were loaded
        required_widgets = {
            "template_dir_button": self.template_dir_button,
            "template_combo": self.template_combo,
            "csv_chooser": self.csv_chooser,
            "date_calendar": self.date_calendar,
            "row_adjustment": self.row_adjustment,
            "row_spinner": self.row_spinner,
            "row_count_label": self.row_count_label,
            "preview_text": self.preview_text,
            "output_folder_button": self.output_folder_button,
            "filename_preview_label": self.filename_preview_label,
            "status_label": self.status_label,
            "field_date": self.filename_field_checks.get("date"),
            "field_vehicle_no": self.filename_field_checks.get("vehicle_no"),
            "field_driver": self.filename_field_checks.get("driver"),
        }
        for widget_name, widget in required_widgets.items():
            if widget is None:
                msg = f"Failed to load widget '{widget_name}' from UI file"
                raise RuntimeError(msg)

        # Connect signals
        builder.connect_signals(self)

        # Initialize UI state
        self._initialize_ui_state()

        self.show_all()

    def _initialize_ui_state(self) -> None:
        """Initialize UI widget states with saved settings."""
        # Set template directory
        if self.template_dir.exists():
            self.template_dir_button.set_current_folder(str(self.template_dir))
        elif self.default_templates_dir.exists():
            self.template_dir_button.set_current_folder(str(self.default_templates_dir))
        else:
            self.template_dir_button.set_current_folder(str(Path.home()))

        # Add CSV file filters
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        self.csv_chooser.add_filter(csv_filter)

        all_filter = Gtk.FileFilter()
        all_filter.set_name("All files")
        all_filter.add_pattern("*")
        self.csv_chooser.add_filter(all_filter)

        # Pre-populate with last used CSV file if available
        if self.last_csv_path and self.last_csv_path.exists():
            self.csv_chooser.set_filename(str(self.last_csv_path))

        # Set calendar date
        self._set_calendar_date(self.default_date)

        # Set output directory
        if self.output_dir.exists():
            self.output_folder_button.set_filename(str(self.output_dir))
        else:
            self.output_folder_button.set_filename(str(Path.home()))

        # Load saved filename field selections
        saved_fields = self.settings.load_filename_fields()
        for field_key, check in self.filename_field_checks.items():
            if field_key != "date":  # Date is always included (already set in .ui)
                check.set_active(field_key in saved_fields)

        # Load templates
        self._refresh_template_list(self.template_dir)

    # Signal handlers (called from .ui file)
    def on_load_templates_clicked(self, button: Gtk.Button) -> None:
        """Handle loading templates from the selected folder."""
        self._on_load_templates_clicked(button)

    def on_use_default_templates_clicked(self, button: Gtk.Button) -> None:
        """Reset templates to the built-in default folder."""
        self._on_use_default_templates_clicked(button)

    def on_load_csv_clicked(self, button: Gtk.Button) -> None:
        """Handle load CSV button click."""
        self._on_load_csv_clicked(button)

    def on_date_changed(self, calendar: Gtk.Calendar) -> None:
        """Handle date selection changes."""
        self._on_date_changed(calendar)

    def on_row_changed(self, spinner: Gtk.SpinButton) -> None:
        """Handle row spinner value change."""
        self._on_row_changed(spinner)

    def on_insert_clicked(self, button: Gtk.Button) -> None:
        """Handle insert button click."""
        self._on_insert_clicked(button)

    def on_filename_field_toggled(self, check: Gtk.CheckButton) -> None:
        """Handle filename field checkbox toggle."""
        self._on_filename_field_toggled(check)

    def on_save_clicked(self, button: Gtk.Button) -> None:
        """Handle save button click."""
        self._on_save_clicked(button)

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

        self.settings.save_template_dir(templates_dir)
        self.status_label.set_text(f"Loaded {len(self.template_paths)} templates")

    def _on_use_default_templates_clicked(self, button: Gtk.Button) -> None:
        """Reset templates to the built-in default folder."""
        if self.default_templates_dir.exists():
            self.template_dir_button.set_current_folder(str(self.default_templates_dir))
        if not self._refresh_template_list(self.default_templates_dir):
            self._show_error("Default templates folder is missing")
            return

        self.settings.save_template_dir(self.default_templates_dir)
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

        # Action execution with error handling
        def load_csv_action() -> None:
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

        self._run_action("load CSV", load_csv_action)

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
        # Guard clauses
        if not self._require_csv_loaded():
            return
        if not self._require_valid_row():
            return
        success, _template_name, template_path = self._require_template_selected()
        if not success:
            return
        assert template_path is not None  # Type narrowing: success=True guarantees non-None

        # Action execution with error handling
        def insert_action() -> None:
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

            self.settings.save_last_used_date(self._get_selected_date())
            self.status_label.set_text(f"Inserted {len(layers)} text layers")

        self._run_action("insert text", insert_action)

    def _on_filename_field_toggled(self, check: Gtk.CheckButton) -> None:
        """Handle filename field checkbox toggle."""
        # Save the selected fields to settings
        selected_fields = self._get_selected_filename_fields()
        self.settings.save_filename_fields(selected_fields)
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
        # Guard clauses
        if not self._require_csv_loaded():
            return
        if not self._require_valid_row():
            return
        success, output_folder = self._require_output_folder()
        if not success:
            return
        assert output_folder is not None  # Type narrowing: success=True guarantees non-None

        # Action execution with error handling
        def save_action() -> None:
            selected_fields = self._get_selected_filename_fields()

            # Save image using UseCase
            output_path = TextInsertUseCase.save_image_with_metadata(
                self.image,
                output_folder,
                self.csv_data[self.current_row_index],
                self._get_selected_date(),
                selected_fields,
            )

            self.settings.save_last_used_date(self._get_selected_date())
            self.status_label.set_text(f"Saved: {output_path}")

        self._run_action("save image", save_action)

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
        self.settings.save_window_size(width, height)
        self._resize_save_timeout_id = None
        return False  # Return False to stop the timeout from repeating

    def _require_csv_loaded(self) -> bool:
        """Guard: Ensure CSV data is loaded.

        Returns:
            True if CSV is loaded, False otherwise (shows error).
        """
        if not self.csv_data:
            self._show_error("Please load a CSV file first")
            return False
        return True

    def _require_valid_row(self) -> bool:
        """Guard: Ensure a valid row is selected.

        Returns:
            True if a valid row is selected, False otherwise (shows error).
        """
        if self.current_row_index >= len(self.csv_data):
            self._show_error("Invalid row selected")
            return False
        return True

    def _require_template_selected(self) -> tuple[bool, str, Path] | tuple[bool, None, None]:
        """Guard: Ensure a template is selected.

        Returns:
            Tuple of (True, template_name, template_path) on success,
            or (False, None, None) on failure (shows error).
        """
        template_name = self.template_combo.get_active_text()
        if not template_name:
            self._show_error("Please select a template")
            return False, None, None

        template_path = self.template_paths.get(template_name)
        if template_path is None:
            self._show_error("Selected template not found")
            return False, None, None

        return True, template_name, template_path

    def _require_output_folder(self) -> tuple[bool, Path] | tuple[bool, None]:
        """Guard: Ensure output folder is selected.

        Returns:
            Tuple of (True, output_folder) on success,
            or (False, None) on failure (shows error).
        """
        folder_path_str = self.output_folder_button.get_filename()
        if not folder_path_str:
            self._show_error("Please select an output folder")
            return False, None

        return True, Path(folder_path_str)

    def _run_action(self, action_name: str, action_func: Callable[[], None]) -> None:
        """Execute an action with consistent error handling.

        Args:
            action_name: Name of the action for error messages.
            action_func: Function to execute (must not take arguments).
        """
        try:
            action_func()
        except Exception as e:
            _debug_log(f"ERROR: {action_name} failed: {e}")
            self._show_error(f"Failed to {action_name}: {e}")

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
