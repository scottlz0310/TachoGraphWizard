"""Template exporter for extracting text layer configuration."""

from __future__ import annotations

import datetime
import json
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

import gi

gi.require_version("Gegl", "0.4")
gi.require_version("Gimp", "3.0")

from gi.repository import Gegl, Gimp

from tachograph_wizard.templates.models import FontConfig, PositionConfig, Template, TextField


class TemplateExportError(RuntimeError):
    """Raised when exporting a template fails."""


def _log_path() -> Path:
    base = os.environ.get("TEMP") or os.environ.get("TMP") or os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "tachograph_wizard.log"


def _debug_log(message: str) -> None:
    try:
        ts = datetime.datetime.now(tz=datetime.UTC).isoformat(timespec="seconds")
        with _log_path().open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{ts}] template_exporter: {message}\n")
    except Exception:
        return


def _unwrap_value(value: Any) -> Any:
    get_value = getattr(value, "get_value", None)
    if callable(get_value):
        try:
            return get_value()
        except Exception:
            return value
    return value


def _extract_result_values(result: Any) -> list[Any]:
    values: list[Any] = []
    for index in range(5):
        try:
            raw = result.index(index)
        except Exception:
            break
        values.append(_unwrap_value(raw))
    return values


def _list_property_names(obj: object) -> list[str]:
    props: list[str] = []
    list_props = getattr(obj, "list_properties", None)
    if callable(list_props):
        try:
            result = list_props()
        except Exception:
            return props
        if isinstance(result, Iterable) and not isinstance(result, (str, bytes)):
            for spec in result:
                name = getattr(spec, "name", None)
                if isinstance(name, str):
                    props.append(name)
    return props


def _set_config_property(config: object, prop_name: str, value: object) -> bool:
    set_prop = getattr(config, "set_property", None)
    if callable(set_prop):
        try:
            set_prop(prop_name, value)
            return True
        except Exception:
            pass

    props_obj = getattr(config, "props", None)
    if props_obj is not None:
        try:
            setattr(props_obj, prop_name.replace("-", "_"), value)
            return True
        except Exception:
            return False

    return False


def _create_procedure_config(proc: object) -> object | None:
    create_config = getattr(proc, "create_config", None)
    if callable(create_config):
        try:
            return create_config()
        except Exception:
            pass

    proc_cfg_cls = getattr(Gimp, "ProcedureConfig", None)
    if proc_cfg_cls is not None:
        for ctor_name in ("new", "new_from_procedure"):
            ctor = getattr(proc_cfg_cls, ctor_name, None)
            if callable(ctor):
                try:
                    return ctor(proc)
                except Exception:
                    pass

    return None


def _iter_layers(layers: list[Gimp.Layer]) -> list[Gimp.Layer]:
    all_layers: list[Gimp.Layer] = []
    for layer in layers:
        all_layers.append(layer)
        get_children = getattr(layer, "get_children", None)
        if callable(get_children):
            try:
                children = get_children()
            except Exception:
                children = []
            if isinstance(children, list) and children:
                all_layers.extend(_iter_layers(children))
    return all_layers


def _is_text_layer(layer: Gimp.Layer) -> bool:
    text_layer_cls = getattr(Gimp, "TextLayer", None)
    if text_layer_cls is not None and isinstance(layer, text_layer_cls):
        return True

    is_text = getattr(layer, "is_text_layer", None)
    if callable(is_text):
        try:
            return bool(is_text())
        except Exception:
            return False

    return False


def _extract_offsets(offsets: object) -> tuple[float, float]:
    if isinstance(offsets, tuple):
        if len(offsets) >= 3 and isinstance(offsets[0], bool):
            return float(offsets[1]), float(offsets[2])
        if len(offsets) >= 2:
            return float(offsets[0]), float(offsets[1])

    offset_x = getattr(offsets, "offset_x", None)
    offset_y = getattr(offsets, "offset_y", None)
    if isinstance(offset_x, (int, float)) and isinstance(offset_y, (int, float)):
        return float(offset_x), float(offset_y)

    msg = "Unable to read layer offsets."
    raise TemplateExportError(msg)


