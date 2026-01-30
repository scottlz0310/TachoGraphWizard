"""Unit tests for text insert use cases."""

from __future__ import annotations

import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestCsvDateError:
    """Test CsvDateError exception class."""

    def test_from_components(self) -> None:
        """Test creating error from date components."""
        from tachograph_wizard.core.text_insert_usecase import CsvDateError

        error = CsvDateError.from_components("2024", "13", "40")
        assert "2024-13-40" in str(error)
        assert "Invalid date components" in str(error)

    def test_from_string(self) -> None:
        """Test creating error from date string."""
        from tachograph_wizard.core.text_insert_usecase import CsvDateError

        error = CsvDateError.from_string("invalid-date")
        assert "invalid-date" in str(error)
        assert "Invalid date format" in str(error)


class TestResolveDateFromRow:
    """Test resolve_date_from_row method."""

    def test_resolves_date_from_components(self) -> None:
        """Test resolving date from year/month/day components."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"date_year": "2024", "date_month": "3", "date_day": "15"}
        date, source = TextInsertUseCase.resolve_date_from_row(row, strict=False)
        assert date == datetime.date(2024, 3, 15)
        assert source == "csv_parts"

    def test_resolves_date_from_iso_string(self) -> None:
        """Test resolving date from ISO date string."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"date": "2024-03-15"}
        date, source = TextInsertUseCase.resolve_date_from_row(row, strict=False)
        assert date == datetime.date(2024, 3, 15)
        assert source == "csv_date"

    def test_returns_none_when_no_date(self) -> None:
        """Test returning None when no date fields present."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"vehicle_no": "123"}
        date, source = TextInsertUseCase.resolve_date_from_row(row, strict=False)
        assert date is None
        assert source == "none"

    def test_raises_error_on_invalid_components_in_strict_mode(self) -> None:
        """Test raising error on invalid date components in strict mode."""
        from tachograph_wizard.core.text_insert_usecase import CsvDateError, TextInsertUseCase

        row = {"date_year": "2024", "date_month": "13", "date_day": "40"}
        with pytest.raises(CsvDateError):
            TextInsertUseCase.resolve_date_from_row(row, strict=True)

    def test_returns_none_on_invalid_components_in_non_strict_mode(self) -> None:
        """Test returning None on invalid date components in non-strict mode."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"date_year": "2024", "date_month": "13", "date_day": "40"}
        date, source = TextInsertUseCase.resolve_date_from_row(row, strict=False)
        assert date is None
        assert source == "invalid"

    def test_raises_error_on_invalid_date_string_in_strict_mode(self) -> None:
        """Test raising error on invalid date string in strict mode."""
        from tachograph_wizard.core.text_insert_usecase import CsvDateError, TextInsertUseCase

        row = {"date": "not-a-date"}
        with pytest.raises(CsvDateError):
            TextInsertUseCase.resolve_date_from_row(row, strict=True)

    def test_returns_none_on_invalid_date_string_in_non_strict_mode(self) -> None:
        """Test returning None on invalid date string in non-strict mode."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"date": "not-a-date"}
        date, source = TextInsertUseCase.resolve_date_from_row(row, strict=False)
        assert date is None
        assert source == "invalid"

    def test_prefers_components_over_date_string(self) -> None:
        """Test that date components take precedence over date string."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"date_year": "2024", "date_month": "3", "date_day": "15", "date": "2024-06-20"}
        date, source = TextInsertUseCase.resolve_date_from_row(row, strict=False)
        assert date == datetime.date(2024, 3, 15)
        assert source == "csv_parts"

    def test_partial_components_are_ignored(self) -> None:
        """Test that partial date components are ignored."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"date_year": "2024", "date_month": "3"}  # Missing day
        date, source = TextInsertUseCase.resolve_date_from_row(row, strict=False)
        assert date is None
        assert source == "none"


class TestBuildRowData:
    """Test build_row_data method."""

    def test_enriches_row_with_ui_date_when_no_csv_date(self) -> None:
        """Test enriching row with UI date when CSV has no date."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"vehicle_no": "123", "driver": "John"}
        selected_date = datetime.date(2024, 3, 15)
        result = TextInsertUseCase.build_row_data(row, selected_date, strict=False)

        assert result["date_year"] == "2024"
        assert result["date_month"] == "3"
        assert result["date_day"] == "15"
        assert result["date"] == "2024-03-15"
        assert result["vehicle_no"] == "123"
        assert result["driver"] == "John"

    def test_preserves_csv_date_components(self) -> None:
        """Test preserving CSV date components."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"date_year": "2024", "date_month": "6", "date_day": "20", "vehicle_no": "456"}
        selected_date = datetime.date(2024, 3, 15)
        result = TextInsertUseCase.build_row_data(row, selected_date, strict=False)

        # CSV components should be preserved
        assert result["date_year"] == "2024"
        assert result["date_month"] == "6"
        assert result["date_day"] == "20"
        assert result["vehicle_no"] == "456"

    def test_adds_iso_date_from_csv_components(self) -> None:
        """Test adding ISO date field from CSV components."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"date_year": "2024", "date_month": "6", "date_day": "20"}
        selected_date = datetime.date(2024, 3, 15)
        result = TextInsertUseCase.build_row_data(row, selected_date, strict=False)

        assert result["date"] == "2024-06-20"

    def test_preserves_existing_date_field_when_components_present(self) -> None:
        """Test preserving existing date field when components present."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"date_year": "2024", "date_month": "6", "date_day": "20", "date": "existing"}
        selected_date = datetime.date(2024, 3, 15)
        result = TextInsertUseCase.build_row_data(row, selected_date, strict=False)

        assert result["date"] == "existing"

    def test_raises_error_on_invalid_date_in_strict_mode(self) -> None:
        """Test raising error on invalid date in strict mode."""
        from tachograph_wizard.core.text_insert_usecase import CsvDateError, TextInsertUseCase

        row = {"date": "not-a-date"}
        selected_date = datetime.date(2024, 3, 15)
        with pytest.raises(CsvDateError):
            TextInsertUseCase.build_row_data(row, selected_date, strict=True)


class TestGenerateFilenameFromRow:
    """Test generate_filename_from_row method."""

    def test_generates_filename_with_all_fields(self) -> None:
        """Test generating filename with all fields selected."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"vehicle_no": "AB-1234", "driver": "John Doe"}
        selected_date = datetime.date(2024, 3, 15)
        selected_fields = ["date", "vehicle_no", "driver"]

        filename = TextInsertUseCase.generate_filename_from_row(row, selected_date, selected_fields)
        assert filename == "20240315_AB-1234_JohnDoe.png"

    def test_generates_filename_with_date_only(self) -> None:
        """Test generating filename with date only."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"vehicle_no": "AB-1234", "driver": "John Doe"}
        selected_date = datetime.date(2024, 3, 15)
        selected_fields = ["date"]

        filename = TextInsertUseCase.generate_filename_from_row(row, selected_date, selected_fields)
        assert filename == "20240315.png"

    def test_generates_filename_with_date_and_vehicle(self) -> None:
        """Test generating filename with date and vehicle number."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {"vehicle_no": "AB-1234", "driver": "John Doe"}
        selected_date = datetime.date(2024, 3, 15)
        selected_fields = ["date", "vehicle_no"]

        filename = TextInsertUseCase.generate_filename_from_row(row, selected_date, selected_fields)
        assert filename == "20240315_AB-1234.png"

    def test_handles_missing_fields_gracefully(self) -> None:
        """Test handling missing fields gracefully."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        row = {}  # Empty row
        selected_date = datetime.date(2024, 3, 15)
        selected_fields = ["date", "vehicle_no", "driver"]

        filename = TextInsertUseCase.generate_filename_from_row(row, selected_date, selected_fields)
        assert filename == "20240315.png"


class TestLoadCsv:
    """Test load_csv method."""

    def test_loads_and_parses_csv(
        self,
        tmp_path: Path,
    ) -> None:
        """Test loading and parsing CSV file."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("vehicle_no,driver\nAB-1234,John\nCD-5678,Jane\n", encoding="utf-8")

        with patch("tachograph_wizard.core.text_insert_usecase.save_csv_path"):
            data = TextInsertUseCase.load_csv(csv_file)

        assert len(data) == 2
        assert data[0]["vehicle_no"] == "AB-1234"
        assert data[0]["driver"] == "John"
        assert data[1]["vehicle_no"] == "CD-5678"
        assert data[1]["driver"] == "Jane"

    def test_saves_csv_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that CSV path is saved after loading."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("vehicle_no,driver\nAB-1234,John\n", encoding="utf-8")

        with patch("tachograph_wizard.core.text_insert_usecase.save_csv_path") as mock_save:
            TextInsertUseCase.load_csv(csv_file)
            mock_save.assert_called_once_with(csv_file)

    def test_raises_error_on_missing_file(
        self,
        tmp_path: Path,
    ) -> None:
        """Test raising error when CSV file is missing."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        csv_file = tmp_path / "nonexistent.csv"
        with pytest.raises(FileNotFoundError):
            TextInsertUseCase.load_csv(csv_file)


class TestInsertTextFromCsv:
    """Test insert_text_from_csv method."""

    def test_inserts_text_layers(
        self,
        tmp_path: Path,
    ) -> None:
        """Test inserting text layers from CSV data."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        mock_image = Mock()
        template_path = tmp_path / "template.json"

        # Create a minimal template
        template_path.write_text(
            '{"name": "test", "version": "1.0", "reference_width": 1000, "reference_height": 1000, "fields": {}}',
            encoding="utf-8",
        )

        row_data = {"vehicle_no": "AB-1234", "driver": "John"}
        selected_date = datetime.date(2024, 3, 15)

        with (
            patch("tachograph_wizard.core.text_insert_usecase.TemplateManager") as mock_tm,
            patch("tachograph_wizard.core.text_insert_usecase.TextRenderer") as mock_tr,
        ):
            mock_template = Mock()
            mock_tm.return_value.load_template.return_value = mock_template

            mock_renderer = Mock()
            mock_layer1, mock_layer2 = Mock(), Mock()
            mock_renderer.render_from_csv_row.return_value = [mock_layer1, mock_layer2]
            mock_tr.return_value = mock_renderer

            layers = TextInsertUseCase.insert_text_from_csv(
                mock_image,
                template_path,
                row_data,
                selected_date,
            )

            assert len(layers) == 2
            mock_tm.return_value.load_template.assert_called_once_with(template_path)
            mock_tr.assert_called_once_with(mock_image, mock_template)
            mock_renderer.render_from_csv_row.assert_called_once()

            # Verify the enriched row data includes date fields
            call_args = mock_renderer.render_from_csv_row.call_args[0][0]
            assert "date_year" in call_args
            assert "date_month" in call_args
            assert "date_day" in call_args


