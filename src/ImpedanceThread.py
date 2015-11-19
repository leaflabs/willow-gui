from PyQt4 import QtCore, QtGui
import sys, os, h5py, time, datetime
import numpy as np
import hwif
from WillowDataset import WillowDataset

import config
sys.path.append(os.path.join(config.daemonDir, 'util'))
from daemon_control import *

FFT_INDEX_1KHZ = 500

class SnapshotLoadError(Exception):
    """ 
    For reporting that a snapshot that we try to access is not actually saved on disk.
    """
    pass

def saveImpedance_hdf5(data, timestamp, filename):
    f = h5py.File(filename, 'w-') # create file, fail if exists
    dset = f.create_dataset('impedanceMeasurements', data=data)
    dset.attrs['timestamp'] = timestamp
    f.close()
    
class ImpedanceThread(QtCore.QThread):

    progressUpdated = QtCore.pyqtSignal(int)
    maxChanged = QtCore.pyqtSignal(int)
    textChanged = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    msgPosted = QtCore.pyqtSignal(str)
    dataReady = QtCore.pyqtSignal(object)

    def __init__(self, params):
        QtCore.QThread.__init__(self)
        self.params = params
        self.capscale = 0b00        # hardcoded for now
        self.capcurrent = 0.38e-9   # depends on capscale, hardcoded for now
        self.nsamples = 15000       # hardcoded for now
        self.isTerminated = False

    def handleCancel(self):
        """
        This is required to prevent the race condition between QProgressDialog
        and this thread. self.isTerminated is checked before emission of progressUpdated.
        """
        self.isTerminated = True
        try:
            hwif.disableZCheck()
            hwif.stopStreaming()
        except hwif.AlreadyError:
            pass
        except hwif.StateChangeError:
            self.msgPosted.emit('Caught StateChangeError')
        except hwif.hwifError as e:
            self.msgPosted.emit(e.message)
        finally:
            self.finished.emit()
            self.terminate()

    def fft2volts(self, amplitude):
        """
        Converts a complex FFT amplitude to its corresponding (real) voltage amplitude
        The conversion factor between ADC counts and volts is 0.195 microvolts per count.
        """
        return abs(amplitude*2/self.nsamples) * 0.195e-6

    def importSnapshot(self, tmpSnapshotFilename, emit=False):
        # do incomplete snapshots ever get saved if UDP packets are dropped? yes.
        # TODO: implement a check for file size, rather than just checking that the file exists
        if not os.path.isfile(tmpSnapshotFilename):
            raise SnapshotLoadError
        try:
            dataset = WillowDataset(tmpSnapshotFilename, -1)
        # a ValueError raised by python if saved is improperly formatted
        # (this can happen due to a dropped UDP packet and possibly due to
        # other reasons)
        except ValueError:
            raise SnapshotLoadError
        if emit:
            dataset.progressUpdated.connect(self.progressUpdated)
        dataset.importData()
        return dataset

    def analyzeSnapshot_allChipsOneChan(self, snapshotDataset, chan):
        for chip in range(32):
            absChan = chip*32+chan
            if chip in snapshotDataset.chipList:
                fft = np.fft.rfft(snapshotDataset.data_raw[absChan, :])
                volts = self.fft2volts(fft[FFT_INDEX_1KHZ])
                self.impedanceMeasurements[absChan] = volts/self.capcurrent # Z=V/I
            else:
                self.impedanceMeasurements[absChan] = -1

    def analyzeSnapshot_oneChannel(self, snapshotDataset, absChan):
        chip = absChan // 32
        if chip in snapshotDataset.chipList:
            fft = np.fft.rfft(snapshotDataset.data_raw[absChan, :])
            volts = self.fft2volts(fft[FFT_INDEX_1KHZ])
            return volts/self.capcurrent
        else:
            return -1

    # these are attempts to reduce boilerplate for (single/all) channel z tests
    # could still use some cleanup, maybe
    def startStreaming(self):
        self.progressUpdated.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Starting streaming..')
        hwif.startStreaming_boardsamples()
        self.progressUpdated.emit(1)
    
    def channelSnapshotRoutine(self, chan, singleChannel=True):
        # enable ZCheck registers
        hwif.enableZCheck(chan, self.capscale)
        self.textChanged.emit('Analyzing channel {0}..'.format(chan))
        # take snapshot
        tmpSnapshotFilename = os.path.abspath('../tmp/tmpSnapshot.h5') if singleChannel else os.path.abspath('../tmp/tmpSnapshot%02d.h5' % chan)
        hwif.takeSnapshot(self.nsamples, tmpSnapshotFilename) # alreadyStreaming branch
        # import snapshot
        try:
            snapshotDataset = self.importSnapshot(tmpSnapshotFilename)
        except SnapshotLoadError:
            # only possible exception for now is SnapshotLoadError
            raise
        # analyze snapshot
        impedance = self.analyzeSnapshot_oneChannel(snapshotDataset, self.absChan) if singleChannel else self.analyzeSnapshot_allChipsOneChan(snapshotDataset, chan)
        return impedance
            
    def stopZCheck(self):
        # disable ZCheck registers
        self.progressUpdated.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Disabling Intan impedance check..')
        hwif.disableZCheck()
        self.progressUpdated.emit(1)
        # stop streaming
        self.progressUpdated.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Turning off streaming..')
        hwif.stopStreaming()
        self.progressUpdated.emit(1)
        
    def allChipsRoutine(self):
        timestamp  = time.time()
        dt = datetime.datetime.fromtimestamp(timestamp)
        strtime = '%04d%02d%02d-%02d%02d%02d' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        self.impedanceMeasurements = np.zeros(1024)
        self.startStreaming()
        # main loop
        self.progressUpdated.emit(0)
        self.maxChanged.emit(32)
        self.textChanged.emit('Testing all chips...')
        for chan in range(32):
            try:
                thisChanImpedance = self.channelSnapshotRoutine(chan, singleChannel=False)
            except SnapshotLoadError:
                self.msgPosted.emit('There was an error recording impedance from channel {0}. Trying again..'.format(chan))
                try:
                    thisChanImpedance = self.channelSnapshotRoutine(chan, singleChannel=False)
                except:
                    self.msgPosted.emit('Another error recording impedance from channel {0}. Giving up -- please check network configuration, cable connections, etc. if problem continues to persist.'.format(chan))
                    return
            if not self.isTerminated:
                self.progressUpdated.emit(chan+1)
        self.stopZCheck()
        # save result and post message
        impedanceFilename = os.path.abspath('../cal/impedance_%s.h5' % strtime)
        saveImpedance_hdf5(self.impedanceMeasurements, timestamp, impedanceFilename)
        self.msgPosted.emit('Impedance measurements saved to %s' % impedanceFilename)
        if self.plot:
            self.dataReady.emit(self.impedanceMeasurements)

    def oneChannelRoutine(self):
        self.startStreaming()
        self.progressUpdated.emit(0)
        self.maxChanged.emit(1)
        try:
            thisChanImpedance = self.channelSnapshotRoutine(self.absChan % 32, singleChannel=True)
        except:
            self.msgPosted.emit('There was an error recording impedance from channel {0}. Trying again..'.format(chan))
            try:
                thisChanImpedance = self.channelSnapshotRoutine(self.absChan % 32, singleChannel=True)
            except:
                self.msgPosted.emit('Another error recording impedance from channel {0}. Giving up -- please check network configuration if problem persists.'.format(chan))
        self.progressUpdated.emit(1)
        if thisChanImpedance > 0:
            self.msgPosted.emit('Impedance Result for Channel %d: %10.2f' % (self.absChan, thisChanImpedance))
        else:
            self.msgPosted.emit('Error: Chip %d is not alive, cannot measure impedance.' % (self.absChan//32))

        self.stopZCheck()

    def run(self):
        try:
            if not os.path.isdir('../tmp'):
                os.mkdir('../tmp')
            if self.params['routine'] == 0:
                self.plot = self.params['plot']
                self.msgPosted.emit('starting allChipsRoutine...')
                self.allChipsRoutine()
            elif self.params['routine'] == 1:
                self.absChan = self.params['channel']
                self.oneChannelRoutine()
        except hwif.StateChangeError:
            self.msgPosted.emit('Caught StateChangeError')
        except hwif.hwifError as e:
            self.msgPosted.emit(e.message)
        finally:
            try:
                hwif.stopStreaming()
            except (hwif.AlreadyError, hwif.hwifError):
                pass
            self.finished.emit()

