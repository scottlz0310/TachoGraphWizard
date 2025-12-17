#!/usr/bin/env python3
"""TachoGraphWizard - GIMP 3 Plugin Entry Point.

Main plugin class that registers procedures and handles GIMP plugin lifecycle.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")

from gi.repository import Gimp, GimpUi, GLib

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
        return ["tachograph-wizard"]

    def do_create_procedure(self, name: str) -> Gimp.Procedure | None:
        """Create and return a procedure.

        Args:
            name: The procedure name to create.

        Returns:
            The created procedure, or None if the name is not recognized.
        """
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
        return None

    def _run_wizard(
        self,
        procedure: Gimp.Procedure,
        run_mode: Gimp.RunMode,
        image: Gimp.Image,
        n_drawables: int,
        drawables: Sequence[Gimp.Drawable],
        config: Gimp.ProcedureConfig,
        run_data: object,
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
        # Import here to avoid circular imports
        from tachograph_wizard.procedures.wizard_procedure import run_wizard_dialog

        # Initialize GimpUi for interactive mode
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("tachograph-wizard")

        # Run the wizard
        try:
            drawable = drawables[0] if n_drawables > 0 else None
            success = run_wizard_dialog(image, drawable)

            # Return success or cancel status
            status = Gimp.PDBStatusType.SUCCESS if success else Gimp.PDBStatusType.CANCEL
        except Exception as e:
            # Return error status
            error_message = f"Error running wizard: {e!s}"
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
