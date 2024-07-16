"""Publick interface correctness tests."""
import os
import subprocess

import pytest

SELF_TEST_FLAG = 'LIMEDEV_SELF_TEST'
SELF_TEST_SKIP = pytest.mark.skipif(SELF_TEST_FLAG in os.environ,
                                    reason = 'Self test')

def runcheck(*args, check = True, **kwargs) -> None:
    """Runs with as default check."""
    subprocess.run(*args, check = check, **kwargs)

@SELF_TEST_SKIP
def test_package():
    """Packaging function."""
    runcheck(('package', '--no-build'))

@SELF_TEST_SKIP
def test_readme():
    """Readme generator."""
    runcheck(('readme'))

# ======================================================================
@SELF_TEST_SKIP
class Test_test:
    """Testing module tests."""
    # ------------------------------------------------------------------
    def test_unittests(self):
        """Unittests handler."""
        environment = os.environ.copy()
        environment[SELF_TEST_FLAG] = ''
        runcheck(('test', 'unittests'), env = environment)
    # ------------------------------------------------------------------
    def test_profile(self):
        """Profiling handler."""
        runcheck(('test', 'profiling', '--no_warmup', '--ignore_missing_dot'))
    # ------------------------------------------------------------------
    def test_typing(self):
        """Type check handler."""
        runcheck(('test', 'typing'), check = False)
    # ------------------------------------------------------------------
    def test_benchmarking(self):
        """Benchmarking handler."""
        runcheck(('test', 'benchmarking'))
    # ------------------------------------------------------------------
    def test_lint(self):
        """Linting handler."""
        runcheck(('test', 'linting'))
    # ------------------------------------------------------------------
