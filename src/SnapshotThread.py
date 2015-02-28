from PyQt4 import QtCore, QtGui
import sys, os, h5py, socket
import numpy as np
import hwif
import CustomExceptions as ex
from WillowDataset import WillowDataset

class SnapshotThread(QtCore.QThread):

    progressUpdated = QtCore.pyqtSignal(int)
    maxChanged = QtCore.pyqtSignal(int)
    labelChanged = QtCore.pyqtSignal(str)
    msgPosted = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    importFinished = QtCore.pyqtSignal(object)

    def __init__(self, params):
        QtCore.QThread.__init__(self)
        self.nsamples_requested = params['nsamples']
        self.filename = params['filename']
        self.plot = params['plot']
        self.isTerminated = False

    def handleCancel(self):
        """
        This is required to prevent the race condition between QProgressDialog
        and this thread. self.isTerminated is checked before emission of valueChanged.
        """
        self.isTerminated = True
        self.terminate()

    def run(self):
        try:
            nsamples_actual = hwif.takeSnapshot(nsamples=self.nsamples_requested, filename=self.filename)
            self.msgPosted.emit('Snapshot Complete: %d samples saved to %s' %
                (nsamples_actual, self.filename))
            if self.plot:
                dataset = WillowDataset(self.filename, -1)
                self.labelChanged.emit('Importing snasphot..')
                self.maxChanged.emit(dataset.nsamples)
                dataset.progressUpdated.connect(self.progressUpdated)
                dataset.importData()
                self.importFinished.emit(dataset)
            self.finished.emit()
        except ex.StateChangeError:
            self.msgPosted.emit('Caught StateChangeError')
        except ex.NoResponseError:
            self.msgPosted.emit('Control Command got no response')
        except socket.error:
            self.msgPosted.emit('Socket error: Could not connect to daemon.')
        except tuple(ex.ERROR_DICT.values()) as e:
            self.msgPosted.emit('Error: %s' % e)

