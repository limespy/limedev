import pathlib
import sys

from . import CLI
from ._aux import PATH_CONFIGS
from ._aux import PATH_REPO
# ======================================================================
def install(path_repo: str | pathlib.Path = pathlib.Path.cwd()) -> int:
    """Copies configurations from the defaults."""
    import shutil # pylint: disable=import-outside-toplevel
    import subprocess

    path_repo = PATH_REPO

    # test configs
    for path_source in PATH_CONFIGS.rglob('*'):
        if path_source.is_file():
            shutil.copyfile(path_source,
                            path_repo / path_source.relative_to(PATH_CONFIGS))

    subprocess.run(['pre-commit','install'])
    return 0
# ======================================================================
def main(args = sys.argv[1:]) -> int:
    return CLI.function_cli(args, module = __name__)
