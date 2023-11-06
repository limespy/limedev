"""Test invokers."""
#%%=====================================================================
# IMPORT
import pathlib
import sys
from collections.abc import Callable
from collections.abc import Sequence
from typing import Any
from typing import cast
from typing import TypeAlias

import yaml

from ._aux import _argumentparser
from ._aux import _import_from_path
from ._aux import _upsearch
from ._aux import PATH_CONFIGS
from .CLI import function_cli

PATH_TESTS = _upsearch('tests')
if PATH_TESTS is None:
    raise FileNotFoundError('Test folder not found')

PATH_TESTS = cast(pathlib.Path, PATH_TESTS) # type: ignore[redundant-cast]

YAMLSafe = int | float | list['YAMLSafe'] | dict[str, 'YAMLSafe']
BenchmarkResultsType: TypeAlias = tuple[str, YAMLSafe]
#%%=====================================================================
def _get_path_config(patterns: Sequence[str], path_start: pathlib.Path
                     ) -> pathlib.Path:
    """Loads test configuration file paths or supplies default if not found."""
    return (PATH_CONFIGS / patterns[0]
            if (path_local := _upsearch(patterns, path_start)) is None
            else path_local)
# ======================================================================
def _parse_options(args: Sequence[str], defaults: dict[str, Any]) -> list[str]:
    positional, keyword = _argumentparser(args)

    positional.extend((f'--{key}{"=" if value else ""}{value}'
                       for key, value in (defaults | keyword).items()))
    return positional
# ======================================================================
def unittests(*args: str, path_tests: pathlib.Path = PATH_TESTS) -> int:
    """Starts pytest unit tests."""
    import pytest

    path_unittests = path_tests / 'unittests'

    for arg in args:
        if arg.startswith('--cov'):
            options = _parse_options(args,
                                     {'cov-report': 'html:tests/unittests/htmlcov'})
            break
    else:
        options = list(args)

    pytest.main([str(path_unittests)] + options)
    return 0
# ======================================================================
def typing(*args: str, path_tests: pathlib.Path = PATH_TESTS) -> int:
    """Starts mypy typing tests."""
    options = {'config-file': _get_path_config(('mypy.ini',), path_tests)}

    from mypy.main import main as mypy

    mypy(args = [str(path_tests.parent / 'src')] + _parse_options(args, options))
    return 0
# ======================================================================
def linting(*args: str, path_tests: pathlib.Path = PATH_TESTS) -> int:
    """Starts pylin linter."""
    from pylint import lint
    options = {'rcfile': str(_get_path_config(('.pylintrc',), path_tests)),
               'output-format': 'colorized',
               'msg-template': '"{path}:{line}:{column}:{msg_id}:{symbol}\n'
                                  '    {msg}"'}
    lint.Run([str(path_tests.parent / 'src')] + _parse_options(args, options))
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
def profiling(*args: str,
              function: str = '',
              no_warmup: str | bool | None = None,
              ignore_missing_dot: str | None = None,
              path_tests: pathlib.Path = PATH_TESTS) -> int: # pylint: disable=too-many-locals
    """Runs profiling and converts results into a PDF."""

    # parsing arguments
    args = list(args)
    path_profiling = (pathlib.Path(args[0])
                      if args and not args[0].startswith('--')
                      else path_tests / 'profiling.py')

    is_warmup = no_warmup in (False, None)

    ignore_missing_dot = ignore_missing_dot in (True, '')

    path_profiles_folder = path_profiling.parent / 'profiles'
    functions = {name: attr for name, attr
                 in _import_from_path(path_profiling).__dict__.items()
                 if not name.startswith('_') and callable(attr)}

    if not path_profiles_folder.exists():
        path_profiles_folder.mkdir()

    path_pstats = path_profiles_folder / '.pstats'
    path_dot = path_profiles_folder / '.dot'

    gprof2dot_args = [str(path_pstats)] + _parse_options(args,
                                                         {'format': 'pstats',
                                                          'node-thres': '1',
                                                          'output': path_dot})

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
#==============================================================================
def benchmarking(*args: str, path_tests: pathlib.Path = PATH_TESTS) -> int:
    """Runs performance tests and save results into YAML file."""

    path_benchmarks = (pathlib.Path(args[0]) if args
                       else path_tests / 'benchmarking.py')

    benchmark = _import_from_path(path_benchmarks).main

    version, results = benchmark()

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
def main(args: Sequence[str] = sys.argv[1:]) -> int: # pylint: disable=dangerous-default-value
    """Main command line entry point."""
    return function_cli(args, module = __name__)
# ----------------------------------------------------------------------
if __name__ == '__main__':
    raise SystemExit(main())
