#!/usr/bin/env python
# type: ignore
"""Updating the pyproject.toml metadata and packaging into wheel and source
distributions."""
# ======================================================================
# IMPORT
import sys
import time

import tomli_w

from ._aux import import_from_path
from ._aux import PATH_REPO
from ._aux import upsearch
from build import __main__ as build

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
# ======================================================================
def main(args = sys.argv[1:]) -> int: # pylint: disable=dangerous-default-value
    """Command line interface entry point.

    Builds README and the package
    """
    if (path_pyproject := upsearch('pyproject.toml')) is None:
        raise FileNotFoundError('pyproject.toml not found')

    path_readme = PATH_REPO / 'README.md'
    # ------------------------------------------------------------------
    # BUILD INFO

    # Loading the pyproject TOML file
    pyproject = tomllib.loads(path_pyproject.read_text())
    project_info = pyproject['project']
    # ------------------------------------------------------------------
    # URL
    source_url = project_info['urls'].get('Source Code',
                                          project_info['urls']['Homepage'])
    # ------------------------------------------------------------------
    # Long Description
    user_readme  = import_from_path(PATH_REPO / 'readme' / 'readme.py').main
    readme_text = str(user_readme(pyproject)) + '\n'
    readme_text_pypi = readme_text
    if source_url.startswith('https://github.com'):
        readme_text_pypi = readme_text_pypi.replace('(./',
                                                    f'({source_url}/blob/main/')
    # ------------------------------------------------------------------
    # Build number
    if '--build-number' in args:
        project_info['version'] += f'.{time.time():.0f}'
    # ------------------------------------------------------------------
    # RUNNING THE BUILD

    pyproject['project'] = project_info
    path_pyproject.write_text(tomli_w.dumps(pyproject))

    for path in (PATH_REPO / 'dist').glob('*'):
        path.unlink()

    path_readme.write_text(readme_text_pypi)

    if '--no-build' not in args:
        build.main([])

    path_readme.write_text(readme_text)
    return 0
# ======================================================================
if __name__ =='__main__':
    raise SystemExit(main())
