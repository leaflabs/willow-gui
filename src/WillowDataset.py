import numpy as np
import h5py
from PyQt4 import QtCore

class WillowDataset(QtCore.QObject):
    """
    Willow Dataset Container Class
    Common format for passing data between import processes, plot windows, etc.
    Given a ndarray(dtype='uint16') in counts, the constructor converts and stores microvolts
        (self.uv) and a time coordinate in milliseconds (self.ms)
    """

    progressUpdated = QtCore.pyqtSignal(int)

    def __init__(self, filename, sampleRange):
        QtCore.QObject.__init__(self)
        self.filename = filename
        self.fileObject = h5py.File(self.filename)
        self.dset = self.fileObject['wired-dataset']

        # determine type based on header flag
        if (self.dset[0][0] & (1<<6)):
            self.type = 'snapshot'
        else:
            self.type = 'experiment'

        # define self.sampleRange and related temporal data
        if sampleRange==-1:
            self.nsamples = len(self.dset)
            self.sampleRange = [0, self.nsamples-1]
        else:
            self.sampleRange = sampleRange
            self.nsamples = self.sampleRange[1] - self.sampleRange[0] + 1
            dsetMin = int(self.dset[0][1])
            dsetMax = int(self.dset[-1][1])
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
        self.boardID = self.dset.attrs['board_id'][0]
        if self.type=='experiment':
            self.cookie = self.dset.attrs['experiment_cookie'][0]
        chipAliveMask = self.dset[0][2] # TODO remove this after debugging
        self.chipList = [i for i in range(32) if (chipAliveMask & (0x1 << i))]
        self.isImported = False

    def importData(self):
        if self.nsamples > 5e6:
            raise Exception('Data range exceeds memory limit of 5 million samples')
        self.data_raw = np.zeros((1024,self.nsamples), dtype='uint16')
        for i in range(self.nsamples):
            self.data_raw[:,i] = self.dset[self.sampleRange[0]+i][3][:1024]
            if (i%1000==0):
                self.progressUpdated.emit(i)
        self.progressUpdated.emit(self.nsamples)
        self.data_uv = (np.array(self.data_raw, dtype='float')-2**15)*0.2
        self.dataMin = np.min(self.data_uv)
        self.dataMax = np.max(self.data_uv)
        self.limits = [self.timeMin, self.timeMax, self.dataMin, self.dataMax]

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
    dataset = WillowDataset('/home/chrono/sng/data/tmpSnapshot.h5', -1)
    dataset.importData()