class TestSaveImageWithMetadata:
    """Test save_image_with_metadata method."""

    def test_saves_image_with_generated_filename(
        self,
        tmp_path: Path,
    ) -> None:
        """Test saving image with generated filename."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        mock_image = Mock()
        mock_duplicate = Mock()
        mock_image.duplicate.return_value = mock_duplicate

        output_folder = tmp_path / "output"
        row_data = {"vehicle_no": "AB-1234", "driver": "John"}
        selected_date = datetime.date(2024, 3, 15)
        selected_fields = ["date", "vehicle_no"]

        with (
            patch("tachograph_wizard.core.text_insert_usecase.save_output_dir") as mock_save_dir,
            patch("tachograph_wizard.core.text_insert_usecase.Exporter") as mock_exporter,
        ):
            output_path = TextInsertUseCase.save_image_with_metadata(
                mock_image,
                output_folder,
                row_data,
                selected_date,
                selected_fields,
            )

            assert output_folder.exists()
            assert output_path == output_folder / "20240315_AB-1234.png"
            mock_save_dir.assert_called_once_with(output_folder)
            mock_image.duplicate.assert_called_once()
            mock_exporter.save_png.assert_called_once_with(
                mock_duplicate,
                output_path,
                flatten=False,
            )

    def test_creates_output_folder_if_missing(
        self,
        tmp_path: Path,
    ) -> None:
        """Test creating output folder if it doesn't exist."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        mock_image = Mock()
        mock_duplicate = Mock()
        mock_image.duplicate.return_value = mock_duplicate

        output_folder = tmp_path / "new_folder"
        assert not output_folder.exists()

        row_data = {"vehicle_no": "AB-1234"}
        selected_date = datetime.date(2024, 3, 15)
        selected_fields = ["date"]

        with (
            patch("tachograph_wizard.core.text_insert_usecase.save_output_dir"),
            patch("tachograph_wizard.core.text_insert_usecase.Exporter"),
        ):
            TextInsertUseCase.save_image_with_metadata(
                mock_image,
                output_folder,
                row_data,
                selected_date,
                selected_fields,
            )

            assert output_folder.exists()

    def test_cleans_up_duplicate_image(
        self,
        tmp_path: Path,
    ) -> None:
        """Test cleaning up duplicate image after save."""
        from tachograph_wizard.core.text_insert_usecase import TextInsertUseCase

        mock_image = Mock()
        mock_duplicate = Mock()
        mock_image.duplicate.return_value = mock_duplicate

        output_folder = tmp_path / "output"
        row_data = {}
        selected_date = datetime.date(2024, 3, 15)
        selected_fields = ["date"]

        with (
            patch("tachograph_wizard.core.text_insert_usecase.save_output_dir"),
            patch("tachograph_wizard.core.text_insert_usecase.Exporter"),
        ):
            TextInsertUseCase.save_image_with_metadata(
                mock_image,
                output_folder,
                row_data,
                selected_date,
                selected_fields,
            )

            mock_duplicate.delete.assert_called_once()
