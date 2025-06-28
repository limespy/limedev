"""Test invokers."""
#%%=====================================================================
# IMPORT
from .._aux import PATH_PROJECT
from ..cli import get_main
from ._aux import BenchmarkResultsType as BenchmarkResultsType
from ._aux import eng_round as eng_round
from ._aux import TypingBackend
from .benchmarking import benchmarking as benchmarking
from .benchmarking import run_timed as run_timed
from .profiling import MissingDot as MissingDot
from .profiling import profiling as profiling
from .typing import typing as typing
from .unittesting import unittesting as unittesting
# ======================================================================
MYPY, PYREFLY, TY = TypingBackend

PATH_PYPROJECT = PATH_PROJECT / 'pyproject.toml'

# ======================================================================
main = get_main(__name__)
# ----------------------------------------------------------------------
if __name__ == '__main__':
    raise SystemExit(main())
