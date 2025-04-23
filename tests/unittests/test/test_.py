"""Publick interface correctness tests."""
from subprocess import run

import pytest
from limedev import test

from .._aux import runcheck
# ======================================================================

SKIP_NO_DOT = pytest.mark.skipif(not run(('dot', '-V')).returncode,
                                 reason = 'Graphviz dot not available')
# ======================================================================
class Test_benchmarking:
    """Testing benchmarking."""
    # ------------------------------------------------------------------
    def test_cli(self):
        """Benchmarking handler."""
        runcheck('limedev', 'benchmarking')
# ======================================================================
class Test_linting:
    """Testing linting."""
    # ------------------------------------------------------------------
    def test_cli(self):
        """Linting handler."""
        runcheck('limedev', 'linting')
# ======================================================================
class Test_profiling:
    """Testing profiling."""
    # ------------------------------------------------------------------
    def test_cli(self):
        """Profiling handler."""
        runcheck('limedev',
                 'profiling',
                 '--function=empty',
                 '--no_warmup',
                 '--missing_dot=IGNORE')
    # ------------------------------------------------------------------
    def test_warmup(self):
        """Profiling handler."""
        test.profiling(function = 'empty',
                       no_warmup = False,
                       missing_dot = test.MissingDot.IGNORE)
    # ------------------------------------------------------------------
    def test_missing_dot_IGNORE(self):
        """Profiling handler."""
        test.profiling(function = 'empty',
                       no_warmup = True,
                       missing_dot = test.MissingDot.IGNORE)
    # ------------------------------------------------------------------
    @SKIP_NO_DOT
    def test_missing_dot_ERROR(self):
        """Profiling handler."""
        with pytest.raises(RuntimeError):
            test.profiling(function = 'empty',
                           no_warmup = True,
                           missing_dot = test.MissingDot.ERROR)
    # ------------------------------------------------------------------
    @SKIP_NO_DOT
    def test_missing_dot_WARN(self):
        """Profiling handler."""
        with pytest.warns(RuntimeWarning):
            test.profiling(function = 'empty',
                           no_warmup = True,
                           missing_dot = test.MissingDot.WARN)
# ======================================================================
class Test_typing:
    """Testing typing."""
    # ------------------------------------------------------------------
    def test_cli(self):
        """Type check handler."""
        runcheck('limedev', 'typing', check = False)
# ======================================================================
class Test_unittests:
    """Testing unittests."""
    # ------------------------------------------------------------------
    def test_cli(self):
        """Unittests handler."""
        runcheck('limedev', 'unittests', '--tests="dummy"')
