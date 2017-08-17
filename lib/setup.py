import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='willowephys',
    version=read('willowephys/LIB_VERSION').rstrip(),
    description='Tools for the control of Willow electrophysiology systems and visualization of data obtained with them.',
    author='Sara Sinback',
    author_email='sinback@leaflabs.com',
    packages=['willowephys'],
    #package_data={'': ['willowephys/LIB_VERSION']},
    include_package_data=True,
    install_requires=[
        'numpy',
        'scipy',
        'sharedmem',
        'h5py>=2.5.0',
    ],
    long_description=read('README.md'),
)
