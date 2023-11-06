#!/usr/bin/env python
# type: ignore
"""Updating the pyproject.toml metadata and packaging into wheel and source
distributions."""
#%%═════════════════════════════════════════════════════════════════════
# IMPORT
import re
import sys
import time

import tomli_w
from build import __main__ as build

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from ._aux import _import_from_path
from ._aux import _upsearch
from ._aux import PATH_REPO


def main(args = sys.argv[1:]) -> int: # pylint: disable=dangerous-default-value
    """Command line interface entry point.

    Builds README and the package
    """
    if (path_pyproject := _upsearch('pyproject.toml')) is None:
        raise FileNotFoundError('pyproject.toml not found')

    path_readme = PATH_REPO / 'README.md'
    #%%═════════════════════════════════════════════════════════════════════
    # BUILD INFO

    # Loading the pyproject TOML file
    pyproject = tomllib.loads(path_pyproject.read_text())
    project_info = pyproject['project']
    version = re.search(r"(?<=__version__ = ').*(?=')",
                        next((PATH_REPO / 'src').rglob('__init__.py')
                             ).read_text())[0]

    if '--build-number' in args:
        version += f'.{time.time():.0f}'

    project_info['version'] = version
    #───────────────────────────────────────────────────────────────────────
    # URL
    source_url = project_info['urls'].get('Source Code',
                                          project_info['urls']['Homepage'])
    if source_url.startswith('https://github.com'):
        source_main_url = source_url + '/blob/main/'
    #───────────────────────────────────────────────────────────────────────
    # Long Description
    user_readme  = _import_from_path(PATH_REPO / 'readme' / 'readme.py').main
    readme_text = str(user_readme(project_info)) + '\n'
    readme_text_pypi = readme_text.replace('./', source_main_url)
    #%%═════════════════════════════════════════════════════════════════════
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
#=======================================================================
if __name__ =='__main__':
    raise SystemExit(main())
