from pathlib import Path
from timeit import timeit
from typing import ParamSpec
from typing import TYPE_CHECKING

from ._aux import import_from_path
from ._aux import PATH_TESTS
# ======================================================================
# Hinting types
P = ParamSpec('P')

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypeAlias
    from typing import TypeVar

    from ._aux import YAMLSafe

    T = TypeVar('T')
    BenchmarkResultsType: TypeAlias = tuple[str, YAMLSafe]
else:
    Callable = Generator = Iterable = tuple
    T = BenchmarkResultsType = object
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
def main(path_benchmarks: Path | None = None,
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
                import win32api # type: ignore[unresolved-inport,unused-ignore,import-untyped]
                import win32process # type: ignore[unresolved-inport,unused-ignore,import-untyped]
                from win32con import PROCESS_ALL_ACCESS # type: ignore[unresolved-inport,unused-ignore,import-untyped]
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
            os.nice(-20 - os.nice(0)) # type: ignore[attr-defined, unused-ignore]
    except PermissionError as error:
        if error.errno == 1:
            from warnings import warn
            warn('Raising the process priority not permitted',
                 RuntimeWarning, stacklevel = 2)
        else:
            raise
    _benchmarks = import_from_path(path_benchmarks)
    try:
        version, results = _benchmarks.main(**kwargs)
    except AttributeError as exc:
        raise AttributeError(
            f"module {_benchmarks.__name__!r} has no function main",
                             name = _benchmarks.__name__, obj = _benchmarks
                             ) from exc
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
