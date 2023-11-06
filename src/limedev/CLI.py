"""Command line interface tools."""
import sys
from types import ModuleType

from ._aux import _argumentparser
# ======================================================================
def function_cli(args = sys.argv[1:], # pylint: disable=dangerous-default-value
                 module: str | ModuleType = '__main__'
                 ) -> int:
    """Functions as main able to run functions matching signature and generate
    helptext."""
    if isinstance(module, str):
        module = sys.modules[module]

    if not args:
        # Generating helptext
        helptext = 'Functions available:'

        from inspect import signature

        for name, attr in module.__dict__.items():
            if (callable(attr)
                and not name.startswith('_')
                and name != 'main'
                and (_signature := signature(attr)).return_annotation in {int, 'int'}):
                helptext += f'\n\n{name}'

                # Adding parameters
                for parameter_name, parameter in _signature.parameters.items():
                    helptext += f' {parameter_name}'
                    if parameter.default is not parameter.empty:
                        helptext += f'={parameter.default}'

                # Adding docstring
                if attr.__doc__ is not None:
                    helptext += f"\n    '''{attr.__doc__}'''"
        print(helptext)
        return 0
    moduleargs, kwargs = _argumentparser(args[1:])
    return getattr(module, args[0])(*moduleargs, **kwargs)
