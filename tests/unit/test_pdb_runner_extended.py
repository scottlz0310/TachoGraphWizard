# pyright: reportPrivateUsage=false
"""Extended unit tests for pdb_runner - covers run_pdb_procedure and helper functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestMakeValueArray:
    """Test _make_value_array function."""

    def test_make_value_array_success(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_make_value_array creates value array from list."""
        from tachograph_wizard.core.pdb_runner import _make_value_array

        result = _make_value_array([1, 2, 3])
        # With mock GIMP, the return will be from mock
        assert result is not None

    @patch("tachograph_wizard.core.pdb_runner.Gimp")
    def test_make_value_array_no_class(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """_make_value_array returns None when ValueArray class is missing."""
        from tachograph_wizard.core.pdb_runner import _make_value_array

        mock_gimp.ValueArray = None

        result = _make_value_array([1, 2, 3])
        assert result is None


class TestUnwrapGvalue:
    """Test _unwrap_gvalue function."""

    def test_unwrap_with_get_value(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Unwraps value via get_value() method."""
        from tachograph_wizard.core.pdb_runner import _unwrap_gvalue

        obj = MagicMock()
        obj.get_value.return_value = 42
        assert _unwrap_gvalue(obj) == 42

    def test_unwrap_plain_value(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns plain value as-is."""
        from tachograph_wizard.core.pdb_runner import _unwrap_gvalue

        assert _unwrap_gvalue(42) == 42
        assert _unwrap_gvalue("hello") == "hello"

    def test_unwrap_failing_get_value(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns original when get_value raises."""
        from tachograph_wizard.core.pdb_runner import _unwrap_gvalue

        obj = MagicMock()
        obj.get_value.side_effect = Exception("fail")
        result = _unwrap_gvalue(obj)
        assert result is obj


class TestListPropertyNames:
    """Test _list_property_names function."""

    def test_with_properties(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Extracts property names from object."""
        from tachograph_wizard.core.pdb_runner import _list_property_names

        spec1 = MagicMock()
        spec1.name = "prop-a"
        spec2 = MagicMock()
        spec2.name = "prop-b"

        obj = MagicMock()
        obj.list_properties.return_value = [spec1, spec2]

        result = _list_property_names(obj)
        assert result == ["prop-a", "prop-b"]

    def test_without_list_properties(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns empty list when list_properties not available."""
        from tachograph_wizard.core.pdb_runner import _list_property_names

        result = _list_property_names(42)
        assert result == []

    def test_list_properties_raises(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns empty list when list_properties raises."""
        from tachograph_wizard.core.pdb_runner import _list_property_names

        obj = MagicMock()
        obj.list_properties.side_effect = Exception("fail")

        result = _list_property_names(obj)
        assert result == []


class TestSetConfigProperty:
    """Test _set_config_property function."""

    def test_via_set_property(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Uses set_property when available."""
        from tachograph_wizard.core.pdb_runner import _set_config_property

        config = MagicMock()
        assert _set_config_property(config, "test", 42) is True

    def test_via_props(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Falls back to props attribute."""
        from tachograph_wizard.core.pdb_runner import _set_config_property

        config = MagicMock()
        config.set_property.side_effect = Exception("fail")
        config.props = MagicMock()

        assert _set_config_property(config, "test-prop", 42) is True

    def test_all_fail(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns False when all methods fail."""
        from tachograph_wizard.core.pdb_runner import _set_config_property

        config = MagicMock()
        config.set_property.side_effect = Exception("fail")
        config.props = None

        assert _set_config_property(config, "test", 42) is False


class TestCreateProcedureConfig:
    """Test _create_procedure_config function."""

    def test_via_create_config(
        self,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Uses proc.create_config() when available."""
        from tachograph_wizard.core.pdb_runner import _create_procedure_config

        proc = MagicMock()
        config = MagicMock()
        proc.create_config.return_value = config

        result = _create_procedure_config(proc)
        assert result is config

    @patch("tachograph_wizard.core.pdb_runner.Gimp")
    def test_create_config_fails_fallback_to_none(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Returns None when all fallbacks fail."""
        from tachograph_wizard.core.pdb_runner import _create_procedure_config

        mock_gimp.ProcedureConfig = None

        proc = MagicMock()
        proc.create_config.side_effect = Exception("fail")

        result = _create_procedure_config(proc)
        assert result is None


class TestRunPdbProcedure:
    """Test run_pdb_procedure function."""

    @patch("tachograph_wizard.core.pdb_runner.Gimp")
    def test_run_pdb_via_run_procedure(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Run via pdb.run_procedure succeeds."""
        from tachograph_wizard.core.pdb_runner import run_pdb_procedure

        pdb = MagicMock()
        result_obj = MagicMock()
        pdb.run_procedure.return_value = result_obj
        mock_gimp.get_pdb.return_value = pdb

        result = run_pdb_procedure("test-proc", [])
        assert result is result_obj

    @patch("tachograph_wizard.core.pdb_runner.Gimp")
    def test_run_pdb_via_module_level(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Run via Gimp.pdb_run_procedure succeeds."""
        from tachograph_wizard.core.pdb_runner import run_pdb_procedure

        pdb = MagicMock()
        pdb.run_procedure.side_effect = Exception("not available")
        mock_gimp.get_pdb.return_value = pdb

        result_obj = MagicMock()
        mock_gimp.pdb_run_procedure = MagicMock(return_value=result_obj)

        result = run_pdb_procedure("test-proc", [])
        assert result is result_obj

    @patch("tachograph_wizard.core.pdb_runner.Gimp")
    def test_run_pdb_via_lookup_procedure_run(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Run via pdb.lookup_procedure + proc.run succeeds."""
        from tachograph_wizard.core.pdb_runner import run_pdb_procedure

        pdb = MagicMock()
        pdb.run_procedure.side_effect = Exception("not available")
        mock_gimp.pdb_run_procedure = MagicMock(side_effect=Exception("not available"))
        mock_gimp.get_pdb.return_value = pdb

        proc = MagicMock()
        result_obj = MagicMock()
        proc.run.return_value = result_obj
        pdb.lookup_procedure.return_value = proc

        result = run_pdb_procedure("test-proc", [])
        assert result is result_obj

    @patch("tachograph_wizard.core.pdb_runner.Gimp")
    def test_run_pdb_all_fail_raises(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Raises AttributeError when all invocation paths fail."""
        from tachograph_wizard.core.pdb_runner import run_pdb_procedure

        pdb = MagicMock()
        pdb.run_procedure.side_effect = Exception("fail")
        mock_gimp.pdb_run_procedure = MagicMock(side_effect=Exception("fail"))
        mock_gimp.get_pdb.return_value = pdb

        proc = MagicMock()
        proc.run.side_effect = Exception("fail")
        proc.create_config.side_effect = Exception("fail")
        pdb.lookup_procedure.return_value = proc

        mock_gimp.ProcedureConfig = None

        with pytest.raises(AttributeError, match="Unable to run"):
            run_pdb_procedure("test-proc", [])

    @patch("tachograph_wizard.core.pdb_runner.Gimp")
    def test_run_pdb_with_debug_log_on_failure(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """debug_log is called when all invocation paths fail."""
        from tachograph_wizard.core.pdb_runner import run_pdb_procedure

        pdb = MagicMock()
        pdb.run_procedure.side_effect = Exception("fail")
        mock_gimp.pdb_run_procedure = MagicMock(side_effect=Exception("fail"))
        mock_gimp.get_pdb.return_value = pdb

        proc = MagicMock()
        proc.run.side_effect = Exception("fail")
        proc.create_config.side_effect = Exception("fail")
        pdb.lookup_procedure.return_value = proc

        mock_gimp.ProcedureConfig = None

        log_messages: list[str] = []

        with pytest.raises(AttributeError):
            run_pdb_procedure("test-proc", [], debug_log=log_messages.append)

        assert any("Unable to run" in msg for msg in log_messages)

    @patch("tachograph_wizard.core.pdb_runner.Gimp")
    def test_run_pdb_via_config(
        self,
        mock_gimp: MagicMock,
        mock_gimp_modules: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Run via procedure.run(config) when direct run fails."""
        from tachograph_wizard.core.pdb_runner import run_pdb_procedure

        pdb = MagicMock()
        pdb.run_procedure.side_effect = Exception("fail")
        mock_gimp.pdb_run_procedure = MagicMock(side_effect=Exception("fail"))
        mock_gimp.get_pdb.return_value = pdb
        mock_gimp.ProcedureConfig = None

        config = MagicMock()
        config.list_properties.return_value = []
        proc = MagicMock()

        # proc.run: first call (list) fails, second (config) succeeds
        result_obj = MagicMock()
        call_count = [0]

        def run_side_effect(_arg: object) -> object:
            call_count[0] += 1
            if call_count[0] <= 1:
                msg = "fail"
                raise RuntimeError(msg)
            return result_obj

        proc.run.side_effect = run_side_effect
        proc.create_config.return_value = config
        pdb.lookup_procedure.return_value = proc

        # No ValueArray so only list path tried for direct run
        mock_gimp.ValueArray = None

        result = run_pdb_procedure("test-proc", [])
        assert result is result_obj
