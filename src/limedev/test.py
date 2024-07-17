"""Test invokers."""
#%%=====================================================================
# IMPORT
import pathlib
import timeit
from math import floor
from math import log10
from typing import TypeAlias

import yaml

from ._aux import import_from_path
from ._aux import PATH_CONFIGS
from ._aux import upsearch
from ._aux import YAMLSafe
from .CLI import get_main
#%%=====================================================================
if (_PATH_TESTS := upsearch('tests')) is None:
    PATH_TESTS = pathlib.Path.cwd()
else:
    PATH_TESTS = _PATH_TESTS

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
def profiling(path_profiling: pathlib.Path = PATH_TESTS / 'profiling.py',
              function: str = '',
              no_warmup: bool = False,
              ignore_missing_dot: bool = False,
              **kwargs: str) -> int:
    """Runs profiling and converts results into a PDF."""

    # parsing arguments
    import cProfile
    import gprof2dot
    import subprocess

    is_warmup = ~no_warmup

    path_profiles_folder = path_profiling.parent / 'profiles'

    user_functions = import_from_path(path_profiling).__dict__

    if function: # Selecting only one
        functions = {function: user_functions[function]}
    else:
        functions = {name: attr for name, attr
                     in user_functions.items()
                     if not name.startswith('_') and callable(attr)}

    path_profiles_folder.mkdir(parents = True, exist_ok = True)

    path_pstats = path_profiles_folder / '.pstats'
    path_dot = path_profiles_folder / '.dot'
    kwargs = {'format': 'pstats',
               'node-thres': '1',
               'output': str(path_dot)} | kwargs
    gprof2dot_args = [str(path_pstats)] + _pack_kwargs(kwargs)


    for name, _function in functions.items():
        print(f'Profiling {name}')

        if is_warmup: # Prep to eliminate first run overhead
            _function()

        with cProfile.Profile() as profiler:
            _function()
        profiler.dump_stats(path_pstats)

        gprof2dot.main(gprof2dot_args)

        path_pstats.unlink()
        path_pdf = path_profiles_folder / f'{name}.pdf'
        try:
            subprocess.run(['dot', '-Tpdf', str(path_dot), '-o', str(path_pdf)])
        except FileNotFoundError as exc:
            if ignore_missing_dot:
                return 0
            raise RuntimeError('Conversion to PDF failed, maybe graphviz dot'
                            ' program is not installed.'
                            ' See http://www.graphviz.org/download/') from exc
        finally:
            path_dot.unlink()
    return 0
# ======================================================================
def run_timed(function, /, *args, **kwargs):
    """Self-adjusting timing.

    Minimum two runs
    """
    _globals = {'function': function,
                'args': args,
                'kwargs': kwargs}
    t_min_s = 0.5
    n = 2
    args_expanded = ''.join(f'a{n}, ' for n in range(len(args)))
    kwargs_expanded = ', '.join(f'{k} = {k}' for k in kwargs)
    call = f'function({args_expanded}{kwargs_expanded})'

    args_setup = f'{args_expanded} = args\n'
    kwargs_setup = '\n'.join((f'{k} = kwargs["{k}"]' for k in kwargs))
    setup = f'{args_setup if args else ""}\n{kwargs_setup}\n' + call

    while (t := timeit.timeit(call, setup,
                              globals = _globals, number = n)) < t_min_s:
        n *= 2 * int(t_min_s / t)
    return  t / float(n)
# ----------------------------------------------------------------------
_prefixes_items = (('n', 1e-9),
                   ('u', 1e-6),
                   ('m', 1e-3),
                   ('',  1.),
                   ('k', 1e3),
                   ('M', 1e6))
prefixes = dict(_prefixes_items)
# ----------------------------------------------------------------------
def sigfig_round(value: float, n_sigfig: int) -> float:
    """Rounds to specified number of significant digits."""
    n_decimals = max(0, n_sigfig - floor(log10(value)) - 1)
    return round(value, n_decimals)
# ----------------------------------------------------------------------
def eng_round(value: float, n_sigfig: int = 3) -> tuple[float, str]:
    """Shifts to nearest SI prefix fraction and rounds to given number of
    significant digits."""
    prefix_symbol_previous, prefix_value_previous = _prefixes_items[0]
    for prefix_symbol, prefix_value in _prefixes_items[1:]:
        if value < prefix_value:
            break
        prefix_symbol_previous = prefix_symbol
        prefix_value_previous = prefix_value
    return (sigfig_round(value / prefix_value_previous, n_sigfig),
            prefix_symbol_previous)
# ----------------------------------------------------------------------
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
