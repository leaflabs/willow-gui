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
    statusUpdated = QtCore.pyqtSignal(str)

    def __init__(self, nsamples_requested, filename):
        super(SnapshotThread, self).__init__()
        self.nsamples_requested = nsamples_requested
        self.filename = filename
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
            self.statusUpdated.emit('Snapshot Complete: %d samples saved to %s' %
                (nsamples_actual, self.filename))
            self.finished.emit()    # wait, why is this necessary to reset to dialog?
        except ex.StateChangeError:
            self.statusUpdated.emit('Caught StateChangeError')
        except ex.NoResponseError:
            self.statusUpdated.emit('Control Command got no response')
        except socket.error:
            self.statusUpdated.emit('Socket error: Could not connect to daemon.')
        except tuple(ex.ERROR_DICT.values()) as e:
            self.statusUpdated.emit('Error: %s' % e)

