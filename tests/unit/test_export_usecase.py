"""Unit tests for export use cases."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestSanitizeTemplateName:
    """Test sanitize_template_name method."""

    def test_removes_json_extension(self) -> None:
        """Test removing .json extension from template name."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        result = ExportTemplateUseCase.sanitize_template_name("my-template.json")
        assert result == "my-template"

    def test_removes_json_extension_case_insensitive(self) -> None:
        """Test removing .json extension case-insensitively."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        result = ExportTemplateUseCase.sanitize_template_name("my-template.JSON")
        assert result == "my-template"

    def test_strips_whitespace(self) -> None:
        """Test stripping whitespace from template name."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        result = ExportTemplateUseCase.sanitize_template_name("  my-template  ")
        assert result == "my-template"

    def test_handles_name_without_extension(self) -> None:
        """Test handling template name without extension."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        result = ExportTemplateUseCase.sanitize_template_name("my-template")
        assert result == "my-template"

    def test_handles_name_with_json_in_middle(self) -> None:
        """Test handling template name with 'json' in the middle."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        result = ExportTemplateUseCase.sanitize_template_name("my-json-template")
        assert result == "my-json-template"

    def test_handles_empty_string(self) -> None:
        """Test handling empty string."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        result = ExportTemplateUseCase.sanitize_template_name("")
        assert result == ""

    def test_handles_only_json_extension(self) -> None:
        """Test handling name that is only .json extension."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        result = ExportTemplateUseCase.sanitize_template_name(".json")
        assert result == ""


class TestComputeOutputPath:
    """Test compute_output_path method."""

    def test_computes_path_with_sanitization(self) -> None:
        """Test computing output path with sanitization."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        output_dir = Path("/tmp/templates")  # noqa: S108  # nosec B108
        template_name = "  my-template.json  "

        result = ExportTemplateUseCase.compute_output_path(template_name, output_dir)

        assert result == output_dir / "my-template.json"

    def test_computes_path_without_extension(self) -> None:
        """Test computing output path for name without extension."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        output_dir = Path("/tmp/templates")  # noqa: S108  # nosec B108
        template_name = "my-template"

        result = ExportTemplateUseCase.compute_output_path(template_name, output_dir)

        assert result == output_dir / "my-template.json"


class TestExportTemplate:
    """Test export_template method."""

    def test_exports_template_successfully(
        self,
        tmp_path: Path,
    ) -> None:
        """Test successfully exporting a template."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        mock_image = Mock()
        template_name = "test-template"
        output_dir = tmp_path / "templates"
        output_dir.mkdir()
        description = "Test template description"

        # Patch at the point of import inside the export_template method
        with patch("tachograph_wizard.core.template_exporter.TemplateExporter") as mock_exporter_cls:
            mock_exporter = Mock()
            mock_exporter_cls.return_value = mock_exporter
            expected_path = output_dir / "test-template.json"
            mock_exporter.export_template.return_value = expected_path

            result = ExportTemplateUseCase.export_template(
                mock_image,
                template_name,
                output_dir,
                description=description,
            )

            assert result == expected_path
            mock_exporter_cls.assert_called_once_with(mock_image)
            mock_exporter.export_template.assert_called_once_with(
                "test-template",
                expected_path,
                description=description,
            )

    def test_sanitizes_template_name_before_export(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that template name is sanitized before export."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        mock_image = Mock()
        template_name = "  test-template.json  "  # Has extension and whitespace
        output_dir = tmp_path / "templates"
        output_dir.mkdir()

        with patch("tachograph_wizard.core.template_exporter.TemplateExporter") as mock_exporter_cls:
            mock_exporter = Mock()
            mock_exporter_cls.return_value = mock_exporter
            expected_path = output_dir / "test-template.json"
            mock_exporter.export_template.return_value = expected_path

            ExportTemplateUseCase.export_template(
                mock_image,
                template_name,
                output_dir,
            )

            # Verify sanitized name was used
            mock_exporter.export_template.assert_called_once()
            call_args = mock_exporter.export_template.call_args
            assert call_args[0][0] == "test-template"  # First arg should be sanitized name
            assert call_args[0][1] == expected_path

    def test_passes_description_to_exporter(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that description is passed to exporter."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        mock_image = Mock()
        template_name = "test-template"
        output_dir = tmp_path / "templates"
        output_dir.mkdir()
        description = "Custom description"

        with patch("tachograph_wizard.core.template_exporter.TemplateExporter") as mock_exporter_cls:
            mock_exporter = Mock()
            mock_exporter_cls.return_value = mock_exporter
            expected_path = output_dir / "test-template.json"
            mock_exporter.export_template.return_value = expected_path

            ExportTemplateUseCase.export_template(
                mock_image,
                template_name,
                output_dir,
                description=description,
            )

            call_args = mock_exporter.export_template.call_args
            assert call_args[1]["description"] == description

    def test_raises_template_export_error_on_failure(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that TemplateExportError is raised on export failure."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase
        from tachograph_wizard.core.template_exporter import TemplateExportError

        mock_image = Mock()
        template_name = "test-template"
        output_dir = tmp_path / "templates"
        output_dir.mkdir()

        with patch("tachograph_wizard.core.template_exporter.TemplateExporter") as mock_exporter_cls:
            mock_exporter = Mock()
            mock_exporter_cls.return_value = mock_exporter
            mock_exporter.export_template.side_effect = TemplateExportError("Export failed")

            with pytest.raises(TemplateExportError, match="Export failed"):
                ExportTemplateUseCase.export_template(
                    mock_image,
                    template_name,
                    output_dir,
                )

    def test_uses_empty_description_by_default(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that empty description is used by default."""
        from tachograph_wizard.core.export_usecase import ExportTemplateUseCase

        mock_image = Mock()
        template_name = "test-template"
        output_dir = tmp_path / "templates"
        output_dir.mkdir()

        with patch("tachograph_wizard.core.template_exporter.TemplateExporter") as mock_exporter_cls:
            mock_exporter = Mock()
            mock_exporter_cls.return_value = mock_exporter
            expected_path = output_dir / "test-template.json"
            mock_exporter.export_template.return_value = expected_path

            ExportTemplateUseCase.export_template(
                mock_image,
                template_name,
                output_dir,
            )

            call_args = mock_exporter.export_template.call_args
            assert call_args[1]["description"] == ""
