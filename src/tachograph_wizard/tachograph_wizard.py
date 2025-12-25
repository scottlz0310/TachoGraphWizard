#!/usr/bin/env python3
"""TachoGraphWizard - GIMP 3 Plugin Entry Point.

Main plugin class that registers procedures and handles GIMP plugin lifecycle.
"""

from __future__ import annotations

import os
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")

from gi.repository import Gimp, GimpUi, GLib


def _log_path() -> Path:
    base = os.environ.get("TEMP") or os.environ.get("TMP") or os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "tachograph_wizard.log"


def _debug_log(message: str) -> None:
    try:
        timestamp = datetime.now(tz=UTC).isoformat(timespec="seconds")
        line = f"[{timestamp}] {message}"
        with _log_path().open("a", encoding="utf-8") as fp:
            fp.write(line + "\n")
    except Exception:
        # Never crash the plugin due to logging.
        pass


_debug_log(f"module imported from: {__file__}")


# Ensure the package is importable when GIMP executes this file from within a
# subdirectory under the plug-ins folder.
_plugin_dir = Path(__file__).resolve().parent
_parent_dir = _plugin_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

if TYPE_CHECKING:
    from collections.abc import Sequence


class TachographWizard(Gimp.PlugIn):
    """Main plugin class for TachoGraphWizard.

    This class implements the GIMP PlugIn interface and registers
    the tachograph chart processing wizard procedure.
    """

    def do_query_procedures(self) -> list[str]:
        """Return list of procedures provided by this plugin.

        Returns:
            List containing the procedure name(s) this plugin provides.
        """
        _debug_log("do_query_procedures")
        return ["tachograph-wizard", "tachograph-text-inserter"]

    def do_create_procedure(self, name: str) -> Gimp.Procedure | None:
        """Create and return a procedure.

        Args:
            name: The procedure name to create.

        Returns:
            The created procedure, or None if the name is not recognized.
        """
        _debug_log(f"do_create_procedure name={name}")
        if name == "tachograph-wizard":
            procedure = Gimp.ImageProcedure.new(
                self,
                name,
                Gimp.PDBProcType.PLUGIN,
                self._run_wizard,
                None,
            )

            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)

            procedure.set_menu_label("Tachograph Chart Wizard...")
            procedure.set_icon_name(GimpUi.ICON_GEGL)
            procedure.add_menu_path("<Image>/Filters/Processing")

            procedure.set_documentation(
                "Process tachograph chart scanned images",
                "Interactive wizard to split, clean, rotate, and annotate "
                "tachograph chart images from A3 scans. Provides step-by-step "
                "workflow for processing multiple circular tachograph charts.",
                name,
            )
            procedure.set_attribution(
                "TachoGraphWizard Team",
                "TachoGraphWizard Team",
                "2025",
            )

            return procedure

        if name == "tachograph-text-inserter":
            procedure = Gimp.ImageProcedure.new(
                self,
                name,
                Gimp.PDBProcType.PLUGIN,
                self._run_text_inserter,
                None,
            )

            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)

            procedure.set_menu_label("Tachograph Text Inserter...")
            procedure.set_icon_name(GimpUi.ICON_GEGL)
            procedure.add_menu_path("<Image>/Filters/Processing")

            procedure.set_documentation(
                "Insert text from CSV files into tachograph charts",
                "Load vehicle data from CSV files and insert formatted text "
                "using customizable templates. Supports position ratio management "
                "and automatic font sizing for different image resolutions.",
                name,
            )
            procedure.set_attribution(
                "TachoGraphWizard Team",
                "TachoGraphWizard Team",
                "2025",
            )

            return procedure

        return None

    def _run_wizard(
        self,
        procedure: Gimp.Procedure,
        run_mode: Gimp.RunMode,
        image: Gimp.Image,
        *args: object,
    ) -> Gimp.ValueArray:
        """Execute the wizard procedure.

        Args:
            procedure: The procedure being run.
            run_mode: The run mode (interactive, non-interactive, etc.).
            image: The image to process.
            n_drawables: Number of drawables.
            drawables: The drawable(s) to process.
            config: Procedure configuration.
            run_data: Additional run data.

        Returns:
            ValueArray containing the procedure's return values.
        """

        # Lightweight logging to make invocation/debugging visible on Windows.
        # GIMP may fail silently unless we emit a message or write to stderr.
        _debug_log(f"_run_wizard invoked (run_mode={run_mode}, args_len={len(args)})")

        # Normalize callback args: different GIMP 3 builds/bindings may pass either
        # (drawables, config, run_data) or (n_drawables, drawables, config, run_data).
        drawables: Sequence[Gimp.Drawable] = []

        if args:
            if isinstance(args[0], int):
                if len(args) >= 2:
                    drawables = args[1]  # type: ignore[assignment]
            else:
                drawables = args[0]  # type: ignore[assignment]

        try:
            _debug_log(
                f"args_types={[type(a).__name__ for a in args]} drawables_len={len(drawables) if hasattr(drawables, '__len__') else 'na'}",
            )
        except Exception:
            pass
        try:
            Gimp.message("Tachograph Wizard: invoked")
        except Exception as exc:
            _debug_log(f"Gimp.message failed: {exc!s}")

        # Initialize GimpUi for interactive mode BEFORE importing any Gtk/GimpUi UI modules.
        if run_mode == Gimp.RunMode.INTERACTIVE:
            try:
                GimpUi.init("tachograph-wizard")
                _debug_log("GimpUi.init ok")
            except Exception as exc:
                _debug_log(f"GimpUi.init failed: {exc!s}")

        # Import here to avoid circular imports (and after UI init).
        from tachograph_wizard.procedures.wizard_procedure import run_wizard_dialog

        # Run the wizard
        try:
            drawable = drawables[0] if drawables else None
            _debug_log(f"running dialog (drawable_present={drawable is not None})")
            success = run_wizard_dialog(image, drawable)

            # Return success or cancel status
            status = Gimp.PDBStatusType.SUCCESS if success else Gimp.PDBStatusType.CANCEL
        except Exception as e:
            tb = traceback.format_exc()
            _debug_log(f"error: {e!s}")
            try:
                sys.stderr.write(f"[tachograph_wizard] traceback:\n{tb}\n")
                sys.stderr.flush()
            except Exception:
                pass

            try:
                Gimp.message(f"Tachograph Wizard error: {e!s}\n\n{tb}")
            except Exception as exc:
                _debug_log(f"Gimp.message(error) failed: {exc!s}")

            # Return error status
            error_message = f"Error running wizard: {e!s}"
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error(error_message),
            )

        return procedure.new_return_values(status, GLib.Error())

    def _run_text_inserter(
        self,
        procedure: Gimp.Procedure,
        run_mode: Gimp.RunMode,
        image: Gimp.Image,
        *args: object,
    ) -> Gimp.ValueArray:
        """Execute the text inserter procedure.

        Args:
            procedure: The procedure being run.
            run_mode: The run mode (interactive, non-interactive, etc.).
            image: The image to process.
            args: Additional arguments.

        Returns:
            ValueArray containing the procedure's return values.
        """
        _debug_log(f"_run_text_inserter invoked (run_mode={run_mode}, args_len={len(args)})")

        # Normalize callback args
        drawables: Sequence[Gimp.Drawable] = []

        if args:
            if isinstance(args[0], int):
                if len(args) >= 2:
                    drawables = args[1]  # type: ignore[assignment]
            else:
                drawables = args[0]  # type: ignore[assignment]

        try:
            _debug_log(
                f"args_types={[type(a).__name__ for a in args]} drawables_len={len(drawables) if hasattr(drawables, '__len__') else 'na'}",
            )
        except Exception:
            pass

        # Initialize GimpUi for interactive mode
        if run_mode == Gimp.RunMode.INTERACTIVE:
            try:
                GimpUi.init("tachograph-text-inserter")
                _debug_log("GimpUi.init ok")
            except Exception as exc:
                _debug_log(f"GimpUi.init failed: {exc!s}")

        # Import here to avoid circular imports
        from tachograph_wizard.procedures.text_inserter_procedure import run_text_inserter_dialog

        # Run the text inserter dialog
        try:
            drawable = drawables[0] if drawables else None
            _debug_log(f"running text inserter dialog (drawable_present={drawable is not None})")
            success = run_text_inserter_dialog(image, drawable)

            # Return success or cancel status
            status = Gimp.PDBStatusType.SUCCESS if success else Gimp.PDBStatusType.CANCEL
        except Exception as e:
            tb = traceback.format_exc()
            _debug_log(f"error: {e!s}")
            try:
                sys.stderr.write(f"[tachograph_wizard] traceback:\n{tb}\n")
                sys.stderr.flush()
            except Exception:
                pass

            try:
                Gimp.message(f"Tachograph Text Inserter error: {e!s}\n\n{tb}")
            except Exception as exc:
                _debug_log(f"Gimp.message(error) failed: {exc!s}")

            # Return error status
            error_message = f"Error running text inserter: {e!s}"
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error(error_message),
            )

        return procedure.new_return_values(status, GLib.Error())


def main() -> None:
    """Main entry point for the plugin."""
    Gimp.main(TachographWizard.__gtype__, sys.argv)


if __name__ == "__main__":
    main()
