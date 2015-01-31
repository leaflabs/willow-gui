from PyQt4 import QtCore, QtGui
import sys, os, h5py
import numpy as np
import hwif
import CustomExceptions as ex

from parameters import *
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

class SnapshotThread(QtCore.QThread):

    valueChanged = QtCore.pyqtSignal(int)
    maxChanged = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(int)
    statusUpdated = QtCore.pyqtSignal(str)

    def __init__(self, nsamples_requested, filename):
        super(SnapshotThread, self).__init__()
        self.nsamples_requested = nsamples_requested
        self.filename = filename
        self.isTerminated = False

    def terminate(self):
        """
        This is required to prevent the race condition between QProgressDialog
        and this thread. self.isTerminated is checked before emission of valueChanged.
        """
        self.isTerminated = True
        super(SnapshotThread, self).terminate()

    def run(self):
        try:
            nsamples_actual = hwif.takeSnapshot(nsamples=self.nsamples_requested, filename=self.filename)
            self.finished.emit(nsamples_actual)
        except ex.StateChangeError:
            self.statusUpdated.emit('Caught StateChangeError')
        except ex.NoResponseError:
            self.statusUpdated.emit('Control Command got no response')
        except socket.error:
            self.statusUpdated.emit('Socket error: Could not connect to daemon.')
        except tuple(ex.ERROR_DICT.values()) as e:
            self.statusUpdated.emit('Error: %s' % e)

    def run_reference(self):
        f = h5py.File(self.filename)
        dset = f['wired-dataset']
        if self.sampleRange==-1:
            self.sampleRange = [0, len(dset)-1]
        self.nsamples = self.sampleRange[1] - self.sampleRange[0] + 1
        self.maxChanged.emit(self.nsamples)
        data = np.zeros((1024,self.nsamples), dtype='uint16')
        for i in range(self.nsamples):
            data[:,i] = dset[self.sampleRange[0]+i][3][:1024]
            if (i%1000==0) and not self.isTerminated:
                self.valueChanged.emit(i)
        self.valueChanged.emit(self.nsamples)   # to reset the progressdialog
        self.finished.emit(self.filename, data, self.sampleRange)

