"""Package API."""
import pathlib

from ._aux import import_from_path  # noqa: F401
from ._aux import PATH_DEFAULT_CONFIGS
from ._aux import PATH_PROJECT
# ======================================================================
def install(path_repo: str | pathlib.Path = PATH_PROJECT, version: str = '3.12'
            ) -> int:
    """Copies configurations from the defaults."""
    import shutil
    import subprocess

    # test configs
    for path_source in (PATH_DEFAULT_CONFIGS / version).rglob('*'):
        if path_source.is_file():
            shutil.copyfile(path_source,
                            path_repo / path_source.relative_to(PATH_DEFAULT_CONFIGS))

    subprocess.run(['pre-commit', 'install'])
    return 0
