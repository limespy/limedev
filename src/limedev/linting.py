from pathlib import Path

from ._aux import _get_path_config
from ._aux import _pack_kwargs
# ======================================================================
def main(*paths: Path,
         config: Path | None = _get_path_config('ruff.toml'),
         **kwargs: str
            ) -> int:
    """Runs linter."""

    import os
    import sys
    from ruff.__main__ import find_ruff_bin

    if config:
        kwargs = {'config': str(config) } | kwargs

    ruff = os.fsdecode(find_ruff_bin())

    args = (ruff, 'check',
            *(str(path) for path in paths),
            *_pack_kwargs(kwargs))

    print('Linting', *paths)

    if sys.platform == 'win32':
        from subprocess import run
        return run(args).returncode
    else:
        os.execvp(ruff, args)
