from PyQt4 import QtCore, QtGui
import sys, os, h5py, time, datetime
import numpy as np
import hwif
from WillowDataset import WillowDataset

import config
sys.path.append(os.path.join(config.daemonDir, 'util'))
from daemon_control import *

FFT_INDEX_1KHZ = 500

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
        dataset = WillowDataset(tmpSnapshotFilename, -1)
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

    def allChipsRoutine(self):
        dt = datetime.datetime.fromtimestamp(time.time())
        strtime = '%04d%02d%02d-%02d%02d%02d' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        self.impedanceMeasurements = np.zeros(1024)
        # start streaming
        self.progressUpdated.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Starting streaming..')
        hwif.startStreaming_boardsamples()
        self.progressUpdated.emit(1)
        # main loop
        self.progressUpdated.emit(0)
        self.maxChanged.emit(32)
        self.textChanged.emit('Testing all chips...')
        for chan in range(32):
            if not self.isTerminated:
                self.progressUpdated.emit(chan)
            hwif.enableZCheck(chan, self.capscale) 
            tmpSnapshotFilename = os.path.abspath('../tmp/tmpSnapshot%02d.h5' % chan)
            hwif.takeSnapshot(self.nsamples, tmpSnapshotFilename) # alreadyStreaming branch
            snapshotDataset = self.importSnapshot(tmpSnapshotFilename)
            impedance = self.analyzeSnapshot_allChipsOneChan(snapshotDataset, chan)
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
        # save result and post message
        impedanceFilename = os.path.abspath('../cal/impedance_%s.npy' % strtime)
        np.save(impedanceFilename, self.impedanceMeasurements)
        self.msgPosted.emit('Impedance measurements saved to %s' % impedanceFilename)
        if self.plot:
            self.dataReady.emit(self.impedanceMeasurements)


    def oneChannelRoutine(self):
        # start streaming
        self.progressUpdated.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Starting streaming..')
        hwif.startStreaming_boardsamples()
        self.progressUpdated.emit(1)
        # enable ZCheck registers
        self.progressUpdated.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Enabling Intan impedance check..')
        hwif.enableZCheck(self.absChan % 32, self.capscale) 
        self.progressUpdated.emit(1)
        # take snapshot
        self.progressUpdated.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Taking snapshot..')
        tmpSnapshotFilename = os.path.abspath('../tmp/tmpSnapshot.h5')
        hwif.takeSnapshot(self.nsamples, tmpSnapshotFilename) # alreadyStreaming branch
        self.progressUpdated.emit(1)
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
        # import snapshot
        self.progressUpdated.emit(0)
        self.maxChanged.emit(self.nsamples)
        self.textChanged.emit('Importing snapshot..')
        snapshotData = self.importSnapshot(tmpSnapshotFilename, emit=True)
        self.progressUpdated.emit(self.nsamples)
        # analyze snapshot
        self.progressUpdated.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Analyzing snapshot..')
        impedance = self.analyzeSnapshot_oneChannel(snapshotData, self.absChan)
        self.progressUpdated.emit(1)
        if impedance > 0:
            self.msgPosted.emit('Impedance Result for Channel %d: %10.2f' % (self.absChan, impedance))
        else:
            self.msgPosted.emit('Error: Chip %d is not alive, cannot measure impedance.' % (self.absChan//32))

    def run(self):
        try:
            if hwif.isRecording() or hwif.isStreaming():
                self.msgPosted.emit('ImpedanceThread: Cannot check impedance while recording or streaming')
            if self.params['routine'] == 0:
                self.plot = self.params['plot']
                self.allChipsRoutine()
            elif self.params['routine'] == 1:
                self.absChan = self.params['channel']
                self.oneChannelRoutine()
        except hwif.StateChangeError:
            self.msgPosted.emit('Caught StateChangeError')
        except hwif.hwifError as e:
            self.msgPosted.emit(e.message)
        finally:
            self.finished.emit()

