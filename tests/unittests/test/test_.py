"""Publick interface correctness tests."""
from subprocess import run

import pytest
from limedev.profiling import main as profile
from limedev.profiling import MissingDot

from .._aux import runcheck
# ======================================================================
try:
    run(('dot', '-V'))
except FileNotFoundError:
    IS_DOT = False
else:
    IS_DOT = True
SKIP_IS_DOT = pytest.mark.skipif(IS_DOT,
                                 reason = 'Graphviz dot available')
SKIP_NO_DOT = pytest.mark.skipif(not IS_DOT,
                                 reason = 'Graphviz dot not available')
# ======================================================================
class Test_benchmarking:
    """Testing benchmarking."""
    # ------------------------------------------------------------------
    def test_cli(self):
        """Benchmarking handler."""
        runcheck('limedev', 'benchmark')
# ======================================================================
class Test_linting:
    """Testing linting."""
    # ------------------------------------------------------------------
    def test_cli(self):
        """Linting handler."""
        runcheck('limedev', 'lint')
# ======================================================================
class Test_profiling:
    """Testing profiling."""
    # ------------------------------------------------------------------
    def test_cli(self):
        """Profiling handler."""
        runcheck('limedev',
                 'profile',
                 '--function=empty',
                 '--no_warmup',
                 '--missing_dot=IGNORE')
    # ------------------------------------------------------------------
    @SKIP_NO_DOT
    def test_missing_dot_base(self):
        """Profiling handler."""
        profile(function = 'empty',
                       no_warmup = True,
                       missing_dot = MissingDot.ERROR)
    # ------------------------------------------------------------------
    def test_warmup(self):
        """Profiling handler."""
        profile(function = 'empty',
                       no_warmup = False,
                       missing_dot = MissingDot.IGNORE)
    # ------------------------------------------------------------------
    @SKIP_IS_DOT
    def test_missing_dot_IGNORE(self):
        """Profiling handler."""
        profile(function = 'empty',
                       no_warmup = True,
                       missing_dot = MissingDot.IGNORE)
    # ------------------------------------------------------------------
    @SKIP_IS_DOT
    def test_missing_dot_ERROR(self):
        """Profiling handler."""
        with pytest.raises(RuntimeError):
            profile(function = 'empty',
                           no_warmup = True,
                           missing_dot = MissingDot.ERROR)
    # ------------------------------------------------------------------
    @SKIP_IS_DOT
    def test_missing_dot_WARN(self):
        """Profiling handler."""
        with pytest.warns(RuntimeWarning):
            profile(function = 'empty',
                           no_warmup = True,
                           missing_dot = MissingDot.WARN)
# ======================================================================
class Test_typing:
    """Testing typing."""
    # ------------------------------------------------------------------
    def test_cli(self):
        """Type check handler."""
        runcheck('limedev', 'type', check = False)
# ======================================================================
class Test_unittests:
    """Testing unittests."""
    # ------------------------------------------------------------------
    def test_cli(self):
        """Unittests handler."""
        runcheck('limedev', 'unittest', '--tests="dummy"')
