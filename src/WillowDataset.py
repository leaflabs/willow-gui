import numpy as np
from scipy import signal as dsp

import h5py

from PyQt4 import QtCore

import config
if not config.initialized:
    config.updateAttributes(config.loadJSON())

import sharedmem


# general parameters
NCHAN = 1024
NCHIPS = 32
SAMPLE_RATE = 3e4
MS_PER_SEC = 1000
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


class WillowImportError(Exception):
    pass

class WillowDataset(QtCore.QObject):
    """
    Willow Dataset Container Class
    Common format for passing data between import processes, plot windows, etc.
    """

    def __init__(self, filename):
        QtCore.QObject.__init__(self)

        self.filename = filename
        self.fileObject = h5py.File(self.filename, 'r')
        self.dset = self.fileObject['channel_data']
        self.isSnapshot = self.fileObject.attrs['ph_flags'][0] & (1 << 6)
        self.nsamples, self.nchan = self.dset.shape
        self.time_ms = np.arange(self.nsamples)*MS_PER_SEC/SAMPLE_RATE
        self.timeMin = np.min(self.time_ms)
        self.timeMax = np.max(self.time_ms)
        self.boardID = self.fileObject.attrs['board_id'][0]
        if self.isSnapshot:
            self.cookie = None
        else:
            self.cookie = self.fileObject.attrs['experiment_cookie'][0]
        chipAliveMask = self.fileObject['chip_live'][0]
        self.chipList = [i for i in range(NCHIPS) if (chipAliveMask & (0x1 << i))]

        self.isImported = False

        self.ncpu = sharedmem.cpu_count()

        self.slice_nsamples = 0

        self.slice_activity = sharedmem.empty(NCHAN, dtype=np.float32)

    def importData(self):
        self.data_raw = self.dset[:].transpose()
        self.data_uv = (np.array(self.data_raw, dtype=np.float)-2**15)*MICROVOLTS_PER_COUNT
        self.dataMin = np.min(self.data_uv)
        self.dataMax = np.max(self.data_uv)
        self.limits = [self.timeMin, self.timeMax, self.dataMin, self.dataMax]
        self.isImported = True

    def importSlice(self, s0, s1):
        # s0, s1 are the first and last sample indices of the slice
        nsamps = s1 - s0
        nchans = self.dset.shape[1]
        # cast to float, center on zero (subtract 2**16/2 = 2**15), and convert to microvolts
        self.slice_uv = np.asarray(((self.dset[s0:s1,:].astype(np.float32)-2**15)*MICROVOLTS_PER_COUNT).transpose())
        self.slice_s0 = s0
        self.slice_s1 = s1
        if (s1 - s0) != self.slice_nsamples:
            self.slice_nsamples = s1 - s0
            self.slice_filtered = sharedmem.empty((NCHAN, self.slice_nsamples), dtype=np.float32)
        self.slice_min = np.min(self.slice_uv)
        self.slice_max = np.max(self.slice_uv)

    def filterSlice(self, chans):
        self.slice_filtered[chans] = dsp.lfilter(FILTER_B, FILTER_A, self.slice_uv[chans], axis=1)

    def filterAndCalculateActivitySlice(self):
        with sharedmem.MapReduce() as pool:
            nchan = self.slice_uv.shape[0] // self.ncpu
            def work(i):
                chans = slice(i * nchan, (i + 1) * nchan)
                self.slice_filtered[chans] = dsp.lfilter(FILTER_B, FILTER_A, self.slice_uv[chans], axis=1)
                threshold = np.broadcast_to(
                    np.median(np.abs(self.slice_filtered[chans]), axis=1)*THRESH_SCALE,
                    (self.slice_nsamples, nchan)).transpose()
                self.slice_activity[chans] = np.sum(
                    (self.slice_filtered[chans] < threshold), axis=1) * ACTIVITY_SCALE / float(self.slice_nsamples)
            pool.map(work, range(0, self.ncpu))

    def applyCalibration(self, calibrationFile):
        self.calibrationFile = calibrationFile
        self.impedance = np.load(str(self.calibrationFile))
        self.data_cal = np.zeros((NCHAN, self.nsamples), dtype='float')
        for (i, imp) in enumerate(self.impedance):
            print i
            if imp>0:
                self.data_cal[i,:] = self.data_uv[i,:]*imp
            # else just leave it at zero
