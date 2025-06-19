from . import _api
from ..cli import get_main
# ======================================================================
_main = get_main(_api.__name__)
# ----------------------------------------------------------------------
def main(args: list[str] | None = None) -> int:
    print('hmm')
    if args is None:
        from sys import argv
        args = argv[1:]
    return _main(['package'] + args)