def _read_color_components(color: Any) -> tuple[float, float, float]:
    if not isinstance(color, Gegl.Color):
        msg = "Unexpected color type."
        raise TemplateExportError(msg)

    get_rgba = getattr(color, "get_rgba", None)
    if callable(get_rgba):
        try:
            rgba = get_rgba()
        except Exception:
            msg = "Failed to read color values."
            raise TemplateExportError(msg) from None
        if isinstance(rgba, (list, tuple)) and len(rgba) >= 4:
            r, g, b, _a = rgba[:4]
        else:
            msg = "Failed to read color values."
            raise TemplateExportError(msg)
    else:
        r = getattr(color, "r", None)
        g = getattr(color, "g", None)
        b = getattr(color, "b", None)

    r_val = float(r) if isinstance(r, (int, float)) else None
    g_val = float(g) if isinstance(g, (int, float)) else None
    b_val = float(b) if isinstance(b, (int, float)) else None
    if r_val is None or g_val is None or b_val is None:
        msg = "Failed to read color components."
        raise TemplateExportError(msg)

    return r_val, g_val, b_val


def _color_to_hex(color: Any) -> str:
    r, g, b = _read_color_components(color)

    def _clamp(value: float) -> int:
        return max(0, min(255, round(value * 255)))

    return f"#{_clamp(r):02x}{_clamp(g):02x}{_clamp(b):02x}"


def _justification_to_align(value: Any) -> Literal["left", "center", "right"]:
    name = None
    if hasattr(value, "name"):
        name = getattr(value, "name", None)
    if not isinstance(name, str):
        name = str(value)

    name = name.upper()
    if "CENTER" in name:
        return "center"
    if "RIGHT" in name:
        return "right"
    return "left"


