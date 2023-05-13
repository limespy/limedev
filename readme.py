import limedev
import yamdog as md
from limedev import readme
#=======================================================================
NAME = 'LimeDev'
#=======================================================================
def make(project_info):

    semi_description = md.Document([
        f'{NAME} is collection tools for Python development.\n'
        'These tools are more or less thin wrappers around other packages.'
    ])
    return readme.make(limedev, semi_description,
                       name = NAME)
#=======================================================================
def main():

    import pathlib
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib # type: ignore

    PATH_BASE = pathlib.Path(__file__).parent
    PATH_README = PATH_BASE / 'README.md'
    PATH_PYPROJECT = PATH_BASE / 'pyproject.toml'

    PATH_README.write_text(str(make(tomllib.loads(PATH_PYPROJECT.read_text())['project']))
                           + '\n')
    return 0
#=======================================================================
if __name__ == '__main__':
    raise SystemExit(main())
