#!/usr/bin/env python3

from setuptools import setup, Command, find_packages
import platform
import subprocess
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
    subprocess.run(["sudo", "apt-get", "install", "curl", "autoconf", "automake", "libtool", "pkg-config"])
    subprocess.run(["sudo", "ldconfig"])

    if os.path.isfile('/etc/lsb-release'):
        # Ubuntu
        print('Please run `sudo apt-get install libmagic-dev` to install libmagic on Ubuntu.')
    elif os.path.isfile('/etc/redhat-release'):
        # RedHat/CentOS
        print('Please run `sudo yum install libmagic-devel` to install libmagic on RedHat/CentOS.')
    elif os.path.isfile('/etc/os-release'):
        # Other Linux distros
        print('Please use your package manager to install libmagic-devel or libmagic-dev on this system.')

    modules.append('evdev==1.6.1')

if platform.system() == 'Darwin':
    subprocess.run(["brew", "install", "curl", "autoconf", "automake", "libtool", "pkg-config"])

if platform.system() == 'Windows':
    print('Please install libmagic-devel or libmagic-dev using your package manager.')

# Gather nltk and spacy requirements
try:
    subprocess.call(['python3', '-m', 'spacy', 'download', 'en_core_web_sm'])
    subprocess.call(['python3', '-m', 'nltk.downloader', 'vader_lexicon'])
    subprocess.call(['python3', '-m', 'nltk.downloader', 'words'])
    subprocess.call(['python3', '-m', 'nltk.downloader', 'stopwords'])
    subprocess.call(['python3', '-m', 'nltk.downloader', 'punkt'])
    subprocess.call(['python3', '-m', 'nltk.downloader', 'averaged_perceptron_tagger'])
    subprocess.call(['python3', '-m', 'nltk.downloader', 'averaged_perceptron_tagger_eng'])
    subprocess.call(['python3', '-m', 'nltk.downloader', 'punkt_tab'])
    subprocess.call(['python3', '-m', 'nltk.downloader', 'maxent_ne_chunker'])
except Exception as e:
    print(f"Error installing nltk vader_lexicon: {e}")


setup(
    name='symbiote',
    version='0.14.0',
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
    },
    python_requires='>=3.10, <3.13',
)
