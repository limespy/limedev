"""Helper functions and values for other modules."""
from collections.abc import Iterable
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import TypeAlias

PATH_BASE = Path(__file__).parent
PATH_DEFAULT_CONFIGS = PATH_BASE / 'configs'

_YAMLelementary: TypeAlias = int | float | str | None
YAMLSafe: TypeAlias = (dict[_YAMLelementary, 'YAMLSafe']
                       | list['YAMLSafe']
                       | _YAMLelementary)
# ======================================================================
def upsearch(patterns: str | Iterable[str],
              path_search: Path = Path.cwd(),
              deep: bool = False,
              path_stop: Path | None = None) -> Path | None:
    """Searches for pattern gradually going up the path."""

    if path_stop is None:
        path_stop = Path(path_search.root)
    elif path_search.root != path_stop.root:
        raise ValueError(f'Start path {path_search} does not share root with stop path {path_stop}')

    if isinstance(patterns, str):
        patterns = (patterns,)

    for path in (path_search, *path_search.parents):
        for pattern in patterns:
            try:
                return next((path.rglob if deep else path.glob
                             )(pattern))
            except StopIteration:
                pass
        if path == path_stop:
            break
    return None
# ----------------------------------------------------------------------
_PATH_CWD = Path.cwd()
PATH_PROJECT = (_PATH_CWD
                if (path_base_child := upsearch(('pyproject.toml',
                                                 '.git',
                                                 'setup.py'),
                                                 _PATH_CWD)) is None
                else path_base_child.parent)

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
