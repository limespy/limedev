"""Test invokers."""
#%%=====================================================================
# IMPORT
import pathlib
import sys
from typing import Any
from typing import Callable

import yaml # type: ignore

from ._aux import _import_from_path
from ._aux import _upsearch

PATH_BASE = pathlib.Path(__file__).parent
PATH_CONFIGS = PATH_BASE / 'configs'
TEST_FOLDER_NAME = 'tests'
BENCHMARKING_NAME = 'benchmarking'
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
    positional = []
    if args:
        for arg in args:
            if arg.startswith('--'):
                key, _, value = arg[2:].partition('=')
                keyword[key] = value
            else:
                positional.append(arg)
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
            path_report = path_unittests / 'htmlcov'
            options = _parse_options(args, {'cov-report': f'html:"{path_report}"'})
            break
    else:
        options = args

    pytest.main([str(path_unittests)] + options)
    return 0
#==============================================================================
def typing(path_tests: pathlib.Path, args: list[str]) -> int:
    """Starts mypy typing tests."""
    options = {'config-file': _get_path_config(('mypy.ini',), path_tests)}

    from mypy.main import main as mypy # pylint: disable=import-outside-toplevel

    mypy(args = [str(path_tests.parent / 'src')] + _parse_options(args, options))
    return 0
#==============================================================================
def linting(path_tests: pathlib.Path, args: list[str]) -> int:
    """Starts pylin linter."""
    from pylint import lint # type: ignore # pylint: disable=import-outside-toplevel
    options = {'rcfile': str(_get_path_config(('.pylintrc',), path_tests)),
               'output-format': 'colorized',
               'msg-template': '"{path}:{line}:{column}:{msg_id}:{symbol}\n'
                                  '    {msg}"'}
    lint.Run([str(path_tests.parent / 'src')] + _parse_options(args, options))
    return 0
#=======================================================================
def profiling(path_tests: pathlib.Path, args: list[str]) -> int:
    """Runs profiling and converts results into a PDF."""
    import cProfile # pylint: disable=import-outside-toplevel
    import gprof2dot # type: ignore # pylint: disable=import-outside-toplevel
    import subprocess # pylint: disable=import-outside-toplevel

    path_profiling = path_tests / 'profiling.py'
    path_profiles_folder = path_tests / 'profiles'

    profile_module = _import_from_path(path_profiling)

    functions = [(name, attr) for name, attr in profile_module.__dict__.items()
                 if not name.startswith('_') and callable(attr)]
    # options = _parse_options(args, {'cpu': '',
    #                                 'memory': '',
    #                                 'reduced-profile': '',
    #                                 'module-path': f'"{path_profiling}"'})
    is_warmup = True
    for i, arg in enumerate(args):
        if arg == '--no-warmup':
            args.pop(i)
            is_warmup = False
            break

    for name, function in functions:
        print(f'Profiling "{name}"')
        # subprocess.run(['scalene', str(PATH_BASE / '_profiling.py'), f'--function={name}'] + options)

        if not path_profiles_folder.exists():
            path_profiles_folder.mkdir()

        path_profile = path_profiles_folder / name
        path_pstats = path_profile.with_suffix('.pstats')
        path_dot = path_profile.with_suffix('.dot')
        path_pdf = path_profile.with_suffix('.pdf')

        if is_warmup: # Prep to eliminate first run overhead
            function()

        with cProfile.Profile() as pr:
            function()

        pr.dump_stats(path_pstats)

        options = {'format': 'pstats',
                   'node-thres': '1',
                   'output': path_dot}

        gprof2dot.main([str(path_pstats)] + _parse_options(args, options))
        path_pstats.unlink()
        try:
            subprocess.run(['dot', '-Tpdf', str(path_dot), '-o', str(path_pdf)])
        except FileNotFoundError as exc:
            raise RuntimeError('Conversion to PDF failed, maybe graphviz dot'
                            ' program is not installed.'
                            ' See http://www.graphviz.org/download/') from exc
        path_dot.unlink()
    return 0
#==============================================================================
def benchmarking(path_tests: pathlib.Path, args: list[str]) -> int:
    """Runs performance tests and save results into YAML file."""

    path_benchmarks = (pathlib.Path(args[0]) if args
                       else path_tests / f'{BENCHMARKING_NAME}.py')

    benchmark = _import_from_path(path_benchmarks).main
    path_performance_data = path_benchmarks.with_suffix('yaml')

    version, results = benchmark()

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
#==============================================================================
TESTS: dict[str, Callable] = {function.__name__: function # type: ignore
                              for function in
                              (linting,
                               unittests,
                               typing,
                               profiling,
                               benchmarking)}
def main(args: list[str] = sys.argv[1:]) -> int: # pylint: disable=dangerous-default-value
    """Command line interface entry point."""
    if (path_tests := _upsearch(TEST_FOLDER_NAME)) is None:
        raise FileNotFoundError('Tests not found')

    if not args:
        return 0

    name = args.pop(0)

    if (function := TESTS.get(name)) is None:
        return _import_from_path(path_tests / f'{name}.py').main(args)
    return function(path_tests, args)
#==============================================================================
if __name__ == '__main__':
    raise SystemExit(main())
