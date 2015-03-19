from PyQt4 import QtCore, QtGui
import sys, os, h5py, time, datetime, socket
import numpy as np
import hwif

import config

class TransferThread(QtCore.QThread):

    statusUpdated = QtCore.pyqtSignal(str)

    def __init__(self, params):
        QtCore.QThread.__init__(self)
        self.sampleRange = params['sampleRange']    # none if 'entire experiment'
        filename = params['filename']               # none if 'rename'
        if filename:
            self.filename = filename
            self.rename = False
        else:
            self.filename = os.path.join(config.dataDir, 'tmp_transfer.h5')
            self.rename = True
        self.isTerminated = False

    def handleCancel(self):
        """
        This is required to prevent the race condition between QProgressDialog
        and this thread. self.isTerminated is checked before emission of valueChanged.
        """
        self.isTerminated = True
        self.terminate()

    def isSampleRangeValid(self):
        if isinstance(self.sampleRange, list) and (len(self.sampleRange)==2):
            if (self.sampleRange[1]>self.sampleRange[0]) and (self.sampleRange[0]>=0):
                return True
            else:
                return False
        elif self.sampleRange==None:
            return True
        else:
            return False

    def isFilenameValid(self):
        if os.path.exists(os.path.dirname(self.filename)):
            return True
        else:
            return False

    def run(self):
        if not self.isSampleRangeValid():
            self.statusUpdated.emit('sampleRange not valid: %s' % repr(self.sampleRange))
            return
        if not self.isFilenameValid():
            self.statusUpdated.emit('Target filename not valid: %s' % repr(self.filename))
            return
        try:
            if (self.sampleRange == None) and (hwif.getDaqBSI() == 0):
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
                    self.filename = os.path.join(config.dataDir, 'experiment_C%s.h5' % strtime)
                    os.rename(tmpFilename, self.filename)
                self.statusUpdated.emit('Transfer complete: %s' % self.filename)
        except hwif.StateChangeError:
            self.statusUpdated.emit('Caught StateChangeError')
        except hwif.hwifError as e:
            self.statusUpdated.emit(e.message)
