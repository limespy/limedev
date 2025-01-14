"""Helper functions and values for other modules."""
from collections.abc import Iterable
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import TypeAlias

PATH_BASE = Path(__file__).parent
PATH_CONFIGS = PATH_BASE / 'configs'

_YAMLelementary: TypeAlias = int | float | str | None
YAMLSafe: TypeAlias = (dict[_YAMLelementary, 'YAMLSafe']
                       | list['YAMLSafe']
                       | _YAMLelementary)
# ======================================================================
def upsearch(patterns: str | Iterable[str],
              path_search = Path.cwd(),
              deep = False) -> Path | None:
    """Searches for pattern gradually going up the path."""
    path_previous = Path()
    if isinstance(patterns, str):
        patterns = (patterns,)
    while True:
        for pattern in patterns:
            try:
                return next(path_search.rglob(pattern) if deep
                            else path_search.glob(pattern))
            except StopIteration:
                pass
        path_previous, path_search = path_search, path_search.parent
        if path_search == path_previous:
            return None
# ----------------------------------------------------------------------
if (path_base_child := upsearch(('pyproject.toml',
                                  '.git',
                                  'setup.py'))) is None:
    raise FileNotFoundError('Base path not found')
PATH_REPO = path_base_child.parent
# ======================================================================
def import_from_path(path_module: Path) -> ModuleType:
    """Imports python module from a path."""
    spec = util.spec_from_file_location(path_module.stem, path_module)

    # creates a new module based on spec
    module = util.module_from_spec(spec) # type: ignore

    # executes the module in its own namespace
    # when a module is imported or reloaded.
    spec.loader.exec_module(module) # type: ignore
    return module
