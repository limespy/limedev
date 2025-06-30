#!/usr/bin/env python
# type: ignore
"""Updating the pyproject.toml metadata and packaging into wheel and.

source.

distributions.
"""
# ======================================================================
# IMPORT
import tomllib # type: ignore[unresolved-inport]
from pathlib import Path
from time import time
from typing import TYPE_CHECKING

import tomli_w

from .._aux import import_from_path
from .._aux import PATH_PROJECT
from .._aux import upsearch
# ======================================================================
# Hinting types
if TYPE_CHECKING:
    from typing import TypeAlias
    from collections.abc import Iterable
    OptionTree: TypeAlias = dict[str, 'OptionTree' | str]
else:
    Iterable = tuple
    OptionTree = object
# ======================================================================
DEPENDENCIES_PREFIX = 'requirements_'
# ======================================================================
def insert_option(option_tree: OptionTree, option: Iterable[str]) -> None:
    options = [option]
    while (split := option.rpartition('-'))[1]:
        option = split[0]
        options.append(option)

    options.reverse()
    options_iter = iter(options)
    for option in options_iter:

        if (suboption_tree := option_tree.get(option)) is None:
            suboption_tree = {}
            option_tree[option] = suboption_tree
            option_tree = suboption_tree

            for option in options_iter:
                suboption_tree = {}
                option_tree[option] = suboption_tree
                option_tree = suboption_tree

            break
        option_tree = suboption_tree
# ======================================================================
def construct_options(project_name: str,
                      path_dependencies: Path,
                      option_tree: OptionTree,
                      all_options: dict[str, Path]
                      ) -> dict[str, Path]:

    for option, suboption_tree in option_tree.items():

        dependencies = {f'{project_name}[{req}]\n' for req in suboption_tree}

        # Fill in the dependencies
        path = path_dependencies / f'{DEPENDENCIES_PREFIX}{option}.txt'

        all_options[option] = path

        path.touch()
        prefix = f'{project_name}[{option}'
        with open(path, 'r+') as file:
            dependencies.update(line for line in file.readlines()
                                if not (line in dependencies
                                        or line.startswith(prefix)))
            file.seek(0)
            file.truncate()
            file.writelines(sorted(dependencies))

        construct_options(project_name,
                          path_dependencies,
                          suboption_tree,
                          all_options)
    return all_options
# ======================================================================
def package(build: bool = False,
            build_number: bool = False,
            release_candidate: int = 0) -> int:
    """Command line interface entry point.

    Builds README and the package
    """
    if (path_pyproject := upsearch('pyproject.toml')) is None:
        raise FileNotFoundError('pyproject.toml not found')

    path_readme = PATH_PROJECT / 'README.md'
    # ------------------------------------------------------------------
    # BUILD INFO

    # Loading the pyproject TOML file
    pyproject = tomllib.loads(path_pyproject.read_text())
    project_info = pyproject['project']
    pypi_name = project_info['name']
    # ------------------------------------------------------------------
    # optional-dependencies

    # read all

    option_tree: OptionTree = {}

    # Read current option files
    path_dependencies = PATH_PROJECT / 'dependencies'
    for path in path_dependencies.rglob(f'{DEPENDENCIES_PREFIX}*.txt'):
        option_name = path.stem.removeprefix(DEPENDENCIES_PREFIX)
        if option_name != 'all':
            insert_option(option_tree, option_name)

    # Build option groups
    all_options = construct_options(pypi_name,
                                    path_dependencies,
                                    {'all': option_tree},
                                    {})

    # Sort and convert to posix paths
    pyproject['tool']['setuptools']['dynamic']['optional-dependencies'] = (
        {option: {'file': path.relative_to(PATH_PROJECT).as_posix()}
         for option, path in sorted(all_options.items(),
                                    key = lambda item: item[0])})
    # ------------------------------------------------------------------
    # URL
    source_url = project_info['urls'].get('Source Code',
                                          project_info['urls']['Homepage'])
    # ------------------------------------------------------------------
    # Long Description
    user_readme  = import_from_path(PATH_PROJECT / 'readme' / 'readme.py').main
    readme_text = str(user_readme(pyproject)) + '\n'
    readme_text_pypi = readme_text
    if source_url.startswith('https://github.com'):
        readme_text_pypi = readme_text_pypi.replace('(./',
                                                    f'({source_url}/blob/main/')
    # ------------------------------------------------------------------
    # Release candidate
    if release_candidate:
        project_info['version'] += f'rc{release_candidate}'
    # ------------------------------------------------------------------
    # Build number
    if build_number:
        project_info['version'] += f'.{time():.0f}'
    # ------------------------------------------------------------------
    # RUNNING THE BUILD

    pyproject['project'] = project_info
    path_pyproject.write_text(tomli_w.dumps(pyproject))

    for path in (PATH_PROJECT / 'dist').glob('*'):
        path.unlink()

    path_readme.write_text(readme_text_pypi)

    if build:
        from build.__main__ import main as _build
        _build([], prog = pypi_name)

    path_readme.write_text(readme_text)
    return 0
