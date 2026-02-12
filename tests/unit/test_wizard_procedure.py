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


class TestWizardProcedureThresholdBias:
    """Test threshold bias behavior helpers."""

    def test_default_threshold_bias_constant_is_15(self) -> None:
        """The wizard default threshold value should remain 15."""
        from tachograph_wizard.procedures import wizard_procedure

        assert wizard_procedure._DEFAULT_AUTO_THRESHOLD_BIAS == 15

    def test_resolve_auto_threshold_bias_maps_default_to_none(self) -> None:
        """Default UI value should map to None to use splitter-side default."""
        from tachograph_wizard.procedures import wizard_procedure

        result = wizard_procedure._resolve_auto_threshold_bias(15)
        assert result is None

    def test_resolve_auto_threshold_bias_keeps_non_default_value(self) -> None:
        """Non-default UI value should be passed through as explicit threshold."""
        from tachograph_wizard.procedures import wizard_procedure

        result = wizard_procedure._resolve_auto_threshold_bias(21)
        assert result == 21
