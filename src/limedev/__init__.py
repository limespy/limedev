"""Tools for testing, building readme and packaging."""
from typing import TYPE_CHECKING

from ._api import * # noqa: F403

if TYPE_CHECKING:
    from types import ModuleType
    from . import cli as cli
    from . import package as package
else:
    ModuleType = object
# ======================================================================
def __getattr__(name: str) -> str | ModuleType:
    if name == '__version__':
        from importlib import metadata
        return metadata.version(__package__)

    if name in {'cli', 'package'}:
        from importlib import import_module
        from sys import modules as _modules

        module = import_module(f'.{name}', __package__)
        setattr(_modules[__package__], name, module)
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
