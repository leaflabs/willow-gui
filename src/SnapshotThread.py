from PyQt4 import QtCore, QtGui
import sys, os, h5py
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
        except hwif.StateChangeError:
            self.msgPosted.emit('Caught StateChangeError')
        except hwif.hwifError as e:
            self.msgPosted.emit(e.message)
        finally:
            self.finished.emit()
