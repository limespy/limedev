"""Publick interface correctness tests."""
from .._aux import runcheck
# ======================================================================
def test_package():
    """Packaging function."""
    runcheck('limedev', 'package')
