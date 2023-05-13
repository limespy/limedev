#!/usr/bin/env python
# type: ignore
#%%═════════════════════════════════════════════════════════════════════
# IMPORT
import pathlib
import re
import sys
import time

import tomli_w
from build import __main__ as build

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

def main(args = sys.argv[1:]):
    path_cwd = pathlib.Path.cwd()
    try:
        path_pyproject = next(path_cwd.rglob('pyproject.toml'))
    except StopIteration:
        print(f'Tests not found under {path_cwd}')

    path_base = path_pyproject.parent
    path_readme = path_base / 'readme.md'

    sys.path.insert(1, str(path_base))
    if (path_base_str := str(path_base)) not in sys.path[:3]:
        sys.path.insert(1, path_base_str)
    import readme
    #%%═════════════════════════════════════════════════════════════════════
    # BUILD INFO

    # Loading the pyproject TOML file
    pyproject = tomllib.loads(path_pyproject.read_text())
    project_info = pyproject['project']
    path_package_init = next((path_base / 'src').rglob('__init__.py'))
    version = re.search(r"(?<=__version__ = ').*(?=')",
                        path_package_init.read_text())[0]

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
    readme_text = str(readme.make(project_info)) + '\n'
    readme_text_pypi = readme_text.replace('./', source_main_url)
    #%%═════════════════════════════════════════════════════════════════════
    # RUNNING THE BUILD

    pyproject['project'] = project_info
    path_pyproject.write_text(tomli_w.dumps(pyproject))

    for path in (path_base / 'dist').glob('*'):
        path.unlink()

    path_readme.write_text(readme_text_pypi)

    if not '--no-build' in args:
        build.main([])

    path_readme.write_text(readme_text)
#=======================================================================
if __name__ =='__main__':
    raise SystemExit(main())
