import numpy as np
import h5py
from PyQt4 import QtCore

import config
if not config.initialized:
    config.updateAttributes(config.loadJSON())

MAX_NSAMPLES = config.importLimit_GB*5e5
MICROVOLTS_PER_COUNT = 0.195

class WillowImportError(Exception):
    pass

class WillowDataset(QtCore.QObject):
    """
    Willow Dataset Container Class
    Common format for passing data between import processes, plot windows, etc.
    """

    progressUpdated = QtCore.pyqtSignal(int)

    def __init__(self, filename, sampleRange):
        QtCore.QObject.__init__(self)
        self.filename = filename
        self.fileObject = h5py.File(self.filename)
        # the following test allows for backward-compatibility
        if 'wired-dataset' in self.fileObject:
            self.isOldLayout = True
            self.dset = self.fileObject['wired-dataset']
            # determine type based on header flag
            if (self.dset[0][0] & (1<<6)):
                self.type = 'snapshot'
            else:
                self.type = 'experiment'
        else:
            self.isOldLayout = False 
            self.dset = self.fileObject['channel_data']
            # determine type based on header flag
            if self.fileObject['ph_flags'][0] & (1<<6):
                self.type = 'snapshot'
            else:
                self.type = 'experiment'

        # define self.sampleRange and related temporal data
        if sampleRange==-1:
            if self.isOldLayout:
                self.nsamples = len(self.dset)
            else:
                self.nsamples = len(self.dset)//1024
            self.sampleRange = [0, self.nsamples-1]
        else:
            self.sampleRange = sampleRange
            self.nsamples = self.sampleRange[1] - self.sampleRange[0] + 1
            if self.isOldLayout:
                dsetMin = int(self.dset[0][1])
                dsetMax = int(self.dset[-1][1])
            else:
                dsetMin = int(self.fileObject['sample_index'][0])
                dsetMax = int(self.fileObject['sample_index'][-1])
            if self.type=='snapshot':
                # need to normalize because snapshots have random offsets
                dsetMax -= dsetMin
                dsetMin = 0
            if (self.sampleRange[0] < dsetMin) or (self.sampleRange[1] > dsetMax):
                raise IndexError('Error: sampleRange [%d, %d] out of range for dset: [%d, %d]'
                    % tuple(self.sampleRange+[dsetMin,dsetMax]))
        self.time_ms = np.arange(self.sampleRange[0], self.sampleRange[1]+1)/30.
        self.timeMin = np.min(self.time_ms)
        self.timeMax = np.max(self.time_ms)

        # other metadata
        if self.isOldLayout:
            self.boardID = self.dset.attrs['board_id'][0]
            if self.type=='experiment':
                self.cookie = self.dset.attrs['experiment_cookie'][0]
            else:
                self.cookie = None
            chipAliveMask = self.dset[0][2]
        else:
            self.boardID = self.fileObject.attrs['board_id'][0]
            if self.type=='experiment':
                self.cookie = self.fileObject.attrs['experiment_cookie'][0]
            else:
                self.cookie = None
            chipAliveMask = self.fileObject['chip_live'][0]
        self.chipList = [i for i in range(32) if (chipAliveMask & (0x1 << i))]
        self.isImported = False

    def importData(self):
        if self.isOldLayout:
            if self.nsamples > MAX_NSAMPLES:
                raise WillowImportError
            self.data_raw = np.zeros((1024,self.nsamples), dtype='uint16')
            for i in range(self.nsamples):
                self.data_raw[:,i] = self.dset[self.sampleRange[0]+i][3][:1024]
                if (i%1000==0):
                    self.progressUpdated.emit(i)
        else:
            self.progressUpdated.emit(0)
            self.data_raw = np.array(self.fileObject['channel_data'][self.sampleRange[0]*1024:(self.sampleRange[1]+1)*1024], dtype='uint16').reshape((self.nsamples, 1024)).transpose()
        self.progressUpdated.emit(self.nsamples)
        self.data_uv = (np.array(self.data_raw, dtype='float')-2**15)*MICROVOLTS_PER_COUNT
        self.dataMin = np.min(self.data_uv)
        self.dataMax = np.max(self.data_uv)
        self.limits = [self.timeMin, self.timeMax, self.dataMin, self.dataMax]
        self.isImported = True

    def filterData(self):
        pass # TODO

    def applyCalibration(self, calibrationFile):
        self.calibrationFile = calibrationFile
        self.impedance = np.load(str(self.calibrationFile))
        self.data_cal = np.zeros((1024, self.nsamples), dtype='float')
        for (i, imp) in enumerate(self.impedance):
            print i
            if imp>0:
                self.data_cal[i,:] = self.data_uv[i,:]*imp
            # else just leave it at zero

if __name__=='__main__':
    dataset = WillowDataset('/home/chrono/tmp/snapshot.h5', -1)
    #dataset.importData()
