"""Unit tests for CSV parsing utilities."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestCSVParser:
    """Test CSVParser behavior."""

    def test_parse_csv_returns_rows(self, tmp_path: Path) -> None:
        """Parse a valid CSV file into row dictionaries."""
        from tachograph_wizard.core.csv_parser import CSVParser

        csv_path = tmp_path / "data.csv"
        csv_path.write_text("col_a,col_b\n1,2\n", encoding="utf-8")

        rows = CSVParser.parse(csv_path)

        assert rows == [{"col_a": "1", "col_b": "2"}]

    def test_parse_csv_raises_on_missing_file(self, tmp_path: Path) -> None:
        """Parsing a missing file raises FileNotFoundError."""
        from tachograph_wizard.core.csv_parser import CSVParser

        missing_path = tmp_path / "missing.csv"

        with pytest.raises(FileNotFoundError):
            CSVParser.parse(missing_path)

    def test_parse_csv_raises_on_empty_rows(self, tmp_path: Path) -> None:
        """CSV with only headers but no rows raises ValueError."""
        from tachograph_wizard.core.csv_parser import CSVParser

        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("col_a,col_b\n", encoding="utf-8")

        with pytest.raises(ValueError, match="empty"):
            CSVParser.parse(csv_path)

    def test_get_headers_returns_header_list(self, tmp_path: Path) -> None:
        """Read headers from a CSV file."""
        from tachograph_wizard.core.csv_parser import CSVParser

        csv_path = tmp_path / "headers.csv"
        csv_path.write_text("alpha,beta,gamma\n1,2,3\n", encoding="utf-8")

        headers = CSVParser.get_headers(csv_path)

        assert headers == ["alpha", "beta", "gamma"]

    def test_validate_headers_reports_missing_fields(self) -> None:
        """Detect missing template fields."""
        from tachograph_wizard.core.csv_parser import CSVParser

        is_valid, missing = CSVParser.validate_headers(["alpha", "beta"], ["alpha", "gamma"])

        assert is_valid is True
        assert missing == ["gamma"]
