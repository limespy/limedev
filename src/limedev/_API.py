"""Package API."""
import pathlib
import sys
from collections.abc import Sequence

from . import CLI
from ._aux import PATH_CONFIGS
from ._aux import PATH_REPO
# ======================================================================
def install(path_repo: str | pathlib.Path = PATH_REPO, version: str = '3.12'
            ) -> int:
    """Copies configurations from the defaults."""
    import shutil
    import subprocess

    # test configs
    for path_source in (PATH_CONFIGS / version).rglob('*'):
        if path_source.is_file():
            shutil.copyfile(path_source,
                            path_repo / path_source.relative_to(PATH_CONFIGS))

    subprocess.run(['pre-commit', 'install'])
    return 0
# ======================================================================
def main(args: Sequence[str] = sys.argv[1:]) -> int: # pylint: disable=dangerous-default-value
    """Main command line entry point."""
    return CLI.function_cli(args, module = __name__)
