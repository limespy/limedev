"""Test invokers."""
#%%=====================================================================
# IMPORT
import pathlib
from collections.abc import Callable
from typing import Any
from typing import TypeAlias

import yaml

from ._aux import import_from_path
from ._aux import PATH_CONFIGS
from ._aux import upsearch
from .CLI import get_main
#%%=====================================================================
if (_PATH_TESTS := upsearch('tests')) is None:
    PATH_TESTS = pathlib.Path.cwd()
else:
    PATH_TESTS = _PATH_TESTS

YAMLSafe = int | float | list['YAMLSafe'] | dict[str, 'YAMLSafe']
BenchmarkResultsType: TypeAlias = tuple[str, YAMLSafe]
#%%=====================================================================
def _get_path_config(pattern: str, path_start: pathlib.Path = PATH_TESTS
                     ) -> pathlib.Path:
    """Loads test configuration file paths or supplies default if not found."""
    return (PATH_CONFIGS / pattern
            if (path_local := upsearch(pattern, path_start)) is None
            else path_local)
# ======================================================================
def _pack_kwargs(kwargs: dict[str, str]) -> list[str]:

    return [f"--{key}{'=' if value else ''}{value}"
            for key, value in kwargs.items()]
# ======================================================================
def unittests(path_unittests: pathlib.Path = PATH_TESTS / 'unittests',
              cov: bool = False,
              **kwargs: str
              ) -> int:
    """Starts pytest unit tests."""
    import pytest

    if cov and 'cov-report' not in kwargs:
        kwargs['cov-report'] = f"html:{path_unittests/'htmlcov'}"

    pytest.main([str(path_unittests)] + _pack_kwargs(kwargs))
    return 0
# ======================================================================
def typing(path_src: pathlib.Path = PATH_TESTS.parent / 'src',
           config_file: str = str(_get_path_config('mypy.ini')),
           **kwargs: str
           ) -> int:
    """Starts mypy static type tests."""
    if 'config-file' not in kwargs:
        kwargs['config-file'] = config_file

    from mypy.main import main as mypy

    mypy(args = [str(path_src)] + _pack_kwargs(kwargs))
    return 0
# ======================================================================
def linting(path_source: pathlib.Path  = PATH_TESTS.parent / 'src',
            path_config: str = str(_get_path_config('.pylintrc')),
            **kwargs: str
            ) -> int:
    """Starts pylin linter."""
    from pylint import lint

    kwargs = {'rcfile': path_config,
              'output-format': 'colorized',
              'msg-template': '"{path}:{line}:{column}:{msg_id}:{symbol}\n'
                              '    {msg}"'} | kwargs

    lint.Run([str(path_source)] + _pack_kwargs(kwargs))
    return 0
# ======================================================================
def _run_profiling(function: Callable[[], Any],
                   path_pstats: pathlib.Path,
                   path_dot: pathlib.Path,
                   path_pdf: pathlib.Path,
                   is_warmup: bool,
                   ignore_missing_dot: bool,
                   gprof2dot_args: list[str]
                   ) -> None:
    import cProfile
    import gprof2dot
    import subprocess
    if is_warmup: # Prep to eliminate first run overhead
        function()

    with cProfile.Profile() as profiler:
        function()
    profiler.dump_stats(path_pstats)

    gprof2dot.main(gprof2dot_args)
    path_pstats.unlink()
    try:
        subprocess.run(['dot', '-Tpdf', str(path_dot), '-o', str(path_pdf)])
    except FileNotFoundError as exc:
        if ignore_missing_dot:
            return None
        raise RuntimeError('Conversion to PDF failed, maybe graphviz dot'
                        ' program is not installed.'
                        ' See http://www.graphviz.org/download/') from exc
    finally:
        path_dot.unlink()
    return None
# ----------------------------------------------------------------------
def profiling(path_profiling: pathlib.Path = PATH_TESTS / 'profiling.py',
              function: str = '',
              no_warmup: str | bool | None = None,
              ignore_missing_dot: str | None = None,
              **kwargs: str) -> int:
    """Runs profiling and converts results into a PDF."""

    # parsing arguments

    is_warmup = no_warmup in (False, None)

    ignore_missing_dot = ignore_missing_dot in (True, '')

    path_profiles_folder = path_profiling.parent / 'profiles'
    functions = {name: attr for name, attr
                 in import_from_path(path_profiling).__dict__.items()
                 if not name.startswith('_') and callable(attr)}

    if not path_profiles_folder.exists():
        path_profiles_folder.mkdir()

    path_pstats = path_profiles_folder / '.pstats'
    path_dot = path_profiles_folder / '.dot'
    kwargs = {'format': 'pstats',
               'node-thres': '1',
               'output': str(path_dot)} | kwargs
    gprof2dot_args = [str(path_pstats)] + _pack_kwargs(kwargs)

    if function:
        print(f'Profiling {function}')
        _run_profiling(functions[function],
                       path_pstats,
                       path_dot,
                       path_profiles_folder / f'{function}.pdf',
                       is_warmup,
                       ignore_missing_dot,
                       gprof2dot_args)
        return 0

    for name, _function in functions.items():
        print(f'Profiling {name}')
        _run_profiling(_function,
                       path_pstats,
                       path_dot,
                       path_profiles_folder / f'{name}.pdf',
                       is_warmup,
                       ignore_missing_dot,
                       gprof2dot_args)
    return 0
# ======================================================================
def benchmarking(path_benchmarks: pathlib.Path = PATH_TESTS / 'benchmarking.py') -> int:
    """Runs performance tests and save results into YAML file."""

    version, results = import_from_path(path_benchmarks).main()

    path_performance_data = path_benchmarks.with_suffix('.yaml')

    if not path_performance_data.exists():
        path_performance_data.touch()

    with open(path_performance_data, encoding = 'utf8', mode = 'r+') as file:

        if (data := yaml.safe_load(file)) is None:
            data = {}

        file.seek(0)
        data[version] = results
        yaml.safe_dump(data, file,
                       sort_keys = False, default_flow_style = False)
        file.truncate()
    return 0
# ======================================================================
main = get_main(__name__)
# ----------------------------------------------------------------------
if __name__ == '__main__':
    raise SystemExit(main())
