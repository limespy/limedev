"""Functions for doing profilings."""
import time

import limedev
from limedev import readme as rm
#=======================================================================
def empty():
    """Empty function."""

def readme():
    """Generation of a readme."""
    rm.make(limedev, '')

def sleep():
    """Just sleeping."""
    time.sleep(0.5)
