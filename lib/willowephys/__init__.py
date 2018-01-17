import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

__version__ = read('LIB_VERSION').rstrip()

from const import *
from .willowdataset import WillowDataset
from .plotmatrix import PlotMatrix
