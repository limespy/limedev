from .._aux import runcheck
# ======================================================================
def test_readme():
    """Readme generator."""
    runcheck('limedev', 'readme')
