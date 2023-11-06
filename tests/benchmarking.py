import limedev as ld
from limedev.test import BenchmarkResultsType
def main() -> BenchmarkResultsType:
    return ld.__version__, {}
