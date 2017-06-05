from PyQt4 import QtCore, QtGui
import os, h5py, time, datetime
import subprocess
import numpy as np

import config

class TransferThread(QtCore.QThread):

    statusUpdated = QtCore.pyqtSignal(str)

    def __init__(self, params):
        QtCore.QThread.__init__(self)
        self.deviceFile = params['source']
        self.sampleRange = params['sampleRange']    # none if 'entire experiment'
        filename = params['filename']               # none if 'rename'
        if filename:
            self.targetFile = filename
            self.rename = False
        else:
            self.targetFile = os.path.join(config.dataDir, 'tmp_transfer.h5')
            self.rename = True
        self.isTerminated = False

    def handleCancel(self):
        """
        This is required to prevent the race condition between QProgressDialog
        and this thread. self.isTerminated is checked before emission of valueChanged.
        """
        self.isTerminated = True

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
        if os.path.exists(os.path.dirname(self.targetFile)):
            return True
        else:
            return False

    def run(self):
        if not self.isSampleRangeValid():
            self.statusUpdated.emit('sampleRange not valid: %s' % repr(self.sampleRange))
            return
        if not self.isFilenameValid():
            self.statusUpdated.emit('Target filename not valid: %s' % repr(self.targetFile))
            return

        sata2hdf5_path = os.path.join(config.daemonDir, 'build/sata2hdf5')
        if self.sampleRange:
            offset = str(self.sampleRange[0])
            count = str(self.sampleRange[1] - self.sampleRange[0]) # treat sampleRange as a half-open set
            callList = [sata2hdf5_path, '-o', offset, '-c', count, self.deviceFile, self.targetFile]
        else: # entire experiment
            callList = [sata2hdf5_path, self.deviceFile, self.targetFile]

        po = subprocess.Popen(callList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.statusUpdated.emit('Transfer begun.')

        while True:
            if (po.poll() != None):
                break
            if self.isTerminated:
                po.kill()
                self.statusUpdated.emit('Transfer canceled.')
                return
            time.sleep(0.03)

        if po.returncode == 0:
            if self.rename:
                tmpFilename = self.targetFile
                f = h5py.File(tmpFilename)
                timestamp = f.attrs['experiment_cookie'][0]
                dt = datetime.datetime.fromtimestamp(timestamp)
                strtime = '%04d%02d%02d-%02d%02d%02d' % (dt.year, dt.month, dt.day, dt.hour,
                    dt.minute, dt.second)
                self.targetFile = os.path.join(config.dataDir, 'experiment_C%s.h5' % strtime)
                os.rename(tmpFilename, self.targetFile)
            self.statusUpdated.emit('Transfer complete. Generated datafile: %s' % self.targetFile)
        elif po.returncode == 3:
            self.statusUpdated.emit('ERROR: Transfer failed; no Willow data found on block device %s'
                                        % self.deviceFile)
        else:
            self.statusUpdated.emit('ERROR: Transfer failed with return code %d' % po.returncode)
