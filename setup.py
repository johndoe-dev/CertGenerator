#!/usr/bin/env python
"""
Run following commands on terminal to install required package and install cert cli in virtual environment

pip install --editable .
"""

import os
from codecs import open as c_open
from setuptools import setup, find_packages


def about(item=None):
    _about = {}
    here = os.path.abspath(os.path.dirname(__file__))
    with c_open(os.path.join(here, "certgenerator", "__version__.py"), 'r', 'utf-8') as version:
        exec(version.read(), _about)

    if item:
        return _about[item]
    return _about


def basedir():
    return os.path.abspath(os.path.dirname(__file__))


requirements_file = os.path.join(basedir(), 'requirements.txt')
if os.path.exists(requirements_file):
    with c_open(requirements_file) as f:
        requirements = f.read().splitlines()


setup(
    name=about('__title__'),
    version=about('__version__'),
    license=about('__license__'),
    author=about('__author__'),
    author_email=about('__author_email__'),
    url=about('__url__'),
    description=about('__description__'),
    long_description=open(about('__long_description__')).read(),
    py_modules='cert',
    install_requires=['click', 'pycparser', 'PyYAML'],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        # If any package contains *.ini files, include them
        '': ['*.ini', '*.yaml', '*.csv']
    },
    entry_points='''
        [console_scripts]
        cert=certgenerator.cli:main
    ''',
)
