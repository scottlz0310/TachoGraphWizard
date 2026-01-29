# pyright: reportPrivateUsage=false
"""Unit tests for wizard_procedure.

Note: Settings functions have been removed from wizard_procedure.py as of Issue #30 follow-up.
The save functionality has been moved to text_inserter_dialog.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock


class TestWizardProcedure:
    """Test wizard procedure module."""

    def test_module_imports(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test that wizard_procedure module can be imported."""
        from tachograph_wizard.procedures import wizard_procedure

        # Verify the main function exists
        assert hasattr(wizard_procedure, "run_wizard_dialog")
        assert callable(wizard_procedure.run_wizard_dialog)
