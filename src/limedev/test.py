"""Test invokers."""
#%%=====================================================================
# IMPORT
import pathlib
import sys
from typing import Any
from typing import Callable

import yaml

from ._aux import _argumentparser
from ._aux import _import_from_path
from ._aux import _upsearch
from ._aux import PATH_CONFIGS

TEST_FOLDER_NAME = 'tests'
BenchmarkResultsType = tuple[str, dict[str, int | float | list | dict]]
#%%=====================================================================
# TEST CASES

#%%=====================================================================
def _get_path_config(patterns, path_start):
    """Loads test configuration file paths or supplies default if not found."""
    return (PATH_CONFIGS / patterns[0]
            if (path_local := _upsearch(patterns, path_start)) is None
            else path_local)
# ======================================================================
def _parse_options(args: list[str], keyword: dict[str, Any]) -> list[str]:
    positional, keyword = _argumentparser(args)

    positional.extend((f'--{key}{"=" if value else ""}{value}'
                       for key, value in keyword.items()))
    return positional
# ======================================================================
def unittests(path_tests: pathlib.Path, args: list[str]) -> int:
    """Starts pytest unit tests."""
    import pytest # pylint: disable=import-outside-toplevel

    path_unittests = path_tests / 'unittests'

    for arg in args:
        if arg.startswith('--cov'):
            options = _parse_options(args,
                                     {'cov-report': 'html:tests/unittests/htmlcov'})
            break
    else:
        options = args

    pytest.main([str(path_unittests)] + options)
    return 0
# ======================================================================
def typing(path_tests: pathlib.Path, args: list[str]) -> int:
    """Starts mypy typing tests."""
    options = {'config-file': _get_path_config(('mypy.ini',), path_tests)}

    from mypy.main import main as mypy # pylint: disable=import-outside-toplevel disable=no-name-in-module

    mypy(args = [str(path_tests.parent / 'src')] + _parse_options(args, options))
    return 0
# ======================================================================
def linting(path_tests: pathlib.Path, args: list[str]) -> int:
    """Starts pylin linter."""
    from pylint import lint # pylint: disable=import-outside-toplevel
    options = {'rcfile': str(_get_path_config(('.pylintrc',), path_tests)),
               'output-format': 'colorized',
               'msg-template': '"{path}:{line}:{column}:{msg_id}:{symbol}\n'
                                  '    {msg}"'}
    lint.Run([str(path_tests.parent / 'src')] + _parse_options(args, options))
    return 0
# ======================================================================
def _run_profiling(function: Callable[[], Any],
                   path_pstats,
                   path_dot,
                   path_pdf,
                   is_warmup: bool,
                   cProfile,
                   gprof2dot,
                   gprof2dot_args: list[str],
                   subprocess) -> None:

    if is_warmup: # Prep to eliminate first run overhead
        function()

    with cProfile.Profile() as pr:
        function()
    pr.dump_stats(path_pstats)

    gprof2dot.main(gprof2dot_args)
    path_pstats.unlink()
    try:
        subprocess.run(['dot', '-Tpdf', str(path_dot), '-o', str(path_pdf)])
    except FileNotFoundError as exc:
        raise RuntimeError('Conversion to PDF failed, maybe graphviz dot'
                        ' program is not installed.'
                        ' See http://www.graphviz.org/download/') from exc
    path_dot.unlink()
# ----------------------------------------------------------------------
def profiling(path_tests: pathlib.Path, args: list[str]) -> int: # pylint: disable=too-many-locals
    """Runs profiling and converts results into a PDF."""
    import cProfile # pylint: disable=import-outside-toplevel
    import gprof2dot # pylint: disable=import-outside-toplevel
    import subprocess # pylint: disable=import-outside-toplevel
    # parsing arguments
    path_profiling = (pathlib.Path(args[0])
                      if args and not args[0].startswith('--')
                      else path_tests / 'profiling.py')

    is_warmup = True
    function_name = ''

    index = len(args)
    for arg in reversed(args):
        index -= 1
        if arg == '--no-warmup':
            args.pop(index)
            is_warmup = False
        elif arg.startswith('--function='):
            args.pop(index)
            function_name = arg[11:]

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

    if function_name:
        print(f'Profiling {function_name}')
        _run_profiling(functions[function_name],
                       path_pstats,
                       path_dot,
                       path_profiles_folder / f'{function_name}.pdf',
                       is_warmup,
                       cProfile,
                       gprof2dot,
                       gprof2dot_args,
                       subprocess)
        return 0

    for name, function in functions.items():
        print(f'Profiling {name}')
        _run_profiling(function,
                       path_pstats,
                       path_dot,
                       path_profiles_folder / f'{name}.pdf',
                       is_warmup,
                       cProfile,
                       gprof2dot,
                       gprof2dot_args,
                       subprocess)
    return 0
#==============================================================================
def benchmarking(path_tests: pathlib.Path, args: list[str]) -> int:
    """Runs performance tests and save results into YAML file."""

    path_benchmarks = (pathlib.Path(args[0]) if args
                       else path_tests / 'benchmarking.py')

    benchmark = _import_from_path(path_benchmarks).main

    version, results = benchmark()

    path_performance_data = path_benchmarks.with_suffix('.yaml')

    if not path_performance_data.exists():
        path_performance_data.touch()

    with open(path_performance_data, encoding = 'utf8', mode = 'r+') as f:

        if (data := yaml.safe_load(f)) is None:
            data = {}

        f.seek(0)
        data[version] = results
        yaml.safe_dump(data, f, sort_keys = False, default_flow_style = False)
        f.truncate()
    return 0
# ======================================================================
TESTS: dict[str, Callable] = {function.__name__: function
                              for function in
                              (linting,
                               unittests,
                               typing,
                               profiling,
                               benchmarking)}
# ----------------------------------------------------------------------
def main(args: list[str] = sys.argv[1:]) -> int: # pylint: disable=dangerous-default-value
    """Command line interface entry point."""

    path_tests = _upsearch(TEST_FOLDER_NAME)

    if not args:
        return 0

    name = args.pop(0)

    if (function := TESTS.get(name)) is None:
        if path_tests is None:
            raise FileNotFoundError('Test folder not found')
        return _import_from_path(path_tests / f'{name}.py').main(args)
    return function(path_tests, args)
# ----------------------------------------------------------------------
if __name__ == '__main__':
    raise SystemExit(main())
