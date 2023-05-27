#!/usr/bin/env python3

from setuptools import setup, Command, find_packages
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

setup(
    name='symbiote',
    version='0.0.1',
    description='A command line harness to openai functions.',
    author='Wadih Khairallah',
    url='https://github.com/woodyk/symbiote',
    packages=find_packages(),
    install_requires=[
        'pynput==1.7.6',
        'clipboard==0.0.4',
        'python_magic==0.4.27',
        'textract==1.6.5',
        'InquirerPy==0.3.4',
        'openai==0.27.4',
        'tiktoken==0.3.3',
        'beautifulsoup4',
        'pexpect==4.8.0',
        'prompt_toolkit==3.0.38',
        'requests==2.28.2',
        'rich==13.3.4',
        'setuptools==67.6.1',
        'gitignore_parser==0.1.3'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        #'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.11',
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

