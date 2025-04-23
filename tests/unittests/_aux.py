import os
from subprocess import run

import pytest
# ======================================================================
SELF_TEST_FLAG = 'LIMEDEV_SELF_TEST'
SELF_TEST_SKIP = pytest.mark.skipif(SELF_TEST_FLAG in os.environ,
                                    reason = 'Self test')
# ======================================================================
def runcheck(*args: str, check: bool = True, **kwargs) -> None:
    """Runs with as default check."""
    run(args, check = check, **kwargs)
