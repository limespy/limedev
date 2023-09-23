"""Trying to get scalene workinbg programmatically is such a mess."""
import pathlib
import sys
from typing import Iterable

from _aux import _import_from_path
from scalene.scalene_profiler import Scalene

def main(args: Iterable[str] = sys.argv[1:]) -> int:
    is_warmup = True
    for arg in args:
        if arg.startswith('--function='):
            name = arg[11:]
        elif arg.startswith('--module-path='):
            path_module = pathlib.Path(arg[15:-1])
        elif arg == '--no-warmup':
            is_warmup = False

    module = _import_from_path(path_module)
    function = getattr(module, name)

    if is_warmup:
        function()

    @Scalene.profile
    def wrapper():
        function()

    wrapper()

    return 0

if __name__ == '__main__':
    raise SystemExit(main())
