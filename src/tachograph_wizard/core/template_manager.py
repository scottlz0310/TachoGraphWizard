"""Template management for loading and managing text field templates."""

from __future__ import annotations

import json
from pathlib import Path

from tachograph_wizard.templates.models import Template


class TemplateManager:
    """Manages loading and caching of templates."""

    def __init__(self) -> None:
        """Initialize the template manager."""
        self._templates_dir = Path(__file__).parent.parent / "templates" / "default_templates"
        self._cache: dict[str, Template] = {}
        self._file_extension = ".json"

    def load_template(self, template_path: Path) -> Template:
        """Load a template from a JSON file.

        Args:
            template_path: Path to the template JSON file.

        Returns:
            Loaded Template instance.

        Raises:
            FileNotFoundError: If the template file doesn't exist.
            ValueError: If the template file is invalid.
        """
        if not template_path.exists():
            msg = f"Template file not found: {template_path}"
            raise FileNotFoundError(msg)

        # Check cache
        cache_key = str(template_path.resolve())
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Load from file
        try:
            with template_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                msg = f"Invalid template format: {template_path}"
                raise TypeError(msg)

            template = Template.from_dict(data)
            self._cache[cache_key] = template
            return template

        except json.JSONDecodeError as e:
            msg = f"Failed to parse JSON template: {e}"
            raise ValueError(msg) from e

    def list_templates(self) -> list[str]:
        """List available template names in the default templates directory.

        Returns:
            List of template names (without .json extension).
        """
        if not self._templates_dir.exists():
            return []

        templates = sorted(self._templates_dir.glob(f"*{self._file_extension}"))
        return [template.stem for template in templates]

    def get_template_path(self, template_name: str) -> Path:
        """Get the path to a template by name.

        Args:
            template_name: Name of the template (without .json extension).

        Returns:
            Path to the template file.
        """
        return self._templates_dir / f"{template_name}{self._file_extension}"

    def get_default_template(self) -> Template:
        """Get the default template.

        Returns:
            The default Template instance.

        Raises:
            FileNotFoundError: If the default template doesn't exist.
        """
        default_path = self.get_template_path("standard")
        return self.load_template(default_path)

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._cache.clear()
