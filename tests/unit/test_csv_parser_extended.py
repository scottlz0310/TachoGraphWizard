# pyright: reportPrivateUsage=false
"""Extended unit tests for CSV parser - covers encoding fallback and edge cases."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestCSVParserEncodingFallback:
    """Test CSV parsing with encoding fallback paths."""

    def test_parse_csv_utf8_with_bom(self, tmp_path: Path) -> None:
        """Parse a CSV file encoded with UTF-8 BOM."""
        from tachograph_wizard.core.csv_parser import CSVParser

        csv_path = tmp_path / "bom.csv"
        # Write UTF-8 BOM + content
        csv_path.write_bytes(b"\xef\xbb\xbfcol_a,col_b\n1,2\n")

        rows = CSVParser.parse(csv_path)
        assert rows == [{"col_a": "1", "col_b": "2"}]

    def test_parse_csv_decode_failure_raises(self, tmp_path: Path) -> None:
        """CSV that cannot be decoded by any encoding raises ValueError."""
        from tachograph_wizard.core.csv_parser import CSVParser

        csv_path = tmp_path / "bad.csv"
        # Write raw bytes that are invalid in both utf-8-sig and utf-8
        csv_path.write_bytes(b"\x80\x81\x82\x83\n\x84\x85\n")

        # UTF-8 is quite permissive so this may parse; test the branch
        # by mocking open to always raise UnicodeDecodeError
        import unittest.mock as um

        call_count = 0

        def always_fail(*_args: object, **_kwargs: object) -> object:
            nonlocal call_count
            call_count += 1
            codec = "utf-8"
            raise UnicodeDecodeError(codec, b"", 0, 1, "test")

        with um.patch.object(type(csv_path), "open", always_fail), pytest.raises(ValueError, match="Failed to decode"):
            CSVParser.parse(csv_path)

    def test_get_headers_file_not_found(self, tmp_path: Path) -> None:
        """get_headers raises FileNotFoundError for missing file."""
        from tachograph_wizard.core.csv_parser import CSVParser

        with pytest.raises(FileNotFoundError):
            CSVParser.get_headers(tmp_path / "nonexistent.csv")

    def test_get_headers_decode_failure_raises(self, tmp_path: Path) -> None:
        """get_headers with undecodable file raises ValueError."""
        from tachograph_wizard.core.csv_parser import CSVParser

        csv_path = tmp_path / "bad.csv"
        csv_path.write_bytes(b"a,b\n")

        import unittest.mock as um

        def always_fail(*_args: object, **_kwargs: object) -> object:
            codec = "utf-8"
            raise UnicodeDecodeError(codec, b"", 0, 1, "test")

        with um.patch.object(type(csv_path), "open", always_fail), pytest.raises(ValueError, match="Failed to decode"):
            CSVParser.get_headers(csv_path)

    def test_get_headers_empty_csv(self, tmp_path: Path) -> None:
        """get_headers on an empty file raises ValueError (StopIteration)."""
        from tachograph_wizard.core.csv_parser import CSVParser

        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("", encoding="utf-8")

        with pytest.raises(ValueError, match="Failed to read CSV headers"):
            CSVParser.get_headers(csv_path)
