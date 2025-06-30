from enum import Enum
from pathlib import Path

from ._aux import _pack_kwargs
from ._aux import eng_round
from ._aux import import_from_path
from ._aux import PATH_PROJECT
from ._aux import PATH_TESTS
# ======================================================================
# ----------------------------------------------------------------------
class MissingDot(Enum):
    ERROR = 0
    WARN = 1
    IGNORE = 2
# ======================================================================
def main(path_profiling: Path | None = None,
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
