"""Package internal cli."""
from typing import TYPE_CHECKING

from .cli import get_main
# ======================================================================
if TYPE_CHECKING:
    from collections.abc import Callable
else:
    Callable = tuple
# ======================================================================
def __getattr__(name: str) -> Callable[..., int]:
    if name == 'package':
        from .package import package
        return package # type: ignore[return-value]
    if name == 'readme':
        from .readme import main as _main
        return _main
    tools = {'benchmark': 'benchmarking',
             'lint': 'linting',
             'profile': 'profiling',
             'typecheck': 'typing',
             'unittest': 'unittesting'}
    if module_name := tools.get(name):
        from importlib import import_module
        from sys import modules

        module = import_module(f'.{module_name}', __package__)
        setattr(modules[__package__], module_name, module)
        return module.main

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
# ======================================================================
main = get_main(__name__)
