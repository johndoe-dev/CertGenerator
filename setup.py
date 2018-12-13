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


def long_description():
    try:
        return open(about('__long_description__')).read()
    except IOError:
        return ""


setup(
    name=about('__title__'),
    version=about('__version__'),
    author=about('__author__'),
    author_email=about('__author_email__'),
    url=about('__url__'),
    description=about('__description__'),
    long_description=long_description(),
    py_modules='cert',
    install_requires=['click', 'PyYAML', 'pyOpenSSL', 'ruamel.yaml'],
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
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Security',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Environment :: MacOS X',
        'Environment :: Console',
        'Programming Language :: Python :: 2.7',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X'
    ],
)
