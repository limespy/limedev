from pathlib import Path

from ._aux import _pack_kwargs
from ._aux import PATH_DEFAULT_CONFIGS
from ._aux import PATH_PROJECT
from ._aux import PATH_TESTS
from ._aux import upsearch
# ======================================================================
def main(path_unittests: Path | None = None,
              cov: bool = False,
              tests: str = '',
              **kwargs: str
              ) -> int:
    """Starts pytest unit tests."""
    import pytest

    if path_unittests is None:
        if PATH_TESTS is None:
            path_unittests = PATH_PROJECT
        elif not (path_unittests := PATH_TESTS / 'unittests').exists():
            path_unittests = PATH_TESTS

    if cov and ('cov-report' not in kwargs):
        kwargs['cov-report'] = f"html:{path_unittests/'htmlcov'}"

    if (config_file_arg := kwargs.get('config-file')) is None:
        # Trying to find and insert a config file
        try:
            # Looking recursively under unittest forlder
            kwargs['config-file'] = str(next(path_unittests.rglob('pytest.ini')))
        except StopIteration:
            path_config = upsearch('pytest.ini',
                                   path_unittests,
                                   path_stop = PATH_PROJECT)
            if path_config is None:

                if (path_config := upsearch('pyproject.toml',
                                               path_unittests,
                                               path_stop = PATH_PROJECT)
                    ) is not None:
                    if path_config.read_text().find('[tool.pytest.ini_options]') == -1:
                        # Configuration not found
                        path_config = upsearch('pytest.ini',
                                               PATH_DEFAULT_CONFIGS)

            if path_config is not None:
                kwargs['config-file'] = str(path_config)

    elif config_file_arg == '':
        kwargs.pop('config-file')
    if (status := pytest.main([str(path_unittests), '-k', tests,
                                 *_pack_kwargs(kwargs)])) == 0:
        return status
    raise Exception(f'Exit status {status}')
