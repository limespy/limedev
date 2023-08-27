'''Test invokers'''
#%%=====================================================================
# IMPORT
import pathlib
import sys
from typing import Any
from typing import Callable

import yaml # type: ignore

from ._aux import _import_from_path
from ._aux import _upsearch

PATH_CONFIGS = pathlib.Path(__file__).parent / 'configs'
TEST_FOLDER_NAME = 'tests'
PERFORMANCE_NAME = 'performance'
#%%=====================================================================
# TEST CASES

#%%=====================================================================
def _get_path_config(patterns, path_start):
    '''Loads test configuration file paths or supplies default if not found'''
    return (PATH_CONFIGS / patterns[0]
            if (path_local := _upsearch(patterns, path_start)) is None
            else path_local)
# ======================================================================
def _parse_options(args: list[str], options: dict[str, Any]) -> list[str]:
    if args:
        while (arg := args.pop(0)).startswith('--'):
            key, symbol, value = arg.partition('=')
            options[key + symbol] = value
    return [f'{key}{value}' for key, value in options.items()]
# ======================================================================
def unittests(path_tests: pathlib.Path, args: list[str]) -> None:
    '''Starts pytest unit tests'''
    import pytest # pylint: disable=import-outside-toplevel
    if '--coverage' in args:
        args.pop(args.index('--coverage'))
        options = _parse_options(args, {'--cov': '',
                                        '--cov-report=': 'html:tests/unittests/htmlcov'})
    else:
        options = args

    pytest.main([str(path_tests / 'unittests')] + options)
#==============================================================================
def typing(path_tests: pathlib.Path, args: list[str]) -> None:
    '''Starts mypy typing tests'''
    options = {'--config-file=': _get_path_config(('mypy.ini',), path_tests)}

    from mypy.main import main as mypy # pylint: disable=import-outside-toplevel

    mypy(args = [str(path_tests.parent / 'src')] + _parse_options(args, options))
#==============================================================================
def lint(path_tests: pathlib.Path, args: list[str]) -> None:
    '''Starts pylin linter'''
    from pylint import lint as linter # type: ignore # pylint: disable=import-outside-toplevel
    options = {'--rcfile=': str(_get_path_config((".pylintrc",), path_tests)),
               '--output=': 'colorized',
               '--msg-template=': '"{path}:{line}:{column}:{msg_id}:{symbol}\n'
                                  '    {msg}"'}
    linter.Run([str(path_tests.parent / 'src')] + _parse_options(args, options))
#=======================================================================
def profiling(path_tests: pathlib.Path, args: list[str]) -> None:
    '''Runs profiling and converts results into a PDF'''
    import cProfile # pylint: disable=import-outside-toplevel
    import gprof2dot # type: ignore # pylint: disable=import-outside-toplevel
    import subprocess # pylint: disable=import-outside-toplevel

    profile_run = _import_from_path(path_tests / 'profiling.py').main

    path_profile = path_tests / 'profile'
    path_pstats = path_profile.with_suffix('.pstats')
    path_dot = path_profile.with_suffix('.dot')
    path_pdf = path_profile.with_suffix('.pdf')

    profile_run() # Prep to eliminate first run overhead
    with cProfile.Profile() as pr:
        profile_run()
    pr.dump_stats(path_pstats)

    options = {'--format=': 'pstats',
               '--node-thres=': '1',
               '--output=': path_dot}

    gprof2dot.main([str(path_pstats)] + _parse_options(args, options))
    path_pstats.unlink()
    try:
        subprocess.run(['dot', '-Tpdf', str(path_dot), '-o', str(path_pdf)])
    except FileNotFoundError as exc:
        raise RuntimeError('Conversion to PDF failed, maybe graphviz dot'
                           ' program is not installed.'
                           ' See http://www.graphviz.org/download/') from exc
    path_dot.unlink()
#==============================================================================
def performance(path_tests: pathlib.Path, args: list[str]) -> None:
    '''Runs performance tests and save sresults into YAML file'''
    performance_tests = _import_from_path(path_tests / f'{PERFORMANCE_NAME}.py').main
    path_performance_data = path_tests / f'{PERFORMANCE_NAME}.yaml'
    version, results = performance_tests()
    if not path_performance_data.exists():
        path_performance_data.touch()
    with open(path_performance_data, encoding = 'utf8', mode = 'r+') as f:
        if (data := yaml.safe_load(f)) is None:
            data = {}
        f.seek(0)
        data[version] = results
        yaml.safe_dump(data, f, sort_keys = False, default_flow_style = False)
        f.truncate()
#==============================================================================
TESTS: dict[str, Callable] = {function.__name__: function # type: ignore
                              for function in
                              (lint, unittests, typing, profiling, performance)}
def main(args: list[str] = sys.argv[1:]) -> int: # pylint: disable=dangerous-default-value
    '''Command line interface entry point'''
    if (path_tests := _upsearch(TEST_FOLDER_NAME)) is None:
        raise FileNotFoundError('Tests not found')

    if not args:
        return 0

    name = args[0]
    if (function := TESTS.get(name)) is None:
        _import_from_path(path_tests / f'{name}.py').main(args[1:])
    else:
        function(path_tests, args[1:])
    return 0
#==============================================================================
if __name__ == '__main__':
    raise SystemExit(main())
