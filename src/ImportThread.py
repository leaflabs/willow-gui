from PyQt4 import QtCore, QtGui
import sys, os, h5py
import numpy as np
import hwif

from parameters import *
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

class ImportThread(QtCore.QThread):

    valueChanged = QtCore.pyqtSignal(int)
    maxChanged = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(str, np.ndarray, list)
    labelChanged = QtCore.pyqtSignal(str)

    def __init__(self, filename, sampleRange):
        super(ImportThread, self).__init__()
        self.filename = filename
        self.sampleRange = sampleRange
        self.isTerminated = False

    def handleCancel(self):
        """
        This is required to prevent the race condition between QProgressDialog
        and this thread. self.isTerminated is checked before emission of valueChanged.
        """
        self.isTerminated = True
        self.terminate()


    def run(self):
        f = h5py.File(self.filename)
        dset = f['wired-dataset']
        if self.sampleRange==-1:
            self.sampleRange = [0, len(dset)-1]
        self.nsamples = self.sampleRange[1] - self.sampleRange[0] + 1
        self.maxChanged.emit(self.nsamples)
        self.labelChanged.emit('Importing %s...' % self.filename)
        data = np.zeros((1024,self.nsamples), dtype='uint16')
        for i in range(self.nsamples):
            data[:,i] = dset[self.sampleRange[0]+i][3][:1024]
            if (i%1000==0) and not self.isTerminated:
                self.valueChanged.emit(i)
        self.valueChanged.emit(self.nsamples)   # to reset the progressdialog
        self.finished.emit(self.filename, data, self.sampleRange)

