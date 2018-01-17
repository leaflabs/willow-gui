import numpy as np
from scipy import signal as dsp
import sharedmem
import h5py

from const import *

class WillowImportError(Exception):
    pass

class WillowProcessingError(Exception):
    pass

class WillowDataset():
    """
    Willow Dataset Container Class
    Common format for passing data between import processes, plot windows, etc.
    """
    def __init__(self, filename):

        self.filename = filename
        self.fileObject = h5py.File(self.filename)
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
        self.sliceImported = False
        self.sliceBeenFiltered = False

        self.ncpu = sharedmem.cpu_count()

        self.slice_nsamples = 0
        self.slice_nchans = None

    def importData(self):
        self.data_raw = self.dset[:].transpose()
        self.data_uv = (np.array(self.data_raw, dtype=np.float)-2**15)*MICROVOLTS_PER_COUNT
        self.dataMin = np.min(self.data_uv)
        self.dataMax = np.max(self.data_uv)
        self.limits = [self.timeMin, self.timeMax, self.dataMin, self.dataMax]
        self.isImported = True

    def importSlice(self, s0=0, s1=None, chans=np.arange(NCHAN)):
        # s0, s1 are the first and last sample indices of the slice
        if s1 is None:
            s1 = self.nsamples
        chans.sort()    # numpy requires that indexing elements be sorted
        self.chan2slice_idx = {chan: i for i, chan in enumerate(chans)}

        # cast to float, center on zero (subtract 2**16/2 = 2**15), and convert to microvolts
        self.slice_uv = np.asarray(((self.dset[s0:s1,chans].astype(np.float32)-2**15)*MICROVOLTS_PER_COUNT).transpose())
        self.slice_s0 = s0
        self.slice_s1 = s1
        if (s1 - s0) != self.slice_nsamples:
            self.slice_nsamples = s1 - s0
            self.slice_filtered = sharedmem.empty((len(chans), self.slice_nsamples),
                                                  dtype=np.float32)
        if len(chans) != self.slice_nchans:
            self.slice_nchans = len(chans)
            self.slice_activity = sharedmem.empty(self.slice_nchans, dtype=np.float32)
        self.slice_min = np.min(self.slice_uv)
        self.slice_max = np.max(self.slice_uv)
        self.sliceImported = True

    def filterSlice(self):
        if not self.sliceImported:
            raise WillowProcessingError('Import slice before filtering it.')
        self.slice_filtered = dsp.lfilter(FILTER_B, FILTER_A, self.slice_uv, axis=1)
        self.slice_filtered_min = np.min(self.slice_filtered)
        self.slice_filtered_max = np.max(self.slice_filtered)
        self.sliceBeenFiltered = True

    def filterAndCalculateActivitySlice(self):
        if not self.sliceImported:
            raise WillowProcessingError('Import slice before filtering it.')
        with sharedmem.MapReduce() as pool:
            nchan = self.slice_nchans // self.ncpu
            def work(i):
                chans = slice(i * nchan, (i + 1) * nchan)
                self.slice_filtered[chans] = dsp.lfilter(FILTER_B, FILTER_A, self.slice_uv[chans], axis=1)
                threshold = np.broadcast_to(
                    np.median(np.abs(self.slice_filtered[chans]), axis=1)*THRESH_SCALE,
                    (self.slice_nsamples, nchan)).transpose()
                self.slice_activity[chans] = np.sum(
                    (self.slice_filtered[chans] < threshold), axis=1) * ACTIVITY_SCALE / float(self.slice_nsamples)
            pool.map(work, range(0, self.ncpu))
        self.sliceBeenFiltered = True

    def detectSpikesSlice(self, thresh=None):
        if not self.sliceImported:
            raise WillowProcessingError('Import slice before detecting spikes in it.')
        if not self.sliceBeenFiltered:
            # default to multiprocessing filtering option, on the assumption
            # that it's generally faster
            self.filterAndCalculateActivitySlice()
        self.spikes = {}
        nslice_chans = self.slice_filtered.shape[0]
        for slice_chan in xrange(nslice_chans):
            chan_data = self.slice_filtered[slice_chan,:]
            if thresh is None:
                # constants from JP Kinney
                thresh = -4.5 * np.median(np.abs(chan_data))/0.6745
            indices, nspikes = self.spikeThreshold(chan_data, thresh)
            times = self.time_ms[indices]
            spike_data = {'thresh': thresh, 'indices': indices,
                          'nspikes': nspikes, 'times': times}
            self.spikes[slice_chan] = spike_data

    def spikeThreshold(self, indata, thresh):
        # helper function: finds the place where a possible spike is maximal
        def analyzeSpike(spike_data):
            numpified = np.array(spike_data)
            maxind = np.argmax(numpified[:,1])
            return spike_data[maxind][0]

        # next two lines make the algorithm agnostic of polarity (pos/neg)
        polarity = -1. if (thresh < 0) else 1
        thresh = abs(thresh)
        # init buffers and counters
        recording = False
        spike_data = []
        stats = []
        nspikes = 0
        # run over the data
        for i, samp in enumerate(polarity*indata):
            if not recording:
                if samp >= thresh:
                    spike_data.append((i, samp))
                    recording = True
            else:
                if samp < thresh:
                    stats.append(analyzeSpike(spike_data))
                    nspikes += 1
                    spike_data = []
                    recording = False
                else:
                    spike_data.append((i, samp))

        return stats, nspikes

    def applyCalibration(self, calibrationFile):
        self.calibrationFile = calibrationFile
        self.impedance = np.load(str(self.calibrationFile))
        self.data_cal = np.zeros((NCHAN, self.nsamples), dtype='float')
        for (i, imp) in enumerate(self.impedance):
            print i
            if imp>0:
                self.data_cal[i,:] = self.data_uv[i,:]*imp
            # else just leave it at zero
