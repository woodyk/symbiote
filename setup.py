#!/usr/bin/env python3

from setuptools import setup, Command, find_packages
import platform
import os
import shutil

class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        shutil.rmtree('./build', ignore_errors=True)
        shutil.rmtree('./dist', ignore_errors=True)
        shutil.rmtree('./__pycache__', ignore_errors=True)
        shutil.rmtree('./.pytest_cache', ignore_errors=True)
        shutil.rmtree('./.tox', ignore_errors=True)
        shutil.rmtree('./.eggs', ignore_errors=True)
        shutil.rmtree('./htmlcov', ignore_errors=True)
        shutil.rmtree('./.coverage*', ignore_errors=True)
        shutil.rmtree('./docs/_build', ignore_errors=True)
        shutil.rmtree('./.mypy_cache', ignore_errors=True)
        shutil.rmtree('./.pytest_cache', ignore_errors=True)
        shutil.rmtree('./.mypy_cache', ignore_errors=True)
        shutil.rmtree('./dist-info', ignore_errors=True)
        shutil.rmtree('./build-info', ignore_errors=True)
        shutil.rmtree('./src/__pycache__', ignore_errors=True)

        for filename in ['./.coverage', './.coverage.*', './.coverage']:
            try:
                os.remove(filename)
            except OSError:
                pass
module = []
modules = []
# open the file
with open('requirements.txt', 'r') as f:
    for module in f:
        modules.append(module.strip())

modules.append("python-Levenshtein")

if platform.system() == 'Linux':
    modules.append('evdev==1.6.1')

setup(
    name='symbiote',
    version='0.13.0',
    description='A command line harness to AI functions.',
    author='Wadih Khairallah',
    url='https://github.com/woodyk/symbiote',
    packages=find_packages(),
    install_requires=modules,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    entry_points={
        'console_scripts': [
            'symbiote=symbiote.app:entry_point',
        ],
    },
    cmdclass={
        'clean': CleanCommand,
    }
)


