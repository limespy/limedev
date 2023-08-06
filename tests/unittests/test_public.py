import os
import subprocess

import limedev as ld
import pytest

SELF_TEST_FLAG = 'LIMEDEV_SELF_TEST'
IS_SELF_TEST = SELF_TEST_FLAG in os.environ
SELF_TEST_SKIP = pytest.mark.skipif(IS_SELF_TEST, reason = "Self test")

@SELF_TEST_SKIP
def test_package():
    subprocess.run(['package', '--no-build'])

@SELF_TEST_SKIP
def test_readme():
    subprocess.run(['readme'])

# ======================================================================
@SELF_TEST_SKIP
class Test_test:
    def subprocess_self_test(self, test_name: str):
        environment = os.environ.copy()
        environment[SELF_TEST_FLAG] = ''
        subprocess.run(['test', f'--{test_name}'], env = environment)
    # ------------------------------------------------------------------
    def test_unittests(self):
        return self.subprocess_self_test('unittests')
    # ------------------------------------------------------------------
    def test_profile(self):
        return self.subprocess_self_test('profiling')
    # ------------------------------------------------------------------
    def test_typing(self):
        return self.subprocess_self_test('typing')
    # ------------------------------------------------------------------
