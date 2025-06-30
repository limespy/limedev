from enum import auto
from enum import StrEnum
from pathlib import Path

from ._aux import _get_default_config
from ._aux import _get_path_config
from ._aux import _in_pyproject
from ._aux import _pack_kwargs
from ._aux import PATH_PROJECT
from ._aux import PATH_SRC
# ======================================================================
class TypingBackend(StrEnum):
    MYPY = auto()
    PYREFLY = auto()
    TY = auto()

MYPY, PYREFLY, TY = TypingBackend

PATH_PYPROJECT = PATH_PROJECT / 'pyproject.toml'
# ======================================================================
_typecheck_config_map = {MYPY: 'mypy.ini',
                      PYREFLY: 'pyrefly.toml',
                      TY: 'ty.toml'}
# ----------------------------------------------------------------------
def _typecheck_mypy(path_src: Path,
                 config_file: Path | None,
                 kwargs: dict[str, str]) -> int:
    from mypy.main import main as mypy

    try:
        mypy(args = [str(path_src),
                     *((f'--config-file={config_file}',) if config_file else ()),
                     *_pack_kwargs(kwargs)], clean_exit = True)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        if isinstance(exc.code, str):
            from sys import stderr
            print(exc.code, file = stderr)
            return 1
    return 0
# ----------------------------------------------------------------------
def _typecheck_pyrefly(path_src: Path,
                    config_file: Path | None,
                    kwargs: dict[str, str]) -> int:
    from subprocess import run
    try:
        return run(('pyrefly', 'check', str(path_src),
             *((f'--config-file={config_file}',) if config_file else ()),
             *_pack_kwargs(kwargs))).returncode
    except FileNotFoundError:
        pass
    return 1
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _typecheck_ty(path_src: Path,
               config_file: Path | None,
               kwargs: dict[str, str]) -> int:
    from subprocess import run
    try:
        return run(('ty', 'check', str(path_src),
             *((f'--config-file={config_file}',) if config_file else ()),
             *_pack_kwargs(kwargs))).returncode
    except FileNotFoundError:
        pass
    return 1
# ----------------------------------------------------------------------
def main(path_src: Path = PATH_SRC,
           config_file: Path | None = None,
           backend: TypingBackend = MYPY,
           **kwargs: str
           ) -> int:
    """Starts mypy static type tests."""
    if not config_file and (_config_file := kwargs.get('config-file')):
        config_file = Path(_config_file)

    try:
        config_file_name = _typecheck_config_map[backend]
    except KeyError as exc:
        _backends = ', '.join((f'"{_backend}"' for _backend in TypingBackend))
        raise ValueError(
                f"Backend '{backend}' is not supported. "
                f"Supported are {_backends}"
                    ) from exc
    if config_file is None:
        if (config_file := _get_path_config(config_file_name)) is None:
            config_file = (PATH_PYPROJECT if _in_pyproject(backend.lower())
                           else _get_default_config(config_file_name))
    try:
        if backend == MYPY:
            return _typecheck_mypy(path_src, config_file, kwargs)
        elif backend == PYREFLY:
            return _typecheck_pyrefly(path_src, config_file, kwargs)
        elif backend == TY:
            return _typecheck_ty(path_src, config_file, kwargs)
        else:
            _backends = ', '.join((f'"{_backend}"'
                                   for _backend in TypingBackend))
            raise ValueError(
                f"Backend '{backend}' is not supported. "
                f"Supported are {_backends}")
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            f"Backend '{backend}' not found. "
            f"Install optional dependency 'limespy[test-typing-{backend}]' "
            "or all backends 'limespy[test-typing]'",
                                  name = exc.name, path = exc.path)
