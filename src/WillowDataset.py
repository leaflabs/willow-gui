import numpy as np
from scipy import signal as dsp
import multiprocessing as mp
import h5py
from PyQt4 import QtCore

import config
if not config.initialized:
    config.updateAttributes(config.loadJSON())


# general parameters
NCHAN = 1024
NCHIPS = 32
SAMPLE_RATE = 3e4
MS_PER_SEC = 1000
MAX_NSAMPLES = config.importLimit_GB*5e5
MICROVOLTS_PER_COUNT = 0.195

# filter parameters
FILT_LOWCUT_HZ = 100.
FILT_HIGHCUT_HZ = 9500.
FILT_ORDER = 5
NYQUIST_RATE = SAMPLE_RATE / 2.
FILTER_B, FILTER_A = dsp.butter(FILT_ORDER,
                        [FILT_LOWCUT_HZ/NYQUIST_RATE, FILT_HIGHCUT_HZ/NYQUIST_RATE],
                        btype='band')

# activity calculation parameters
THRESH_SCALE = -4.5/0.6745 # from JP Kinney
ACTIVITY_SCALE = 100. # arbitrary scaling to get activity approximately normalized to [0,1]

def filterAndCalculateActivity(data, wpipe):
    # works on uv data
    nchan, nsamp = data.shape
    filteredData = dsp.lfilter(FILTER_B, FILTER_A, data, axis=1)
    wpipe.send(filteredData)
    threshold = np.median(np.abs(filteredData), axis=1)*THRESH_SCALE
    activity = np.zeros(nchan)
    for i in range(nchan):
        activity[i] = np.sum((filteredData[i,:] < threshold[i])) * ACTIVITY_SCALE / float(nsamp)
    wpipe.send(activity)


# the following two functions facilitate multiprocessing for the activity calc

def MPGenerator(dataSlice, nproc):
    nchan = dataSlice.shape[0]
    nchanPerProc = nchan // nproc
    splitter = np.arange(1,nproc) * nchanPerProc
    for subSlice in np.split(dataSlice, splitter):
        yield subSlice

class PipedProcess(mp.Process):
    def __init__(self, rpipe, **kwargs):
        mp.Process.__init__(self, **kwargs)
        self.rpipe = rpipe


class WillowImportError(Exception):
    pass

class WillowDataset(QtCore.QObject):
    """
    Willow Dataset Container Class
    Common format for passing data between import processes, plot windows, etc.
    """

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
                self.nsamples = len(self.dset)//NCHAN
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
        self.time_ms = np.arange(self.sampleRange[0], self.sampleRange[1]+1)*MS_PER_SEC/SAMPLE_RATE
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
        self.chipList = [i for i in range(NCHIPS) if (chipAliveMask & (0x1 << i))]
        self.isImported = False

        self.ncpu = mp.cpu_count()

    def importData(self):
        if self.isOldLayout:
            if self.nsamples > MAX_NSAMPLES:
                raise WillowImportError
            self.data_raw = np.zeros((NCHAN,self.nsamples), dtype='uint16')
            for i in range(self.nsamples):
                self.data_raw[:,i] = self.dset[self.sampleRange[0]+i][3][:NCHAN]
        else:
            self.data_raw = np.array(self.fileObject['channel_data']
                            [self.sampleRange[0]*NCHAN:(self.sampleRange[1]+1)*NCHAN],
                            dtype='uint16').reshape((self.nsamples, NCHAN)).transpose()
        self.data_uv = (np.array(self.data_raw, dtype='float')-2**15)*MICROVOLTS_PER_COUNT
        self.dataMin = np.min(self.data_uv)
        self.dataMax = np.max(self.data_uv)
        self.limits = [self.timeMin, self.timeMax, self.dataMin, self.dataMax]
        self.isImported = True

    def importSlice(self, s0, s1):
        # s0, s1 are the first and last sample indices of the slice
        self.slice_raw = np.array(self.fileObject['channel_data'][s0*NCHAN:s1*NCHAN],
                                    dtype='uint16').reshape((s1-s0, NCHAN)).transpose()
        # cast to float, center on zero (subtract 2**16/2 = 2**15), and convert to microvolts
        self.slice_uv = (np.array(self.slice_raw, dtype='float')-2**15)*MICROVOLTS_PER_COUNT
        self.slice_s0 = s0
        self.slice_s1 = s1
        self.slice_nsamples = s1 - s0
        self.slice_min = np.min(self.slice_uv)
        self.slice_max = np.max(self.slice_uv)

    def filterSlice(self):
        self.slice_filtered = dsp.lfilter(FILTER_B, FILTER_A, self.slice_uv, axis=1)

    def filterAndCalculateActivitySlice(self):
        # (multi) processing
        self.slice_activity = np.zeros(NCHAN)
        self.slice_filtered = np.zeros((NCHAN, self.slice_nsamples))
        procs = []
        for subSlice in MPGenerator(self.slice_uv, self.ncpu):
            rpipe, wpipe = mp.Pipe()
            procs.append(PipedProcess(rpipe, target=filterAndCalculateActivity,
                            args=(subSlice, wpipe)))
        for pp in procs: pp.start()
        cursor = 0
        for i, pp in enumerate(procs):
            filteredData_subslice = pp.rpipe.recv()
            pp.join()
            activity_subslice = pp.rpipe.recv()
            nchan_subslice = activity_subslice.shape[0]
            self.slice_activity[cursor:(cursor+nchan_subslice)] = activity_subslice
            self.slice_filtered[cursor:(cursor+nchan_subslice),:] = filteredData_subslice
            cursor += nchan_subslice

    def applyCalibration(self, calibrationFile):
        self.calibrationFile = calibrationFile
        self.impedance = np.load(str(self.calibrationFile))
        self.data_cal = np.zeros((NCHAN, self.nsamples), dtype='float')
        for (i, imp) in enumerate(self.impedance):
            print i
            if imp>0:
                self.data_cal[i,:] = self.data_uv[i,:]*imp
            # else just leave it at zero

