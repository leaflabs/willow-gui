from PyQt4 import QtCore, QtGui
import sys, os, h5py
import numpy as np
import hwif

import config
sys.path.append(os.path.join(config.daemonDir, 'util'))
from daemon_control import *

from WillowDataset import WillowDataset

class ImportThread(QtCore.QThread):

    valueChanged = QtCore.pyqtSignal(int)
    maxChanged = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(object)
    labelChanged = QtCore.pyqtSignal(str)
    statusUpdated= QtCore.pyqtSignal(str)
    canceled = QtCore.pyqtSignal()

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
        is_live = bool(dset[0][0] & (1<<6))
        if self.sampleRange==-1:
            self.sampleRange = [0, len(dset)-1]
        else:
            dsetMin = int(dset[0][1])
            dsetMax = int(dset[-1][1])
            if is_live:
                # need to normalize because snapshots have random offsets
                dsetMax -= dsetMin
                dsetMin = 0
            if (self.sampleRange[0] < dsetMin) or (self.sampleRange[1] > dsetMax):
                self.statusUpdated.emit('Error: sampleRange [%d, %d] out of range for dset: [%d, %d]'
                    % tuple(self.sampleRange+[dsetMin,dsetMax]))
                self.canceled.emit()
                return
        self.nsamples = self.sampleRange[1] - self.sampleRange[0] + 1
        if self.nsamples > 5e6:
            self.statusUpdated.emit('Data range exceeds memory limit of 5 million samples')
            return
        self.maxChanged.emit(self.nsamples)
        self.labelChanged.emit('Importing %s...' % self.filename)
        data = np.zeros((1024,self.nsamples), dtype='uint16')
        for i in range(self.nsamples):
            data[:,i] = dset[self.sampleRange[0]+i][3][:1024]
            if (i%1000==0) and not self.isTerminated:
                self.valueChanged.emit(i)
        willowDataset = WillowDataset(data, self.sampleRange, self.filename)
        self.valueChanged.emit(self.nsamples)   # to reset the progressdialog
        self.finished.emit(willowDataset)

