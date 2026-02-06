# pyright: reportPrivateUsage=false
"""Unit tests for TextRenderer - covers helper methods and render paths."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestTextRendererHelpers:
    """Test TextRenderer helper methods."""

    def _create_renderer(self) -> object:
        """Create a TextRenderer with mocked dependencies."""
        from tachograph_wizard.core.text_renderer import TextRenderer
        from tachograph_wizard.templates.models import FontConfig, PositionConfig, Template, TextField

        image = MagicMock()
        image.get_width.return_value = 1000
        image.get_height.return_value = 800

        template = Template(
            name="test",
            version="1.0",
            description="test template",
            reference_width=1000,
            reference_height=800,
            fields={
                "driver": TextField(
                    position=PositionConfig(x_ratio=0.1, y_ratio=0.2),
                    font=FontConfig(family="Arial", size_ratio=0.05, color="#ff0000"),
                    align="left",
                    vertical_align="top",
                    visible=True,
                    required=False,
                ),
                "vehicle": TextField(
                    position=PositionConfig(x_ratio=0.5, y_ratio=0.5),
                    font=FontConfig(family="Arial", size_ratio=0.03, color="#000000"),
                    align="center",
                    vertical_align="middle",
                    visible=True,
                    required=False,
                ),
                "hidden": TextField(
                    position=PositionConfig(x_ratio=0.0, y_ratio=0.0),
                    font=FontConfig(family="Arial", size_ratio=0.02, color="#000000"),
                    align="right",
                    vertical_align="bottom",
                    visible=False,
                    required=False,
                ),
            },
        )

        return TextRenderer(image, template)

    def test_calculate_font_size(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Font size is calculated from shorter side * ratio."""
        renderer = self._create_renderer()
        # shorter side = 800, size_ratio = 0.05
        size = renderer._calculate_font_size(0.05)
        assert size == 800 * 0.05

    def test_calculate_position(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Position is calculated from image dimensions * ratios."""
        from tachograph_wizard.templates.models import FontConfig, PositionConfig, TextField

        renderer = self._create_renderer()
        field = TextField(
            position=PositionConfig(x_ratio=0.5, y_ratio=0.25),
            font=FontConfig(family="Arial", size_ratio=0.05, color="#000000"),
            align="left",
            vertical_align="top",
            visible=True,
            required=False,
        )

        x, y = renderer._calculate_position(field)
        assert x == 500.0  # 1000 * 0.5
        assert y == 200.0  # 800 * 0.25

    def test_parse_color(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Parse hex color to Gegl.Color."""
        renderer = self._create_renderer()
        color = renderer._parse_color("#ff8040")
        # Should have set_rgba called with normalized values
        color.set_rgba.assert_called_once_with(1.0, 128 / 255.0, 64 / 255.0, 1.0)

    def test_parse_color_without_hash(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Parse hex color without leading #."""
        renderer = self._create_renderer()
        color = renderer._parse_color("000000")
        # Assert the last call was with (0.0, 0.0, 0.0, 1.0)
        color.set_rgba.assert_called_with(0.0, 0.0, 0.0, 1.0)

    def test_render_text_unknown_field(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """render_text returns None for unknown field."""
        renderer = self._create_renderer()
        result = renderer.render_text("nonexistent", "test")
        assert result is None

    def test_render_text_hidden_field(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """render_text returns None for hidden field."""
        renderer = self._create_renderer()
        result = renderer.render_text("hidden", "test")
        assert result is None

    def test_render_text_empty_text(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """render_text returns None for empty text."""
        renderer = self._create_renderer()
        result = renderer.render_text("driver", "   ")
        assert result is None

    @patch("tachograph_wizard.core.text_renderer.Gimp")
    @patch("tachograph_wizard.core.text_renderer.run_pdb_procedure")
    def test_render_text_success(
        self,
        mock_run_pdb: MagicMock,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """render_text creates and positions text layer."""
        renderer = self._create_renderer()

        # Setup PDB
        pdb = MagicMock()
        mock_gimp.get_pdb.return_value = pdb

        proc = MagicMock()
        config = MagicMock()
        proc.create_config.return_value = config
        pdb.lookup_procedure.return_value = proc

        text_layer = MagicMock()
        text_layer.get_width.return_value = 50
        text_layer.get_height.return_value = 20

        result_obj = MagicMock()
        result_obj.index.side_effect = lambda i: text_layer if i == 1 else MagicMock()  # type: ignore[arg-type]
        proc.run.return_value = result_obj

        mock_gimp.RunMode.NONINTERACTIVE = 1

        layer = renderer.render_text("driver", "Test Driver")
        assert layer is text_layer

    @patch("tachograph_wizard.core.text_renderer.Gimp")
    @patch("tachograph_wizard.core.text_renderer.run_pdb_procedure")
    def test_render_text_center_alignment(
        self,
        mock_run_pdb: MagicMock,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """render_text adjusts position for center alignment."""
        renderer = self._create_renderer()

        pdb = MagicMock()
        mock_gimp.get_pdb.return_value = pdb

        proc = MagicMock()
        config = MagicMock()
        proc.create_config.return_value = config
        pdb.lookup_procedure.return_value = proc

        text_layer = MagicMock()
        text_layer.get_width.return_value = 100
        text_layer.get_height.return_value = 30

        result_obj = MagicMock()
        result_obj.index.side_effect = lambda i: text_layer if i == 1 else MagicMock()  # type: ignore[arg-type]
        proc.run.return_value = result_obj

        mock_gimp.RunMode.NONINTERACTIVE = 1

        layer = renderer.render_text("vehicle", "Test Vehicle")
        assert layer is text_layer
        # Check center alignment: x = 500 - 100/2 = 450, y = 400 - 30/2 = 385
        text_layer.set_offsets.assert_called_once_with(450, 385)

    @patch("tachograph_wizard.core.text_renderer.Gimp")
    def test_render_text_no_proc_returns_none(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """render_text returns None when no text procedure found."""
        renderer = self._create_renderer()

        pdb = MagicMock()
        mock_gimp.get_pdb.return_value = pdb
        pdb.lookup_procedure.return_value = None

        layer = renderer.render_text("driver", "Test")
        assert layer is None

    def test_render_all(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """render_all renders all provided fields."""
        renderer = self._create_renderer()

        # Mock render_text to return mock layers
        mock_layer1 = MagicMock()
        mock_layer2 = MagicMock()

        call_count = [0]

        def mock_render(field_name: str, _text: str) -> object:
            call_count[0] += 1
            if field_name == "driver":
                return mock_layer1
            if field_name == "vehicle":
                return mock_layer2
            return None

        renderer.render_text = mock_render  # type: ignore[assignment]

        data = {"driver": "Taro", "vehicle": "ABC-123", "unknown": "skip"}
        layers = renderer.render_all(data)

        assert len(layers) == 2

    def test_render_from_csv_row(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """render_from_csv_row delegates to render_all."""
        renderer = self._create_renderer()

        called_with: dict[str, str] = {}

        def mock_render_all(data: dict[str, str]) -> list[object]:
            called_with.update(data)
            return []

        renderer.render_all = mock_render_all  # type: ignore[assignment]

        row = {"driver": "Test", "vehicle": "123"}
        renderer.render_from_csv_row(row)

        assert called_with == row
