"""Helper functions and values for other modules."""
from collections.abc import Iterable
from enum import auto
from enum import StrEnum
from importlib import util
from math import floor
from math import log10
from pathlib import Path
from sys import version_info
from types import ModuleType
from typing import TYPE_CHECKING
from typing import TypeAlias
# ======================================================================
# Hinting types

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Iterable
    from pathlib import Path
    from typing import TypeAlias

    _YAMLelementary: TypeAlias = int | float | str | None
    YAMLSafe: TypeAlias = (dict[_YAMLelementary, 'YAMLSafe']
                        | list['YAMLSafe']
                        | _YAMLelementary)
    BenchmarkResultsType: TypeAlias = tuple[str, YAMLSafe]
else:
    Generator = Iterable = tuple
    YAMLSafe = object
# ======================================================================
PATH_BASE = Path(__file__).parent
PATH_DEFAULT_CONFIGS = PATH_BASE / 'configs'

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
#%%=====================================================================
def _try_get_path(path_project: Path, patterns: Iterable[str]
                  ) -> Path | None:
    for pattern in patterns:
        try:
            if (path_src := next(path_project.glob(pattern))).is_dir():
                return path_src
        except StopIteration:
            pass
    return None
# ======================================================================
class TypingBackend(StrEnum):
    MYPY = auto()
    PYREFLY = auto()
    TY = auto()

# ======================================================================
PATH_TESTS = _try_get_path(PATH_PROJECT, ('tests', 'test'))
PATH_SRC = _try_get_path(PATH_PROJECT, ('src', 'source')) or PATH_PROJECT
PATH_VERSION_DEFAULTS = (PATH_DEFAULT_CONFIGS
                         / f'{version_info[0]}.{version_info[1]}')
PATH_FALLBACK_DEFAULTS = (PATH_DEFAULT_CONFIGS / 'fallback')

#%%=====================================================================
def _get_default_config(patterns) -> Path | None:
    return (path if (path := upsearch(patterns,
                                      path_search = PATH_VERSION_DEFAULTS,
                                      path_stop = PATH_VERSION_DEFAULTS))
            else upsearch(patterns,
                          path_search = PATH_FALLBACK_DEFAULTS,
                          path_stop = PATH_FALLBACK_DEFAULTS))
#%%=====================================================================
def _get_path_config(patterns: str | Iterable[str],
                     path_start: Path | None = PATH_TESTS
                     ) -> Path | None:
    """Loads test configuration file paths or supplies.

    default if not found.
    """
    if path_start:
        if _path_config := upsearch(patterns, path_start,
                                    path_stop = PATH_PROJECT):
            return _path_config
    return _get_default_config(patterns)
# ======================================================================
def _pack_kwargs(kwargs: dict[str, str]) -> Generator[str, None, None]:

    return (f"--{key}{'=' if value else ''}{value}"
            for key, value in kwargs.items())
# ======================================================================
def _in_pyproject(section: str, path: Path = PATH_PROJECT / 'pyproject.toml'
                  ) -> bool:
    return path.read_text().find(f'\n[tool.{section}]') != -1
# ======================================================================
_prefixes_items = (('n', 1e-9),
                   ('u', 1e-6),
                   ('m', 1e-3),
                   ('',  1.),
                   ('k', 1e3),
                   ('M', 1e6))
prefixes = dict(_prefixes_items)
# ----------------------------------------------------------------------
def sigfig_round(value: float, n_sigfig: int) -> float:
    """Rounds to specified number of significant digits."""
    if value == 0.:
        return value
    return round(value, max(0, n_sigfig - floor(log10(abs(value))) - 1))
# ----------------------------------------------------------------------
def eng_round(value: float, n_sigfig: int = 3) -> tuple[float, str]:
    """Engineering rounding.

    Shifts to nearest SI prefix fraction and rounds to given significant digits.
    """
    prefix_symbol_previous, prefix_value_previous = _prefixes_items[0]
    for prefix_symbol, prefix_value in _prefixes_items[1:]:
        if value < prefix_value:
            break
        prefix_symbol_previous = prefix_symbol
        prefix_value_previous = prefix_value
    return (sigfig_round(value / prefix_value_previous, n_sigfig),
            prefix_symbol_previous)
