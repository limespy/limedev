"""Defining the readme.md."""
import limedev
from limedev import readme
#=======================================================================
def main(pyproject: readme.Pyproject):
    """This gets called by the limedev."""

    name = pyproject['tool']['limedev']['full_name']
    semi_description = f'''
    {name} is collection tools for Python development.
    These tools are more or less thin wrappers around other packages.'''
    return readme.make(limedev, semi_description,
                       name = name)
#=======================================================================
