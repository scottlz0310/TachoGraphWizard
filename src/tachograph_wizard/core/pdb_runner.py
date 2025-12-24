"""Compatibility helpers for calling GIMP PDB procedures.

GIMP 3 Python GI bindings can differ between builds. In some environments:
- `Gimp.get_pdb()` returns a PDB object without `run_procedure()`.
- The module exposes alternative entry points such as `Gimp.pdb_run_procedure()`.

This module provides a best-effort wrapper that tries multiple invocation paths.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import gi

gi.require_version("Gimp", "3.0")

from gi.repository import Gimp


def _make_value_array(values: Sequence[Any]) -> Any | None:
    value_array_cls = getattr(Gimp, "ValueArray", None)
    new_from_values = getattr(value_array_cls, "new_from_values", None)
    if callable(new_from_values):
        try:
            return new_from_values(list(values))
        except Exception:
            return None
    return None


def _unwrap_gvalue(value: Any) -> Any:
    """Best-effort unwrap for GObject.Value to a Python value."""
    get_value = getattr(value, "get_value", None)
    if callable(get_value):
        try:
            return get_value()
        except Exception:
            return value
    return value


def _list_property_names(obj: Any) -> list[str]:
    """Return GObject property names if available."""
    props: list[str] = []
    list_props = getattr(obj, "list_properties", None)
    if callable(list_props):
        try:
            for spec in list_props():
                name = getattr(spec, "name", None)
                if isinstance(name, str):
                    props.append(name)
        except Exception:
            return []
    return props


def _set_config_property(config: Any, prop_name: str, value: Any) -> bool:
    """Try to set a config property using several PyGObject idioms."""
    try:
        set_prop = getattr(config, "set_property", None)
        if callable(set_prop):
            set_prop(prop_name, value)
            return True
    except Exception:
        pass

    try:
        # Some objects expose properties via .props with underscores
        props_obj = getattr(config, "props", None)
        if props_obj is not None:
            setattr(props_obj, prop_name.replace("-", "_"), value)
            return True
    except Exception:
        pass

    return False


def _populate_config(name: str, config: Any, values: Sequence[Any], *, debug_log: Callable[[str], None] | None) -> None:
    def _log(msg: str) -> None:
        if debug_log is not None:
            debug_log(msg)

    prop_names = set(_list_property_names(config))
    if prop_names:
        _log(f"pdb_config props={sorted(prop_names)[:30]}")

    # Unwrap and map values by heuristic.
    for raw in values:
        v = _unwrap_gvalue(raw)

        # Run mode
        try:
            if isinstance(v, Gimp.RunMode):
                for cand in ("run-mode", "run_mode", "runmode"):
                    if (not prop_names) or (cand in prop_names):
                        if _set_config_property(config, cand, v):
                            _log(f"pdb_config set {cand}={v}")
                            break
                continue
        except Exception:
            pass

        # Image
        try:
            if isinstance(v, Gimp.Image):
                for cand in ("image",):
                    if (not prop_names) or (cand in prop_names):
                        if _set_config_property(config, cand, v):
                            _log(f"pdb_config set {cand}=<Image>")
                            break
                continue
        except Exception:
            pass

        # Drawable
        try:
            if isinstance(v, Gimp.Drawable):
                for cand in ("drawable",):
                    if (not prop_names) or (cand in prop_names):
                        if _set_config_property(config, cand, v):
                            _log(f"pdb_config set {cand}=<Drawable>")
                            break
                continue
        except Exception:
            pass

        # ValueArray (often drawables)
        try:
            if isinstance(v, Gimp.ValueArray):
                for cand in ("drawables", "value-array", "values"):
                    if (not prop_names) or (cand in prop_names):
                        if _set_config_property(config, cand, v):
                            _log(f"pdb_config set {cand}=<ValueArray>")
                            break
                continue
        except Exception:
            pass

        # Fallback: ignore unknowns; we rely on defaults for now.
        _log(f"pdb_config skip arg type={type(v).__name__} for {name}")


def _create_procedure_config(proc: Any, *, debug_log: Callable[[str], None]) -> Any | None:
    def _log(msg: str) -> None:
        debug_log(msg)

    create_config = getattr(proc, "create_config", None)
    if callable(create_config):
        try:
            cfg = create_config()
            _log("pdb_config created via procedure.create_config()")
            return cfg
        except Exception as e:
            _log(f"pdb_config create_config failed: {type(e).__name__}: {e}")

    # Try Gimp.ProcedureConfig constructors (names differ across builds)
    proc_cfg_cls = getattr(Gimp, "ProcedureConfig", None)
    if proc_cfg_cls is not None:
        for ctor_name in ("new", "new_from_procedure"):
            ctor = getattr(proc_cfg_cls, ctor_name, None)
            if callable(ctor):
                try:
                    cfg = ctor(proc)
                    _log(f"pdb_config created via Gimp.ProcedureConfig.{ctor_name}(proc)")
                    return cfg
                except Exception as e:
                    _log(f"pdb_config {ctor_name} failed: {type(e).__name__}: {e}")

    return None


def run_pdb_procedure(
    name: str,
    values: Sequence[Any],
    *,
    debug_log: Callable[[str], None] | None = None,
) -> Any:
    """Run a PDB procedure with compatibility fallbacks.

    Args:
        name: PDB procedure name (e.g. "plug-in-guillotine").
        values: Sequence of arguments (typically GObject.Value and/or ValueArray).
        debug_log: Optional logger.

    Returns:
        The result object returned by the binding.

    Raises:
        AttributeError/RuntimeError if no invocation path succeeds.
    """

    def _log(msg: str) -> None:
        if debug_log is not None:
            debug_log(msg)

    pdb = Gimp.get_pdb()
    args_list = list(values)
    args_va = _make_value_array(values)

    errors: list[str] = []

    def _try(label: str, fn: Callable[[], Any]) -> Any | None:
        try:
            result = fn()
            _log(f"pdb_call ok via {label}")
            return result
        except Exception as e:
            err = f"pdb_call failed via {label}: {type(e).__name__}: {e}"
            errors.append(err)
            _log(err)
            return None

    # 1) PDB instance method (some builds)
    run_proc = getattr(pdb, "run_procedure", None)
    if callable(run_proc):
        result = _try("pdb.run_procedure(list)", lambda: run_proc(name, args_list))
        if result is not None:
            return result
        if args_va is not None:
            result = _try("pdb.run_procedure(ValueArray)", lambda: run_proc(name, args_va))
            if result is not None:
                return result

    # 2) Module-level helper (some builds)
    mod_run = getattr(Gimp, "pdb_run_procedure", None)
    if callable(mod_run):
        result = _try("Gimp.pdb_run_procedure(list)", lambda: mod_run(name, args_list))
        if result is not None:
            return result
        if args_va is not None:
            result = _try("Gimp.pdb_run_procedure(ValueArray)", lambda: mod_run(name, args_va))
            if result is not None:
                return result

    # 3) Lookup procedure object and try running it
    lookup = getattr(pdb, "lookup_procedure", None)
    if callable(lookup):
        proc = _try("pdb.lookup_procedure", lambda: lookup(name))
        if proc is not None:
            proc_run = getattr(proc, "run", None)
            if callable(proc_run):
                result = _try("procedure.run(list)", lambda: proc_run(args_list))
                if result is not None:
                    return result
                if args_va is not None:
                    result = _try("procedure.run(ValueArray)", lambda: proc_run(args_va))
                    if result is not None:
                        return result

                # 4) Some builds require a ProcedureConfig object
                cfg = _create_procedure_config(proc, debug_log=_log)
                if cfg is not None:
                    try:
                        _populate_config(name, cfg, values, debug_log=_log)
                    except Exception as e:
                        _log(f"pdb_config populate failed: {type(e).__name__}: {e}")

                    result = _try("procedure.run(config)", lambda: proc_run(cfg))
                    if result is not None:
                        return result

    msg = "Unable to run PDB procedure; no compatible binding entry point worked."
    if errors:
        msg += " Last errors: " + " | ".join(errors[-3:])
    raise AttributeError(msg)
