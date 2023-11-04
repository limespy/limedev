import os
import subprocess

import pytest

SELF_TEST_FLAG = 'LIMEDEV_SELF_TEST'
SELF_TEST_SKIP = pytest.mark.skipif(SELF_TEST_FLAG in os.environ,
                                    reason = 'Self test')

def runcheck(*args, check = True, **kwargs) -> None:
    subprocess.run(*args, check = check, **kwargs)

@SELF_TEST_SKIP
def test_package():
    runcheck(['package', '--no-build'])

@SELF_TEST_SKIP
def test_readme():
    runcheck(['readme'])

# ======================================================================
@SELF_TEST_SKIP
class Test_test:
    # ------------------------------------------------------------------
    def test_unittests(self):
        environment = os.environ.copy()
        environment[SELF_TEST_FLAG] = ''
        runcheck(['test', f'unittests'], env = environment)
    # ------------------------------------------------------------------
    def test_profile(self):
        runcheck(['test', 'profiling', '--no-warmup', '--ignore-missing-dot'])
    # ------------------------------------------------------------------
    def test_typing(self):
        runcheck(['test', 'typing'], check = False)
    # ------------------------------------------------------------------
    def test_performance(self):
        runcheck(['test', 'benchmarking'])
    # ------------------------------------------------------------------
    def test_lint(self):
        runcheck(['test', 'linting'])
    # ------------------------------------------------------------------
