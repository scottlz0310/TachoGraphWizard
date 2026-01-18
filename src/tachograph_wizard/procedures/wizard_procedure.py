"""Wizard procedure implementation.

Main procedure that coordinates the tachograph chart processing workflow.
Phase 1 (MVP) provides a simple dialog interface. Phase 2 will convert
this to a full GtkAssistant-based wizard.
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gimp, GimpUi, Gtk


def _get_settings_path() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home())
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "tachograph_wizard" / "settings.json"


def _load_last_output_dir(default_dir: Path) -> Path:
    settings_path = _get_settings_path()
    try:
        with settings_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        value = data.get("wizard_last_output_dir")
        if value:
            candidate = Path(value)
            if candidate.exists():
                return candidate
    except FileNotFoundError:
        return default_dir
    except (json.JSONDecodeError, TypeError, ValueError):
        return default_dir
    return default_dir


def _save_last_output_dir(selected_dir: Path) -> None:
    settings_path = _get_settings_path()
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, str] = {}
        if settings_path.exists():
            try:
                with settings_path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (json.JSONDecodeError, TypeError, ValueError):
                data = {}
        data["wizard_last_output_dir"] = str(selected_dir)
        with settings_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=True, indent=2)
    except Exception:
        return


def run_wizard_dialog(
    image: Gimp.Image,
    drawable: Gimp.Drawable | None,
) -> bool:
    """Run the tachograph chart processing wizard.

    Phase 1 (MVP) implementation with simple dialog.
    Phase 2 will upgrade to GtkAssistant-based multi-step wizard.

    Args:
        image: The image to process.
        drawable: The active drawable (may be None).

    Returns:
        True if processing completed successfully, False if cancelled.
    """
    dialog = TachographSimpleDialog(image, drawable)
    response = dialog.run()
    dialog.destroy()

    return response == Gtk.ResponseType.OK


class TachographSimpleDialog(GimpUi.Dialog):
    """Simple dialog for tachograph chart processing.

    Phase 1 (MVP) implementation. Provides basic controls for:
    - Splitting images using guides
    - Removing background
    - Saving as PNG

    Phase 2 will replace this with a proper wizard interface.
    """

    def __init__(
        self,
        image: Gimp.Image,
        drawable: Gimp.Drawable | None,
    ):
        """Initialize the dialog.

        Args:
            image: The image to process.
            drawable: The active drawable.
        """
        super().__init__(
            title="Tachograph Chart Wizard (MVP)",
            role="tachograph-wizard",
        )

        self.image = image
        self.drawable = drawable
        self.split_images: list[Gimp.Image] = []

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
            "<b>Tachograph Chart Processing Wizard</b>\n\nThis wizard will help you process scanned tachograph charts.",
        )
        welcome_label.set_line_wrap(True)
        content_area.pack_start(welcome_label, False, False, 0)

        # Step 1: Split images
        split_frame = self._create_split_section()
        content_area.pack_start(split_frame, False, False, 0)

        # Step 2: Background removal
        background_frame = self._create_background_section()
        content_area.pack_start(background_frame, False, False, 0)

        # Step 3: Save settings
        save_frame = self._create_save_section()
        content_area.pack_start(save_frame, False, False, 0)

        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_text("Ready to process")
        self.status_label.set_xalign(0.0)
        content_area.pack_start(self.status_label, False, False, 0)

        self.show_all()

    def _create_split_section(self) -> Gtk.Frame:
        """Create the image splitting section."""
        frame = Gtk.Frame(label="Step 1: Split Images")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        label = Gtk.Label(
            label="Automatically split the scanned image into individual tachograph discs.",
        )
        label.set_line_wrap(True)
        label.set_xalign(0.0)
        box.pack_start(label, False, False, 0)

        # Padding setting
        padding_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        padding_label = Gtk.Label(label="Split Padding (px):")
        padding_label.set_xalign(0.0)
        padding_box.pack_start(padding_label, False, False, 0)

        self.split_padding_adjustment = Gtk.Adjustment(
            value=20,
            lower=0,
            upper=100,
            step_increment=1,
            page_increment=5,
        )
        split_padding_spin = Gtk.SpinButton(
            adjustment=self.split_padding_adjustment,
            digits=0,
        )
        padding_box.pack_start(split_padding_spin, False, False, 0)

        info_label = Gtk.Label(label="  (Margin around each disc)")
        info_label.set_xalign(0.0)
        padding_box.pack_start(info_label, False, False, 0)
        box.pack_start(padding_box, False, False, 0)

        # Threshold bias
        auto_threshold_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        auto_threshold_label = Gtk.Label(label="Threshold Bias (0=Auto):")
        auto_threshold_label.set_xalign(0.0)
        auto_threshold_box.pack_start(auto_threshold_label, False, False, 0)

        self.auto_threshold_adjustment = Gtk.Adjustment(
            value=0,
            lower=0,
            upper=255,
            step_increment=1,
            page_increment=10,
        )
        auto_threshold_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=self.auto_threshold_adjustment,
        )
        auto_threshold_scale.set_digits(0)
        auto_threshold_box.pack_start(auto_threshold_scale, True, True, 0)
        box.pack_start(auto_threshold_box, False, False, 0)

        # Edge trim settings
        edge_frame = Gtk.Frame(label="Edge Trim (px)")
        edge_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        edge_box.set_border_width(6)
        edge_frame.add(edge_box)

        edge_grid = Gtk.Grid()
        edge_grid.set_column_spacing(6)
        edge_grid.set_row_spacing(6)
        edge_box.pack_start(edge_grid, False, False, 0)

        self.auto_edge_trim_left = Gtk.Adjustment(value=0, lower=0, upper=200, step_increment=1, page_increment=10)
        self.auto_edge_trim_right = Gtk.Adjustment(value=0, lower=0, upper=200, step_increment=1, page_increment=10)
        self.auto_edge_trim_top = Gtk.Adjustment(value=0, lower=0, upper=200, step_increment=1, page_increment=10)
        self.auto_edge_trim_bottom = Gtk.Adjustment(value=0, lower=0, upper=200, step_increment=1, page_increment=10)

        edge_grid.attach(Gtk.Label(label="Left:"), 0, 0, 1, 1)
        edge_grid.attach(Gtk.SpinButton(adjustment=self.auto_edge_trim_left, digits=0), 1, 0, 1, 1)
        edge_grid.attach(Gtk.Label(label="Right:"), 2, 0, 1, 1)
        edge_grid.attach(Gtk.SpinButton(adjustment=self.auto_edge_trim_right, digits=0), 3, 0, 1, 1)
        edge_grid.attach(Gtk.Label(label="Top:"), 0, 1, 1, 1)
        edge_grid.attach(Gtk.SpinButton(adjustment=self.auto_edge_trim_top, digits=0), 1, 1, 1, 1)
        edge_grid.attach(Gtk.Label(label="Bottom:"), 2, 1, 1, 1)
        edge_grid.attach(Gtk.SpinButton(adjustment=self.auto_edge_trim_bottom, digits=0), 3, 1, 1, 1)

        box.pack_start(edge_frame, False, False, 0)

        # Split button
        split_button = Gtk.Button(label="Split Images")
        split_button.connect("clicked", self._on_auto_split_clicked)
        box.pack_start(split_button, False, False, 0)

        return frame

    def _create_background_section(self) -> Gtk.Frame:
        """Create the background removal section."""
        frame = Gtk.Frame(label="Step 2: Remove Background")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        label = Gtk.Label(
            label="Remove background outside the circular disc area.",
        )
        label.set_xalign(0.0)
        box.pack_start(label, False, False, 0)

        # Ellipse padding adjustment
        ellipse_padding_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ellipse_padding_label = Gtk.Label(label="Ellipse Padding (px):")
        ellipse_padding_label.set_xalign(0.0)
        ellipse_padding_box.pack_start(ellipse_padding_label, False, False, 0)

        self.ellipse_padding_adjustment = Gtk.Adjustment(
            value=20,
            lower=0,
            upper=100,
            step_increment=1,
            page_increment=5,
        )
        ellipse_padding_spin = Gtk.SpinButton(
            adjustment=self.ellipse_padding_adjustment,
            digits=0,
        )
        ellipse_padding_box.pack_start(ellipse_padding_spin, False, False, 0)

        ellipse_info_label = Gtk.Label(label="  (Inset from edge)")
        ellipse_info_label.set_xalign(0.0)
        ellipse_padding_box.pack_start(ellipse_info_label, False, False, 0)
        box.pack_start(ellipse_padding_box, False, False, 0)

        remove_bg_button = Gtk.Button(label="Remove Background")
        remove_bg_button.connect("clicked", self._on_remove_background_clicked)
        box.pack_start(remove_bg_button, False, False, 0)

        return frame

    def _create_save_section(self) -> Gtk.Frame:
        """Create the save settings section."""
        frame = Gtk.Frame(label="Step 3: Save As PNG")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(6)
        frame.add(box)

        # Output directory
        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dir_label = Gtk.Label(label="Output Directory:")
        dir_box.pack_start(dir_label, False, False, 0)

        self.output_dir_button = Gtk.FileChooserButton(
            title="Select Output Directory",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        # Set default to last used output directory
        default_dir = _load_last_output_dir(Path.home())
        self.output_dir_button.set_current_folder(str(default_dir))
        dir_box.pack_start(self.output_dir_button, True, True, 0)

        box.pack_start(dir_box, False, False, 0)

        save_button = Gtk.Button(label="Save All As PNG")
        save_button.connect("clicked", self._on_save_clicked)
        box.pack_start(save_button, False, False, 0)

        return frame

    def _on_auto_split_clicked(self, button: Gtk.Button) -> None:
        """Handle auto split button click."""
        try:
            from tachograph_wizard.core.image_splitter import ImageSplitter

            split_padding = int(self.split_padding_adjustment.get_value())
            threshold_value = int(self.auto_threshold_adjustment.get_value())
            threshold_bias = threshold_value if threshold_value > 0 else None
            edge_trim_left = int(self.auto_edge_trim_left.get_value())
            edge_trim_right = int(self.auto_edge_trim_right.get_value())
            edge_trim_top = int(self.auto_edge_trim_top.get_value())
            edge_trim_bottom = int(self.auto_edge_trim_bottom.get_value())

            self.split_images = ImageSplitter.split_by_auto_detect(
                self.image,
                pad_px=split_padding,
                threshold_bias=threshold_bias,
                edge_trim_left=edge_trim_left,
                edge_trim_right=edge_trim_right,
                edge_trim_top=edge_trim_top,
                edge_trim_bottom=edge_trim_bottom,
            )

            for img in self.split_images:
                Gimp.Display.new(img)

            Gimp.displays_flush()

            count = len(self.split_images)
            self.status_label.set_text(f"Auto-split into {count} images")

        except ValueError as e:
            self._show_error(f"Auto split failed: {e}")
        except Exception as e:
            self._show_error(f"Unexpected error during auto split: {e}")

    def _on_remove_background_clicked(self, button: Gtk.Button) -> None:
        """Handle remove background button click."""
        if not self.split_images:
            self._show_error("Please split the image first")
            return

        try:
            from tachograph_wizard.core.background_remover import BackgroundRemover

            ellipse_padding = int(self.ellipse_padding_adjustment.get_value())

            for img in self.split_images:
                # Create undo group for this image
                # This allows Ctrl+Z to undo the background removal
                img.undo_group_start()

                try:
                    # Get layers - GIMP 3 uses get_layers() instead of get_active_layer()
                    layers = img.get_layers()
                    if layers:
                        layer = layers[0]
                        BackgroundRemover.process_background(
                            layer,
                            ellipse_padding=ellipse_padding,
                        )
                finally:
                    # Always end undo group, even if there was an error
                    img.undo_group_end()

            Gimp.displays_flush()

            self.status_label.set_text(
                f"Removed background from {len(self.split_images)} images",
            )

        except Exception as e:
            self._show_error(f"Background removal failed: {e}")

    def _on_save_clicked(self, button: Gtk.Button) -> None:
        """Handle save button click."""
        if not self.split_images:
            self._show_error("No images to save. Please split the image first.")
            return

        try:
            from tachograph_wizard.core.exporter import Exporter

            output_dir_path = self.output_dir_button.get_filename()
            if not output_dir_path:
                self._show_error("Please select an output directory")
                return

            output_dir = Path(output_dir_path)
            _save_last_output_dir(output_dir)

            for i, img in enumerate(self.split_images, start=1):
                # Generate filename
                filename = Exporter.generate_filename(
                    date=datetime.date.today(),
                    vehicle_number=str(i),
                )
                output_path = output_dir / filename

                # Save
                Exporter.save_png(img, output_path)

            self.status_label.set_text(
                f"Saved {len(self.split_images)} images to {output_dir}",
            )

        except Exception as e:
            self._show_error(f"Save failed: {e}")

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
