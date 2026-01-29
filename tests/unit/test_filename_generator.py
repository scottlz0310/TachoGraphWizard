"""Tests for filename_generator module."""

from __future__ import annotations

import datetime

from tachograph_wizard.core.filename_generator import generate_filename


class TestFilenameGenerator:
    """Tests for filename generation functionality."""

    def test_generate_filename_full(self) -> None:
        """Test filename generation with all fields."""
        date = datetime.date(2025, 1, 1)
        result = generate_filename(
            date=date,
            vehicle_number="123",
            driver_name="TaroYamada",
        )
        assert result == "20250101_123_TaroYamada.png"

    def test_generate_filename_partial(self) -> None:
        """Test filename generation with partial fields."""
        date = datetime.date(2025, 1, 1)
        result = generate_filename(date=date)
        assert result == "20250101.png"

    def test_generate_filename_with_vehicle_only(self) -> None:
        """Test filename generation with vehicle number only."""
        date = datetime.date(2025, 1, 1)
        result = generate_filename(
            date=date,
            vehicle_number="456",
        )
        assert result == "20250101_456.png"

    def test_generate_filename_sanitizes_spaces(self) -> None:
        """Test that spaces are properly sanitized."""
        date = datetime.date(2025, 1, 1)
        result = generate_filename(
            date=date,
            vehicle_number="AB 123",
            driver_name="Taro Yamada",
        )
        assert result == "20250101_AB_123_TaroYamada.png"

    def test_generate_filename_sanitizes_slashes(self) -> None:
        """Test that slashes are properly sanitized."""
        date = datetime.date(2025, 1, 1)
        result = generate_filename(
            date=date,
            vehicle_number="AB/123",
            driver_name="Taro/Yamada",
        )
        assert result == "20250101_AB-123_Taro-Yamada.png"

    def test_generate_filename_default_date(self) -> None:
        """Test filename generation with default (today) date.

        Uses a fixed date to avoid time-of-day race conditions.
        """
        from unittest.mock import patch

        fixed_date = datetime.date(2025, 6, 15)
        with patch("tachograph_wizard.core.filename_generator.datetime") as mock_datetime:
            mock_datetime.date.today.return_value = fixed_date
            result = generate_filename(vehicle_number="123")
            assert result == "20250615_123.png"

    def test_generate_filename_custom_extension(self) -> None:
        """Test filename generation with custom extension."""
        date = datetime.date(2025, 1, 1)
        result = generate_filename(
            date=date,
            vehicle_number="123",
            extension="jpg",
        )
        assert result == "20250101_123.jpg"

    def test_generate_filename_removes_fullwidth_space(self) -> None:
        """Test that full-width spaces are removed from driver name."""
        date = datetime.date(2025, 1, 1)
        result = generate_filename(
            date=date,
            driver_name="山田　太郎",
        )
        assert result == "20250101_山田太郎.png"

    def test_generate_filename_removes_backslash(self) -> None:
        """Test that backslashes are sanitized."""
        date = datetime.date(2025, 1, 1)
        result = generate_filename(
            date=date,
            driver_name="Taro\\Yamada",
        )
        assert result == "20250101_Taro-Yamada.png"

    def test_generate_filename_empty_strings(self) -> None:
        """Test filename generation with empty strings."""
        date = datetime.date(2025, 1, 1)
        result = generate_filename(
            date=date,
            vehicle_number="",
            driver_name="",
        )
        assert result == "20250101.png"

    def test_generate_filename_none_date(self) -> None:
        """Test that None date defaults to today.

        Uses a fixed date to avoid time-of-day race conditions.
        """
        from unittest.mock import patch

        fixed_date = datetime.date(2025, 6, 15)
        with patch("tachograph_wizard.core.filename_generator.datetime") as mock_datetime:
            mock_datetime.date.today.return_value = fixed_date
            result = generate_filename(date=None, vehicle_number="123")
            assert result == "20250615_123.png"
