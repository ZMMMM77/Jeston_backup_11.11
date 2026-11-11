from setuptools import find_packages
from setuptools import setup

setup(
    name='lab7_pkg',
    version='0.0.0',
    packages=find_packages(
        include=('lab7_pkg', 'lab7_pkg.*')),
)
