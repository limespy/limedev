"""Helper functions and values for other modules."""
import pathlib
from collections.abc import Iterable
from importlib import util
from types import ModuleType
from typing import Union

PATH_BASE = pathlib.Path(__file__).parent
PATH_CONFIGS = PATH_BASE / 'configs'

# ======================================================================
def _upsearch(patterns: Union[str, Iterable[str]],
              path_search = pathlib.Path.cwd(),
              deep = False) -> pathlib.Path | None:
    """Searches for pattern gradually going up the path."""
    path_previous = pathlib.Path()
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
if (path_base_child := _upsearch(('pyproject.toml',
                                  '.git',
                                  'setup.py'))) is None:
    raise FileNotFoundError('Base path not found')
PATH_REPO = path_base_child.parent
# ======================================================================
def _import_from_path(path_module: pathlib.Path) -> ModuleType:
    """Imports python module from a path."""
    spec = util.spec_from_file_location(path_module.stem, path_module)

    # creates a new module based on spec
    module = util.module_from_spec(spec) # type: ignore

    # executes the module in its own namespace
    # when a module is imported or reloaded.
    spec.loader.exec_module(module) # type: ignore
    return module
# ======================================================================
def _argumentparser(args_in: Iterable[str]
                    ) -> tuple[list[str], dict[str, str]]:
    args = []
    kwargs = {}
    for arg in args_in:
        if arg.startswith('--'):
            keyword, _, value = arg[2:].partition('=')
            kwargs[keyword] = value
        else:
            args.append(arg)
    return args, kwargs
