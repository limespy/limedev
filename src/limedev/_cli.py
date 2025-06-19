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
    if name in {'benchmarking', 'linting', 'profiling', 'typing', 'unittests'}:
        from . import test
        return getattr(test, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
# ======================================================================
main = get_main(__name__)
