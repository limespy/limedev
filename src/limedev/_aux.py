'''Helper functions and values for other modules'''
import pathlib
from importlib import util
from typing import Iterable
from typing import Optional
from typing import Union


def _upsearch(patterns: Union[str, Iterable[str]],
              path_search = pathlib.Path.cwd(),
              deep = False) -> Optional[pathlib.Path]:
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

if (path_base_child := _upsearch(('pyproject.toml',
                                  '.git',
                                  'setup.py'))) is None:
    raise FileNotFoundError('Base path not found')
PATH_BASE = path_base_child.parent

def _import_from_path(path_module: pathlib.Path):
    spec = util.spec_from_file_location(path_module.stem, path_module)

    # creates a new module based on spec
    module = util.module_from_spec(spec) # type: ignore

    # executes the module in its own namespace
    # when a module is imported or reloaded.
    spec.loader.exec_module(module) # type: ignore
    return module
