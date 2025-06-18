"""Test invokers."""
#%%=====================================================================
# IMPORT
from enum import Enum
from math import floor
from math import log10
from pathlib import Path
from timeit import timeit
from typing import ParamSpec
from typing import TYPE_CHECKING

from ._aux import import_from_path
from ._aux import PATH_DEFAULT_CONFIGS
from ._aux import PATH_PROJECT
from ._aux import upsearch
from ._aux import YAMLSafe
from .cli import get_main

from sys import version_info

# ======================================================================
# Hinting types
P = ParamSpec('P')

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Generator
    from collections.abc import Iterable
    from typing import TypeAlias
    from typing import TypeVar

    T = TypeVar('T')
    BenchmarkResultsType: TypeAlias = tuple[str, YAMLSafe]
else:
    Callable = Generator = Iterable = tuple
    T = BenchmarkResultsType = object
#%%=====================================================================
def _try_get_path(path_project: Path, patterns: Iterable[str]
                  ) -> Path | None:
    for pattern in patterns:
        try:
            if (path_src := next(path_project.glob(pattern))).is_dir():
                return path_src
        except StopIteration:
            pass
    return None
# ----------------------------------------------------------------------
PATH_TESTS = _try_get_path(PATH_PROJECT, ('tests', 'test'))
PATH_SRC = _try_get_path(PATH_PROJECT, ('src', 'source')) or PATH_PROJECT
PATH_VERSION_DEFAULTS = (PATH_DEFAULT_CONFIGS
                         / f'{version_info[0]}.{version_info[1]}')
PATH_FALLBACK_DEFAULTS = (PATH_DEFAULT_CONFIGS / 'fallback')
#%%=====================================================================
def _get_default_config(patterns) -> Path | None:
    return (path if (path := upsearch(patterns,
                                      path_search = PATH_VERSION_DEFAULTS,
                                      path_stop = PATH_VERSION_DEFAULTS))
            else upsearch(patterns,
                          path_search = PATH_FALLBACK_DEFAULTS,
                          path_stop = PATH_FALLBACK_DEFAULTS))
#%%=====================================================================
def _get_path_config(patterns: str | Iterable[str],
                     path_start: Path | None = PATH_TESTS
                     ) -> Path | None:
    """Loads test configuration file paths or supplies.

    default if not found.
    """
    if path_start:
        if _path_config := upsearch(patterns, path_start,
                                    path_stop = PATH_PROJECT):
            return _path_config
    return _get_default_config(patterns)
# ======================================================================
def _pack_kwargs(kwargs: dict[str, str]) -> Generator[str, None, None]:

    return (f"--{key}{'=' if value else ''}{value}"
            for key, value in kwargs.items())
# ======================================================================
def unittests(path_unittests: Path | None = None,
              cov: bool = False,
              tests: str = '',
              **kwargs: str
              ) -> int:
    """Starts pytest unit tests."""
    import pytest

    if path_unittests is None:
        if PATH_TESTS is None:
            path_unittests = PATH_PROJECT
        elif not (path_unittests := PATH_TESTS / 'unittests').exists():
            path_unittests = PATH_TESTS

    if cov and ('cov-report' not in kwargs):
        kwargs['cov-report'] = f"html:{path_unittests/'htmlcov'}"

    if (config_file_arg := kwargs.get('config-file')) is None:
        # Trying to find and insert a config file
        try:
            # Looking recursively under unittest forlder
            kwargs['config-file'] = str(next(path_unittests.rglob('pytest.ini')))
        except StopIteration:
            path_config = upsearch('pytest.ini',
                                   path_unittests,
                                   path_stop = PATH_PROJECT)
            if path_config is None:

                if (path_config := upsearch('pyproject.toml',
                                               path_unittests,
                                               path_stop = PATH_PROJECT)
                    ) is not None:
                    if path_config.read_text().find('[tool.pytest.ini_options]') == -1:
                        # Configuration not found
                        path_config = upsearch('pytest.ini',
                                               PATH_DEFAULT_CONFIGS)

            if path_config is not None:
                kwargs['config-file'] = str(path_config)

    elif config_file_arg == '':
        kwargs.pop('config-file')
    if (status := pytest.main([str(path_unittests), '-k', tests,
                                 *_pack_kwargs(kwargs)])) == 0:
        return status
    raise Exception(f'Exit status {status}')
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
def linting(path_source: Path | None = PATH_SRC,
            *,
            config: Path | None = _get_path_config('ruff.toml'),
            **kwargs: str
            ) -> int:
    """Starts pylin linter."""

    import os
    import sys
    from ruff.__main__ import find_ruff_bin

    if config:
        kwargs = {'config': str(config) } | kwargs

    ruff = os.fsdecode(find_ruff_bin())
    path_source_str = str(path_source)

    args = (ruff, 'check', path_source_str, *_pack_kwargs(kwargs))

    print(f'Linting {path_source_str}')

    if sys.platform == 'win32':
        from subprocess import run
        return run(args).returncode
    else:
        os.execvp(ruff, args)
        return 0
