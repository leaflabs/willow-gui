from PyQt4 import QtCore, QtGui
import sys, os, h5py, time, datetime, socket
import numpy as np
import hwif

import config

class TransferThread(QtCore.QThread):

    statusUpdated = QtCore.pyqtSignal(str)

    def __init__(self, filename, sampleRange):
        super(TransferThread, self).__init__()
        if filename == -1:
            self.filename = os.path.join(config.dataDir, 'tmp_transfer.h5')
            self.rename = True
        else:
            self.filename = filename
            self.rename = False
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
        try:
            if (self.sampleRange == -1) and (hwif.getDaqBSI() == 0):
                self.statusUpdated.emit('Error: Could not transfer experiment because BSI is missing.')
                self.statusUpdated.emit('Please specify subset parameters in the Transfer Dialog and try again.')
            else:
                hwif.doTransfer(self.filename, self.sampleRange)
                if self.rename:
                    tmpFilename = self.filename
                    f = h5py.File(tmpFilename)
                    timestamp = f['wired-dataset'].attrs['experiment_cookie'][0]
                    dt = datetime.datetime.fromtimestamp(timestamp)
                    strtime = '%04d%02d%02d-%02d%02d%02d' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
                    filename = os.path.join(config.dataDir, 'experiment_%s.h5' % strtime)
                    os.rename(tmpFilename, filename)
                self.statusUpdated.emit('Transfer complete: %s' % self.filename)
        except hwif.StateChangeError:
            self.statusUpdated.emit('Caught StateChangeError')
        except hwif.hwifError as e:
            self.statusUpdated.emit(e.message)
