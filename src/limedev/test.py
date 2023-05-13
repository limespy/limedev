#%%═════════════════════════════════════════════════════════════════════
# IMPORT
import os
import pathlib
import sys
from importlib import import_module
from typing import Callable
from typing import NoReturn
from typing import Optional
from typing import Union

PATH_CONFIG = pathlib.Path(__file__).parent / 'config'
#%%═════════════════════════════════════════════════════════════════════
# TEST CASES

#══════════════════════════════════════════════════════════════════════════════
def unittests(path_tests: pathlib.Path) -> None:
    import pytest
    CWD = pathlib.Path.cwd()
    os.chdir(str(path_tests / 'unittests'))
    pytest.main(["--cov=numba_integrators", "--cov-report=html"])
    os.chdir(str(CWD))
    return None
#══════════════════════════════════════════════════════════════════════════════
def typing(path_tests: pathlib.Path) -> Optional[tuple[str, str, int]]:
    path_mypy_config = (path_local
                        if (path_local := (path_tests / 'mypy.ini')).exists()
                        else PATH_CONFIG / 'mypy.ini')
    args = [str(path_tests.parent / 'src'),
            '--config-file',
            str(path_mypy_config)]
    from mypy.main import main
    main(args = args)
#══════════════════════════════════════════════════════════════════════════════
def lint(path_tests: pathlib.Path) -> None:
    from pylint import lint
    lint.Run([str(path_tests.parent / 'src'),
              f'--rcfile={str(PATH_CONFIG / ".pylintrc")}',
              '--output-format=colorized',
              '--msg-template="{path}:{line}:{column}:{msg_id}:{symbol}\n'
                              '    {msg}"'])
#═══════════════════════════════════════════════════════════════════════
def profile(path_tests: pathlib.Path):
    import subprocess

    import cProfile
    import gprof2dot

    from profile import main as profile_run # type: ignore

    path_profile = path_tests / 'profile'
    path_pstats = path_profile.with_suffix('.pstats')
    path_dot = path_profile.with_suffix('.dot')
    path_pdf = path_profile.with_suffix('.pdf')

    profile_run()
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
#══════════════════════════════════════════════════════════════════════════════
TESTS: dict[str, Callable] = {function.__name__: function # type: ignore
                              for function in
                              (lint, unittests, typing, profile)}
def main(args: list[str] = sys.argv[1:]) -> Union[list, None, NoReturn]:
    path_cwd = pathlib.Path.cwd()
    try:
        path_tests = next(path_cwd.rglob('tests'))
    except StopIteration:
        print(f'Tests not found under {path_cwd}')

    sys.path.insert(1, str(path_tests))

    if not args:
        return None
    for arg in args:
        if arg.startswith('--'):
            name = arg[2:]
            if (function := TESTS.get(name)) is None:
                module = import_module(name)
                module.main()
            else:
                function(path_tests)
    return None
#══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    raise SystemExit(main())
