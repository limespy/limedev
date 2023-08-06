from typing import Union

import limedev as ld

def main() -> tuple[str, dict[str, Union[int, float, str, list, dict]]]:
    return ld.__version__, {}
