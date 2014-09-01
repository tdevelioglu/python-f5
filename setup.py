#!/usr/bin/python
from setuptools import setup, find_packages

setup(
    name='f5',
    version='0.1.11',
    install_requires=['bigsuds'],
    description='Python Library to interact with F5',
    author='Taylan Develioglu',
    url='https://github.com/tdevelioglu/python-f5;',
    package_dir={'f5': 'src'},
    packages = ['f5'],
    license = 'Apache',
)
