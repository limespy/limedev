from subprocess import run

run(('pip', 'install', '-e', '.[dev]'))
run(('pre-commit', 'install'))
run(('pre-commit', 'run', '--files', __file__))
