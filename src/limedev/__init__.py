"""Tools for testing, building readme and packaging."""
from typing import TYPE_CHECKING

from ._api import * # noqa: F403

if TYPE_CHECKING:
    from types import ModuleType
    from typing import cast

    from . import benchmarking as benchmarking
    from . import cli as cli
    from . import linting as linting
    from . import package as package
    from . import profiling as profiling
    from . import readme as readme
    from . import typing as typing
    from . import unittesting as unittesting

    __version__ = ''

    __package__ = cast(str, __package__) #type: ignore[redundant-cast]
else:
    ModuleType = object
# ======================================================================
def __getattr__(name: str) -> str | ModuleType:
    if name == '__version__':
        from importlib import metadata
        return metadata.version(__package__)

    if name in {'benchmarking',
                'cli',
                'linting',
                'package',
                'profiling',
                'readme',
                'typing',
                'unittesting'}:
        from importlib import import_module
        from sys import modules

        module = import_module(f'.{name}', __package__)
        setattr(modules[__package__], name, module)
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
