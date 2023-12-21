"""Benchmarking."""
import limedev as ld
from limedev.test import BenchmarkResultsType

def main() -> BenchmarkResultsType:
    """Called by the benchmark handler."""
    return ld.__version__, {}
