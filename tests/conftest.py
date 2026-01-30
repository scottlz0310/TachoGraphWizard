"""Pytest configuration and fixtures.

Provides common fixtures for testing TachoGraphWizard,
including GIMP API mocks and test data.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(autouse=True)
def mock_gimp_modules() -> Iterator[tuple[MagicMock, MagicMock, MagicMock]]:
    """Mock the GIMP gi.repository modules.

    Yields:
        Tuple of (Gimp, GimpUi, Gegl) mock modules.
    """
    # Create mocks
    gimp_mock = MagicMock()
    gimpui_mock = MagicMock()
    gegl_mock = MagicMock()
    gtk_mock = MagicMock()
    gio_mock = MagicMock()
    gobject_mock = MagicMock()

    # Mock PDBStatusType
    gimp_mock.PDBStatusType.SUCCESS = 0
    gimp_mock.PDBStatusType.CANCEL = 1
    gimp_mock.PDBStatusType.EXECUTION_ERROR = 2

    # Mock RunMode
    gimp_mock.RunMode.INTERACTIVE = 0
    gimp_mock.RunMode.NONINTERACTIVE = 1

    # Mock MergeType
    gimp_mock.MergeType.EXPAND_AS_NECESSARY = 0

    # Mock PDB
    from tests.fixtures.mock_gimp import MockGimp

    gimp_mock.get_pdb.return_value = MockGimp.create_mock_pdb()
    gimp_mock.list_images.return_value = []

    # Mock Gegl.Color
    gegl_mock.Color.new.return_value = MockGimp.create_mock_color()

    # Mock GObject.Value
    gobject_mock.Value = MagicMock
    gobject_mock.TYPE_INT = int

    # Install mocks
    sys.modules["gi"] = MagicMock()
    sys.modules["gi.repository"] = MagicMock()
    sys.modules["gi.repository.Gimp"] = gimp_mock
    sys.modules["gi.repository.GimpUi"] = gimpui_mock
    sys.modules["gi.repository.Gegl"] = gegl_mock
    sys.modules["gi.repository.Gtk"] = gtk_mock
    sys.modules["gi.repository.Gio"] = gio_mock
    sys.modules["gi.repository.GObject"] = gobject_mock
    sys.modules["gi.repository.GLib"] = MagicMock()

    yield gimp_mock, gimpui_mock, gegl_mock

    # Cleanup
    modules_to_remove = [
        "gi",
        "gi.repository",
        "gi.repository.Gimp",
        "gi.repository.GimpUi",
        "gi.repository.Gegl",
        "gi.repository.Gtk",
        "gi.repository.Gio",
        "gi.repository.GObject",
        "gi.repository.GLib",
    ]
    for module in modules_to_remove:
        sys.modules.pop(module, None)


@pytest.fixture
def mock_image() -> MagicMock:
    """Create a mock GIMP image.

    Returns:
        Mock Gimp.Image object.
    """
    from tests.fixtures.mock_gimp import MockGimp

    return MockGimp.create_mock_image()


@pytest.fixture
def mock_drawable() -> MagicMock:
    """Create a mock GIMP drawable.

    Returns:
        Mock Gimp.Drawable object.
    """
    from tests.fixtures.mock_gimp import MockGimp

    return MockGimp.create_mock_drawable()


@pytest.fixture
def mock_layer() -> MagicMock:
    """Create a mock GIMP layer.

    Returns:
        Mock Gimp.Layer object.
    """
    from tests.fixtures.mock_gimp import MockGimp

    return MockGimp.create_mock_layer()


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory.

    Args:
        tmp_path: Pytest tmp_path fixture.

    Returns:
        Path to temporary directory.
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
