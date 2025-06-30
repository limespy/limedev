"""Benchmarking."""
import limedev as ld
from limedev import eng_round
from limedev import readme
from limedev.benchmarking import BenchmarkResultsType
from limedev.benchmarking import run_timed


def main() -> BenchmarkResultsType:
    """Called by the benchmark handler."""
    results = {}
    for name, function in (('build readme', readme.main),):
        result, prefix = eng_round(run_timed(function)())
        results[f'{name} [{prefix}s]'] = result
    return ld.__version__, results