class TemplateExporter:
    """Extracts text layer data and exports a template JSON."""

    def __init__(self, image: Gimp.Image) -> None:
        self.image = image
        self.image_width = image.get_width()
        self.image_height = image.get_height()
        self.shorter_side = min(self.image_width, self.image_height)
        self.pdb = Gimp.get_pdb()

    @staticmethod
    def parse_layer_name(layer_name: str) -> str | None:
        prefix = "text:"
        if layer_name.lower().startswith(prefix):
            field_name = layer_name[len(prefix) :].strip()
            return field_name or None
        return None

    def list_field_names(self) -> list[str]:
        layers = _iter_layers(self.image.get_layers())
        names = []
        for layer in layers:
            if not _is_text_layer(layer):
                continue
            try:
                layer_name = layer.get_name()
            except Exception:
                continue
            field_name = self.parse_layer_name(layer_name)
            if field_name:
                names.append(field_name)
        return names

    def export_template(
        self,
        template_name: str,
        output_path: Path,
        *,
        description: str = "",
    ) -> Path:
        template_name = template_name.strip()
        if not template_name:
            msg = "Template name is required."
            raise TemplateExportError(msg)

        fields = self._extract_fields()
        if not fields:
            msg = "No text layers with valid field names were found."
            raise TemplateExportError(msg)

        template = Template(
            name=template_name,
            version="1.0",
            description=description,
            reference_width=int(self.image_width),
            reference_height=int(self.image_height),
            fields=fields,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self._template_to_dict(template), indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        return output_path

    def _extract_fields(self) -> dict[str, TextField]:
        layers = _iter_layers(self.image.get_layers())
        fields: dict[str, TextField] = {}
        for layer in layers:
            if not _is_text_layer(layer):
                continue

            try:
                layer_name = layer.get_name()
            except Exception:
                continue

            field_name = self.parse_layer_name(layer_name)
            if not field_name:
                _debug_log(f"Skipping layer without field name: {layer_name}")
                continue

            if field_name in fields:
                msg = f"Duplicate field name detected: {field_name}"
                raise TemplateExportError(msg)

            fields[field_name] = self._build_field(layer)

        return fields

    def _build_field(self, layer: Gimp.Layer) -> TextField:
        offset_x, offset_y = _extract_offsets(layer.get_offsets())

        font = self._get_text_layer_value("gimp-text-layer-get-font", layer)[0]
        font_name = getattr(font, "get_name", None)
        name_value = font_name() if callable(font_name) else None
        family = name_value if isinstance(name_value, str) else str(font)

        font_size_value, font_unit = self._get_text_layer_value("gimp-text-layer-get-font-size", layer)[:2]
        font_size = float(font_size_value)
        font_size_px = self._font_size_to_pixels(font_size, font_unit)

        color = self._get_text_layer_value("gimp-text-layer-get-color", layer)[0]
        color_hex = _color_to_hex(color)

        justification = self._get_text_layer_value("gimp-text-layer-get-justification", layer)[0]
        align = _justification_to_align(justification)

        position = PositionConfig(
            x_ratio=offset_x / self.image_width,
            y_ratio=offset_y / self.image_height,
        )
        font_config = FontConfig(
            family=family,
            size_ratio=font_size_px / self.shorter_side,
            color=color_hex,
        )
        return TextField(
            position=position,
            font=font_config,
            align=align,
            vertical_align="top",
            visible=True,
            required=False,
        )

    def _get_text_layer_value(self, proc_name: str, layer: Gimp.Layer) -> list[Any]:
        proc = self.pdb.lookup_procedure(proc_name)
        if proc is None:
            msg = f"Procedure not available: {proc_name}"
            raise TemplateExportError(msg)

        cfg = _create_procedure_config(proc)
        if cfg is None:
            msg = f"Unable to create ProcedureConfig for {proc_name}"
            raise TemplateExportError(msg)

        prop_names = set(_list_property_names(cfg))
        for cand in ("run-mode", "run_mode", "runmode"):
            if not prop_names or cand in prop_names:
                _set_config_property(cfg, cand, Gimp.RunMode.NONINTERACTIVE)
                break

        layer_set = False
        for cand in ("layer", "text-layer", "text_layer", "textlayer"):
            if not prop_names or cand in prop_names:
                if _set_config_property(cfg, cand, layer):
                    layer_set = True
                    break

        if not layer_set:
            msg = f"Unable to set layer property for {proc_name}"
            raise TemplateExportError(msg)

        run = getattr(proc, "run", None)
        if not callable(run):
            msg = f"Procedure '{proc_name}' cannot be run"
            raise TemplateExportError(msg)

        result = run(cfg)
        values = _extract_result_values(result)
        if not values:
            msg = f"No values returned by {proc_name}"
            raise TemplateExportError(msg)

        status = values[0]
        success = getattr(Gimp.PDBStatusType, "SUCCESS", None)
        if isinstance(status, Gimp.PDBStatusType) and success is not None and status != success:
            msg = f"{proc_name} returned {status}"
            raise TemplateExportError(msg)

        return values[1:]

    def _font_size_to_pixels(self, font_size: float, font_unit: Any) -> float:
        unit_name = getattr(font_unit, "get_name", None)
        unit_label = unit_name() if callable(unit_name) else str(font_unit)
        if isinstance(unit_label, str):
            label = unit_label.lower()
            if "pixel" in label:
                return font_size
            if "point" in label or label in {"pt"}:
                dpi = self._get_image_dpi()
                return font_size * (dpi / 72.0)

        _debug_log(f"Unexpected font unit '{unit_label}', treating as pixels.")
        return font_size

    def _get_image_dpi(self) -> float:
        try:
            resolution = self.image.get_resolution()
        except Exception:
            resolution = None

        if isinstance(resolution, (tuple, list)) and len(resolution) >= 2:
            try:
                x_res = float(resolution[0])
                y_res = float(resolution[1])
                dpi = y_res if y_res > 0 else x_res
                if dpi > 0:
                    return dpi
            except (TypeError, ValueError):
                pass

        return 72.0

    @staticmethod
    def _template_to_dict(template: Template) -> dict[str, Any]:
        fields = {}
        for name, field in template.fields.items():
            fields[name] = {
                "position": {
                    "x_ratio": field.position.x_ratio,
                    "y_ratio": field.position.y_ratio,
                },
                "font": {
                    "family": field.font.family,
                    "size_ratio": field.font.size_ratio,
                    "color": field.font.color,
                    "bold": field.font.bold,
                    "italic": field.font.italic,
                },
                "align": field.align,
                "vertical_align": field.vertical_align,
                "visible": field.visible,
                "required": field.required,
            }

        return {
            "name": template.name,
            "version": template.version,
            "description": template.description,
            "reference_width": template.reference_width,
            "reference_height": template.reference_height,
            "fields": fields,
        }
