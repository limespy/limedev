#%%=====================================================================
# IMPORT
import os
import pathlib
import sys
from importlib import import_module
from typing import Callable
from typing import Iterable
from typing import NoReturn
from typing import Optional
from typing import Union

from ._aux import _upsearch

PATH_CONFIGS = pathlib.Path(__file__).parent / 'configs'
TEST_FOLDER_NAME = 'tests'
#%%=====================================================================
# TEST CASES

#%%=====================================================================
def _get_path_config(patterns, path_start):
    return (PATH_CONFIGS / patterns[0]
            if (path_local := _upsearch(patterns, path_start)) is None
            else path_local)
#==============================================================================
def unittests(path_tests: pathlib.Path) -> None:
    import pytest
    CWD = pathlib.Path.cwd()
    os.chdir(str(path_tests / 'unittests'))
    pytest.main(["--cov=numba_integrators", "--cov-report=html"])
    os.chdir(str(CWD))
    return None
#==============================================================================
def typing(path_tests: pathlib.Path) -> Optional[tuple[str, str, int]]:
    args = [str(path_tests.parent / 'src'),
            '--config-file',
            str(_get_path_config(('mypy.ini',), path_tests))]
    from mypy.main import main
    main(args = args)
#==============================================================================
def lint(path_tests: pathlib.Path) -> None:
    from pylint import lint
    lint.Run([str(path_tests.parent / 'src'),
              f'--rcfile={str(_get_path_config((".pylintrc",), path_tests))}',
              '--output-format=colorized',
              '--msg-template="{path}:{line}:{column}:{msg_id}:{symbol}\n'
                              '    {msg}"'])
#=======================================================================
def profiling(path_tests: pathlib.Path) -> None:
    import subprocess

    import cProfile
    import gprof2dot

    profile_run = import_module(f'{TEST_FOLDER_NAME}.profiling').main

    path_profile = path_tests / 'profile'
    path_pstats = path_profile.with_suffix('.pstats')
    path_dot = path_profile.with_suffix('.dot')
    path_pdf = path_profile.with_suffix('.pdf')

    profile_run() # Prep to eliminate first run overhead
    with cProfile.Profile() as pr:
        profile_run()
        pr.dump_stats(path_pstats)

    gprof2dot.main(['-f', 'pstats', str(path_pstats), '-o', path_dot])
    path_pstats.unlink()
    try:
        subprocess.run(['dot', '-Tpdf', str(path_dot), '-o', str(path_pdf)])
    except FileNotFoundError:
        raise RuntimeError('Conversion to PDF failed, maybe graphviz dot program is not installed. http://www.graphviz.org/download/')
    path_dot.unlink()
#==============================================================================
TESTS: dict[str, Callable] = {function.__name__: function # type: ignore
                              for function in
                              (lint, unittests, typing, profiling)}
def main(args: list[str] = sys.argv[1:]) -> int:

    if (path_tests := _upsearch(TEST_FOLDER_NAME)) is None:
        raise FileNotFoundError('Tests not found')

    sys.path.insert(1, str(path_tests.parent))

    if not args:
        return 0
    for arg in args:
        if arg.startswith('--'):
            name = arg[2:]
            if (function := TESTS.get(name)) is None:
                import_module(f'{TEST_FOLDER_NAME}.{name}').main()
            else:
                function(path_tests)
    return 0
#==============================================================================
if __name__ == '__main__':
    raise SystemExit(main())
