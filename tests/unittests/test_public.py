import os
import subprocess

import pytest

SELF_TEST_FLAG = 'LIMEDEV_SELF_TEST'
SELF_TEST_SKIP = pytest.mark.skipif(SELF_TEST_FLAG in os.environ,
                                    reason = 'Self test')

def runcheck(*args, **kwargs) -> bool:
    return subprocess.run(*args, **kwargs).returncode == 0

@SELF_TEST_SKIP
def test_package():
    assert runcheck(['package', '--no-build'])

@SELF_TEST_SKIP
def test_readme():
    assert runcheck(['readme'])

# ======================================================================
@SELF_TEST_SKIP
class Test_test:
    # ------------------------------------------------------------------
    def test_unittests(self):
        environment = os.environ.copy()
        environment[SELF_TEST_FLAG] = ''
        assert runcheck(['test', f'unittests'], env = environment)
    # ------------------------------------------------------------------
    def test_profile(self):
        assert runcheck(['test', 'profiling'])
    # ------------------------------------------------------------------
    def test_typing(self):
        assert runcheck(['test', 'typing'])
    # ------------------------------------------------------------------
    def test_performance(self):
        assert runcheck(['test', 'benchmarking'])
    # ------------------------------------------------------------------
    def test_lint(self):
        assert runcheck(['test', 'linting'])
    # ------------------------------------------------------------------
