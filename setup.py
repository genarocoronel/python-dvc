import platform
from setuptools import setup, find_packages
from distutils.errors import DistutilsPlatformError
from dvc import VERSION

install_requires = [
    "boto>=2.46.1",
    "google-compute-engine>=2.4.1", #required by boto
    "configparser>=3.5.0",
    "fasteners>=0.14.1",
    "future>=0.16.0",
    "google-cloud>=0.24.0",
    "colorama>=0.3.9",
    "configobj>=5.0.6",
    "networkx>=1.11",
    "pyyaml>=3.12",
    "tinydb>=3.7.0",
    "gitpython>=2.1.8",
    "ntfsutils>=0.1.3",
    "pygraphviz>=1.3.1",
    "checksumdir>=1.1.4",
]

setup(
    name='dvc',
    version=VERSION,
    description='Data Version Control makes your data science projects reproducible and shareable.',
    author='Dmitry Petrov',
    author_email='dmitry@dataversioncontrol.com',
    url='https://github.com/dataversioncontrol/dvc.git',
    license='Apache License 2.0',
    install_requires=install_requires,
    keywords='data science, data version control, machine learning',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    packages=find_packages(exclude=['bin', 'tests', 'functests']),
    include_package_data=True,
    download_url='http://dataversioncontrol.com',
    entry_points={
        'console_scripts': ['dvc = dvc.main:main']
    },
    zip_safe=False
)
