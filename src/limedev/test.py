"""Test invokers."""
#%%=====================================================================
# IMPORT
import timeit
from math import floor
from math import log10
from pathlib import Path
from typing import ParamSpec
from typing import TYPE_CHECKING

import yaml

from ._aux import import_from_path
from ._aux import PATH_CONFIGS
from ._aux import upsearch
from ._aux import YAMLSafe
from .CLI import get_main
# ======================================================================
# Hinting types
P = ParamSpec('P')

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Generator
    from typing import TypeAlias
    from typing import TypeVar

    T = TypeVar('T')
    BenchmarkResultsType: TypeAlias = tuple[str, YAMLSafe]
else:
    Callable = Generator = tuple
    T = BenchmarkResultsType = object
#%%=====================================================================
if (_PATH_TESTS := upsearch('tests')) is None:
    PATH_TESTS = PATH_SRC = Path.cwd()
else:
    PATH_TESTS = _PATH_TESTS
    PATH_SRC = _PATH_TESTS.parent / 'src'
    if not PATH_SRC.exists():
        PATH_SRC = PATH_SRC.parent
#%%=====================================================================
def _get_path_config(pattern: str, path_start: Path = PATH_TESTS
                     ) -> Path:
    """Loads test configuration file paths or supplies default if not found."""
    return (PATH_CONFIGS / pattern
            if (path_local := upsearch(pattern, path_start)) is None
            else path_local)
# ======================================================================
def _pack_kwargs(kwargs: dict[str, str]) -> Generator[str, None, None]:

    return (f"--{key}{'=' if value else ''}{value}"
            for key, value in kwargs.items())
# ======================================================================
def unittests(path_unittests: Path = PATH_TESTS / 'unittests',
              cov: bool = False,
              **kwargs: str
              ) -> int:
    """Starts pytest unit tests."""
    import pytest
    if cov and 'cov-report' not in kwargs:
        kwargs['cov-report'] = f"html:{path_unittests/'htmlcov'}"

    pytest.main([str(path_unittests), *_pack_kwargs(kwargs)])
    return 0
# ======================================================================
def typing(path_src: Path = PATH_SRC,
           config_file: str = str(_get_path_config('mypy.ini')),
           **kwargs: str
           ) -> int:
    """Starts mypy static type tests."""
    if 'config-file' not in kwargs:
        kwargs['config-file'] = config_file

    from mypy.main import main as mypy


    mypy(args = [str(path_src), *_pack_kwargs(kwargs)])
    return 0
# ======================================================================
def linting(path_source: Path = PATH_SRC,
            *,
            config: str = str(_get_path_config('ruff.toml')),
            **kwargs: str
            ) -> int:
    """Starts pylin linter."""

    import os
    import sys
    from ruff.__main__ import find_ruff_bin

    print(config)

    kwargs = {'config': config} | kwargs

    ruff = os.fsdecode(find_ruff_bin())
    path_source_str = str(path_source)

    args = (ruff, 'check', path_source_str, *_pack_kwargs(kwargs))

    print(f'Linting {path_source_str}')

    if sys.platform == 'win32':
        import subprocess

        completed_process = subprocess.run(args)
        return completed_process.returncode
    else:
        os.execvp(ruff, args)
        return 0
# ======================================================================
def profiling(path_profiling: Path = PATH_TESTS / 'profiling.py',
              out: Path | None = None,
              function: str = '',
              no_warmup: bool = False,
              ignore_missing_dot: bool = False,
              **kwargs: str) -> int:
    """Runs profiling and converts results into a PDF."""

    # parsing arguments
    from cProfile import Profile
    import gprof2dot
    import subprocess

    is_warmup = not no_warmup
    if out is None:
        out = path_profiling.parent / '.profiles'

    out.mkdir(exist_ok = True, parents = True)

    user_functions = import_from_path(path_profiling).__dict__

    if function: # Selecting only one
        functions = {function: user_functions[function]}
    else:
        functions = {name: attr for name, attr
                     in user_functions.items()
                     if not name.startswith('_') and callable(attr)}


    path_pstats = out / '.pstats'
    path_dot = out / '.dot'
    kwargs = {'format': 'pstats',
               'node-thres': '1',
               'output': str(path_dot)} | kwargs
    gprof2dot_args = [str(path_pstats), *_pack_kwargs(kwargs)]


    for name, _function in functions.items():
        print(f'Profiling {name}')

        if is_warmup: # Prep to eliminate first run overhead
            _function()

        with Profile() as profiler:
            _function()

        profiler.dump_stats(path_pstats)

        gprof2dot.main(gprof2dot_args)

        path_pstats.unlink()
        path_pdf = out / (name + '.pdf')
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
def _run_best_of(call: str, setup: str,
                 _globals: dict, number: int, samples: int) -> float:
    return min(timeit.timeit(call, setup, globals = _globals, number = number)
               for _ in range(samples))
# ----------------------------------------------------------------------
def run_timed(function: Callable[P, T],
              t_min_s: float = 0.1, min_calls: int = 1, n_samples: int = 5
              ) -> Callable[P, float]:
    """Self-adjusting timing, best-of -timing.

    One call in setup.
    """
    def timer(*args: P.args, **kwargs: P.kwargs) -> float:
        _globals = {'function': function,
                    'args': args,
                    'kwargs': kwargs}
        n = min_calls
        _n_samples = n_samples
        _t_min_s = t_min_s
        args_expanded = ''.join(f'a{n}, ' for n in range(len(args)))
        kwargs_expanded = ', '.join(f'{k} = {k}' for k in kwargs)
        call = f'function({args_expanded}{kwargs_expanded})'

        args_setup = f'{args_expanded} = args\n'
        kwargs_setup = '\n'.join((f'{k} = kwargs["{k}"]' for k in kwargs))
        setup = f'{args_setup if args else ""}\n{kwargs_setup}\n' + call

        while (t := _run_best_of(call, setup, _globals, n, _n_samples)
               ) < _t_min_s:
            n *= 2 * round(_t_min_s / t)
        return  t / float(n)
    return timer
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
    if value == 0.:
        return value
    return round(value, max(0, n_sigfig - floor(log10(abs(value))) - 1))
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
def benchmarking(path_benchmarks: Path = PATH_TESTS / 'benchmarking.py',
                 out: Path | None = None,
                 **kwargs: str) -> int:
    """Runs performance tests and save results into YAML file."""

    version, results = import_from_path(path_benchmarks).main(**kwargs)

    if out is None:
        out = path_benchmarks.parent / f'.{path_benchmarks.stem}.yaml'

    if not out.exists():
        out.touch()

    with open(out, encoding = 'utf8', mode = 'r+') as file:

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
