import os
import subprocess

import limedev as ld
import pytest

SELF_TEST_FLAG = 'LIMEDEV_SELF_TEST'
SELF_TEST_SKIP = pytest.mark.skipif(SELF_TEST_FLAG in os.environ,
                                    reason = "Self test")

@SELF_TEST_SKIP
def test_package():
    subprocess.run(['package', '--no-build'])

@SELF_TEST_SKIP
def test_readme():
    subprocess.run(['readme'])

# ======================================================================
@SELF_TEST_SKIP
class Test_test:
    # ------------------------------------------------------------------
    def test_unittests(self):
        environment = os.environ.copy()
        environment[SELF_TEST_FLAG] = ''
        subprocess.run(['test', f'--unittests'], env = environment)
    # ------------------------------------------------------------------
    def test_profile(self):
        subprocess.run(['test', '--profiling'])
    # ------------------------------------------------------------------
    def test_typing(self):
        subprocess.run(['test', '--typing'])
    # ------------------------------------------------------------------
    def test_performance(self):
        subprocess.run(['test', '--performance'])
    # ------------------------------------------------------------------
    def test_lint(self):
        subprocess.run(['test', '--lint'])
    # ------------------------------------------------------------------
