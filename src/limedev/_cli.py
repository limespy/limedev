"""Package internal cli."""
from importlib import import_module
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
        return import_module('.package', __package__).package
    if name == 'readme':
        return import_module('.readme', __package__).main
    if name in {'benchmarking', 'linting', 'profiling', 'typing', 'unittests'}:
        return getattr(import_module('.test', __package__), name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
# ======================================================================
main = get_main(__name__)
