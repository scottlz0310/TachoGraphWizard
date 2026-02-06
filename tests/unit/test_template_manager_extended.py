# pyright: reportPrivateUsage=false
"""Extended unit tests for TemplateManager - covers cache, errors, and listing."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestTemplateManagerCacheAndErrors:
    """Test TemplateManager cache hit and error handling."""

    def test_load_template_file_not_found(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """load_template raises FileNotFoundError for missing file."""
        from tachograph_wizard.core.template_manager import TemplateManager

        mgr = TemplateManager()
        with pytest.raises(FileNotFoundError):
            mgr.load_template(tmp_path / "nonexistent.json")

    def test_load_template_invalid_json(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """load_template raises ValueError for invalid JSON."""
        from tachograph_wizard.core.template_manager import TemplateManager

        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid", encoding="utf-8")

        mgr = TemplateManager()
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            mgr.load_template(bad_file)

    def test_load_template_non_dict_json(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """load_template raises TypeError for non-dict JSON (e.g. list)."""
        from tachograph_wizard.core.template_manager import TemplateManager

        list_file = tmp_path / "list.json"
        list_file.write_text("[1, 2, 3]", encoding="utf-8")

        mgr = TemplateManager()
        with pytest.raises(TypeError, match="Invalid template format"):
            mgr.load_template(list_file)

    def test_load_template_cache_hit(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Second load returns cached template without reading file again."""
        from tachograph_wizard.core.template_manager import TemplateManager

        template_data = {
            "name": "test",
            "version": "1.0",
            "description": "desc",
            "reference_width": 1000,
            "reference_height": 1000,
            "fields": {},
        }
        template_file = tmp_path / "test.json"
        template_file.write_text(json.dumps(template_data), encoding="utf-8")

        mgr = TemplateManager()
        first = mgr.load_template(template_file)
        second = mgr.load_template(template_file)

        assert first is second  # Same object from cache

    def test_clear_cache(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """clear_cache empties the template cache."""
        from tachograph_wizard.core.template_manager import TemplateManager

        template_data = {
            "name": "test",
            "version": "1.0",
            "description": "desc",
            "reference_width": 1000,
            "reference_height": 1000,
            "fields": {},
        }
        template_file = tmp_path / "test.json"
        template_file.write_text(json.dumps(template_data), encoding="utf-8")

        mgr = TemplateManager()
        mgr.load_template(template_file)
        assert len(mgr._cache) > 0

        mgr.clear_cache()
        assert len(mgr._cache) == 0

    def test_list_template_paths_nonexistent_dir(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """list_template_paths returns empty list for non-existing directory."""
        from tachograph_wizard.core.template_manager import TemplateManager

        mgr = TemplateManager()
        result = mgr.list_template_paths(tmp_path / "nonexistent")
        assert result == []

    def test_list_template_paths_with_custom_dir(
        self,
        tmp_path: Path,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """list_template_paths returns .json files from the specified directory."""
        from tachograph_wizard.core.template_manager import TemplateManager

        # Create some template files
        (tmp_path / "a.json").write_text("{}", encoding="utf-8")
        (tmp_path / "b.json").write_text("{}", encoding="utf-8")
        (tmp_path / "c.txt").write_text("not json", encoding="utf-8")

        mgr = TemplateManager()
        result = mgr.list_template_paths(tmp_path)
        names = [p.name for p in result]

        assert "a.json" in names
        assert "b.json" in names
        assert "c.txt" not in names

    def test_get_template_path(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """get_template_path returns correct path."""
        from tachograph_wizard.core.template_manager import TemplateManager

        mgr = TemplateManager()
        result = mgr.get_template_path("standard")
        assert result.name == "standard.json"

    def test_get_templates_dir(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """get_templates_dir returns the default templates directory."""
        from tachograph_wizard.core.template_manager import TemplateManager

        mgr = TemplateManager()
        result = mgr.get_templates_dir()
        assert result.name == "default_templates"

    def test_list_templates(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """list_templates returns template names from default directory."""
        from tachograph_wizard.core.template_manager import TemplateManager

        mgr = TemplateManager()
        result = mgr.list_templates()
        # Should be a list of strings (stem names)
        assert isinstance(result, list)
        for name in result:
            assert isinstance(name, str)
