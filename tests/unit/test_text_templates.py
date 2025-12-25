"""Unit tests for template management and text rendering helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock

import pytest


class TestTemplateManager:
    """Test TemplateManager behavior."""

    def test_load_template_parses_fields(self, tmp_path: Path) -> None:
        """Load a JSON template into a Template object."""
        from tachograph_wizard.core.template_manager import TemplateManager

        template_path = tmp_path / "template.json"
        template_path.write_text(
            (
                "{"
                '"name":"Example",'
                '"version":"1.0",'
                '"description":"",'
                '"reference_width":1000,'
                '"reference_height":1000,'
                '"fields":{'
                '"driver":{'
                '"position":{"x_ratio":0.1,"y_ratio":0.2},'
                '"font":{"family":"Arial","size_ratio":0.05,"color":"#010203"}'
                "}"
                "}"
                "}"
            ),
            encoding="utf-8",
        )

        manager = TemplateManager()
        template = manager.load_template(template_path)

        assert template.name == "Example"
        assert "driver" in template.fields

    def test_load_template_caches_results(self, tmp_path: Path) -> None:
        """Loading the same template twice returns the cached instance."""
        from tachograph_wizard.core.template_manager import TemplateManager

        template_path = tmp_path / "cached.json"
        template_path.write_text(
            (
                "{"
                '"name":"Cached",'
                '"version":"1.0",'
                '"description":"",'
                '"reference_width":1000,'
                '"reference_height":1000,'
                '"fields":{}'
                "}"
            ),
            encoding="utf-8",
        )

        manager = TemplateManager()
        first = manager.load_template(template_path)
        second = manager.load_template(template_path)

        assert first is second

    def test_load_template_rejects_invalid_json(self, tmp_path: Path) -> None:
        """Invalid JSON templates raise ValueError."""
        from tachograph_wizard.core.template_manager import TemplateManager

        template_path = tmp_path / "bad.json"
        template_path.write_text("{invalid", encoding="utf-8")

        manager = TemplateManager()

        with pytest.raises(ValueError, match="Failed to parse JSON"):
            manager.load_template(template_path)

    def test_list_templates_includes_standard(self) -> None:
        """Default templates list includes the standard template."""
        from tachograph_wizard.core.template_manager import TemplateManager

        manager = TemplateManager()
        templates = manager.list_templates()

        assert "standard" in templates


class TestTextRendererHelpers:
    """Test helper calculations used by TextRenderer."""

    def test_render_all_collects_layers(self, mock_gimp_modules: object) -> None:
        """Collect only non-empty layers returned by render_text."""
        from tachograph_wizard.core.text_renderer import TextRenderer
        from tachograph_wizard.templates.models import FontConfig, PositionConfig, Template, TextField
        from tests.fixtures.mock_gimp import MockGimp

        assert mock_gimp_modules

        image = MockGimp.create_mock_image(width=800, height=600)
        field = TextField(
            position=PositionConfig(x_ratio=0.25, y_ratio=0.5),
            font=FontConfig(size_ratio=0.1),
        )
        template = Template(
            name="Test",
            version="1.0",
            description="",
            reference_width=1000,
            reference_height=1000,
            fields={"driver": field},
        )

        renderer = TextRenderer(image, template)
        renderer_any = cast("Any", renderer)
        renderer_any.render_text = MagicMock(side_effect=[None, "layer"])

        layers = renderer_any.render_all({"driver": "A", "extra": "B"})

        assert layers == ["layer"]
        assert renderer_any.render_text.call_args_list[0].args == ("driver", "A")
        assert renderer_any.render_text.call_args_list[1].args == ("extra", "B")
