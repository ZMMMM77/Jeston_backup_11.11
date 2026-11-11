from setuptools import find_packages
from setuptools import setup

setup(
    name='raceline_msgs',
    version='0.0.0',
    packages=find_packages(
        include=('raceline_msgs', 'raceline_msgs.*')),
)