# ======================================================================
class MissingDot(Enum):
    ERROR = 0
    WARN = 1
    IGNORE = 2
# ----------------------------------------------------------------------
def profiling(path_profiling: Path | None = None,
              out: Path | None = None,
              function: str = '',
              no_warmup: bool = False,
              missing_dot: MissingDot = MissingDot.ERROR,
              **kwargs: str) -> int:
    """Runs profiling and converts results into a PDF."""

    # parsing arguments
    from cProfile import Profile
    from subprocess import run
    from time import perf_counter

    import gprof2dot

    if path_profiling is None:
        path_profiling = (PATH_PROJECT / 'profiling.py' if PATH_TESTS is None
                          else PATH_TESTS / 'profiling.py')

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
               'node-thres': '1', # 1 percent threshold
               'output': str(path_dot)} | kwargs
    gprof2dot_args = [str(path_pstats), *_pack_kwargs(kwargs)]


    for name, _function in functions.items():
        print(f'Profiling {name}')
        if not no_warmup: # Prep to eliminate first run overhead
            t0 = perf_counter()
            _function()
            value, prefix = eng_round(perf_counter() - t0)
            print(f'Warmup time {value:3.1f} {prefix}s')

        t0 = perf_counter()
        with Profile() as profiler:
            _function()

        value, prefix = eng_round(perf_counter() - t0)
        print(f'Profiling time {value:3.1f} {prefix}s')

        profiler.dump_stats(path_pstats)

        gprof2dot.main(gprof2dot_args)

        path_pstats.unlink()
        path_pdf = out / (name + '.pdf')
        try:
            run(('dot', '-Tpdf', str(path_dot), '-o', str(path_pdf)))
        except FileNotFoundError as exc:
            if missing_dot is MissingDot.IGNORE:
                return 0
            message = ('Conversion to PDF failed, maybe Graphviz dot'
                       ' program is not installed.'
                       ' See http://www.graphviz.org/download/')
            if missing_dot is MissingDot.WARN:
                from warnings import warn
                warn(message, RuntimeWarning, stacklevel = 2)
                return 0
            raise RuntimeError(message) from exc
        finally:
            path_dot.unlink()
    return 0
# ======================================================================
def _run_best_of(call: str, setup: str,
                 _globals: dict, number: int, samples: int) -> float:
    return min(timeit(call, setup, globals = _globals, number = number)
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
    """Engineering rounding.

    Shifts to nearest SI prefix fraction and rounds to given significant digits.
    """
    prefix_symbol_previous, prefix_value_previous = _prefixes_items[0]
    for prefix_symbol, prefix_value in _prefixes_items[1:]:
        if value < prefix_value:
            break
        prefix_symbol_previous = prefix_symbol
        prefix_value_previous = prefix_value
    return (sigfig_round(value / prefix_value_previous, n_sigfig),
            prefix_symbol_previous)
# ----------------------------------------------------------------------
def benchmarking(path_benchmarks: Path | None = None,
                 out: Path | None = None,
                 **kwargs: str) -> int:
    """Runs performance tests and save results into YAML.

    file.
    """
    from sys import platform
    import yaml

    if path_benchmarks is None:
        if PATH_TESTS is None:
            raise ValueError('Benchmark path not provided '
                             'and test path not found')
        else:
            path_benchmarks = PATH_TESTS / 'benchmarking.py'

    # Setting process to realtime
    try:
        if platform == 'win32':
            # Based on:
            #   "Recipe 496767: Set Process Priority In Windows" on ActiveState
            #   http://code.activestate.com/recipes/496767/
            try:
                import win32api
                import win32process
                from win32con import PROCESS_ALL_ACCESS
            except ModuleNotFoundError:
                from warnings import warn
                warn('pywin32 is not installed. '
                     'Maybe due to incompatible Python version',
                     ImportWarning, stacklevel = 2)
            else:
                pid = win32api.GetCurrentProcessId()
                handle = win32api.OpenProcess(PROCESS_ALL_ACCESS, True, pid)
                win32process.SetPriorityClass(handle,
                                            win32process.REALTIME_PRIORITY_CLASS)

        elif platform == 'linux':
            import os
            os.nice(-20 - os.nice(0)) # type: ignore[attr-defined]
    except PermissionError as error:
        if error.errno == 1:
            from warnings import warn
            warn('Raising the process priority not permitted',
                 RuntimeWarning, stacklevel = 2)
        else:
            raise
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
