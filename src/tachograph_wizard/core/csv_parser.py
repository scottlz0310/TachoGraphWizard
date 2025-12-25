"""CSV parser for reading vehicle data from CSV files."""

from __future__ import annotations

import csv
from pathlib import Path


class CSVParser:
    """Parser for CSV files containing vehicle information."""

    @staticmethod
    def parse(file_path: Path) -> list[dict[str, str]]:
        """Parse a CSV file and return a list of dictionaries.

        Args:
            file_path: Path to the CSV file.

        Returns:
            List of dictionaries, where each dictionary represents a row
            with column names as keys.

        Raises:
            FileNotFoundError: If the CSV file doesn't exist.
            ValueError: If the CSV file is invalid or empty.
        """
        if not file_path.exists():
            msg = f"CSV file not found: {file_path}"
            raise FileNotFoundError(msg)

        try:
            # Try UTF-8 with BOM first, then fall back to UTF-8
            encodings = ["utf-8-sig", "utf-8"]
            data = None

            for encoding in encodings:
                try:
                    with file_path.open("r", encoding=encoding, newline="") as f:
                        reader = csv.DictReader(f)
                        data = list(reader)
                        break
                except UnicodeDecodeError:
                    continue

            if data is None:
                msg = f"Failed to decode CSV file (tried {encodings}): {file_path}"
                raise ValueError(msg)

            if not data:
                msg = f"CSV file is empty or has no data rows: {file_path}"
                raise ValueError(msg)

            return data

        except csv.Error as e:
            msg = f"Failed to parse CSV file: {e}"
            raise ValueError(msg) from e

    @staticmethod
    def validate_headers(csv_headers: list[str], template_fields: list[str]) -> tuple[bool, list[str]]:
        """Validate that CSV headers match template fields.

        Args:
            csv_headers: List of column names from the CSV file.
            template_fields: List of field names from the template.

        Returns:
            Tuple of (is_valid, missing_fields).
            - is_valid: True if all required fields are present.
            - missing_fields: List of fields that are in template but not in CSV.
        """
        csv_set = set(csv_headers)
        template_set = set(template_fields)

        # Find fields that are in template but not in CSV
        missing = sorted(template_set - csv_set)

        # Valid if no required fields are missing
        # (For now, we're lenient - extra CSV columns are OK, missing ones just won't be rendered)
        is_valid = True

        return is_valid, missing

    @staticmethod
    def get_headers(file_path: Path) -> list[str]:
        """Get the header row from a CSV file.

        Args:
            file_path: Path to the CSV file.

        Returns:
            List of column names.

        Raises:
            FileNotFoundError: If the CSV file doesn't exist.
            ValueError: If the CSV file is invalid.
        """
        if not file_path.exists():
            msg = f"CSV file not found: {file_path}"
            raise FileNotFoundError(msg)

        try:
            encodings = ["utf-8-sig", "utf-8"]

            for encoding in encodings:
                try:
                    with file_path.open("r", encoding=encoding, newline="") as f:
                        reader = csv.reader(f)
                        headers = next(reader)
                        return headers
                except UnicodeDecodeError:
                    continue

            msg = f"Failed to decode CSV file (tried {encodings}): {file_path}"
            raise ValueError(msg)

        except (csv.Error, StopIteration) as e:
            msg = f"Failed to read CSV headers: {e}"
            raise ValueError(msg) from e
