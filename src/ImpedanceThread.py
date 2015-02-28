from PyQt4 import QtCore, QtGui
import sys, os, h5py, time, datetime
import numpy as np
import hwif
from WillowDataset import WillowDataset

import config
sys.path.append(os.path.join(config.daemonDir, 'util'))
from daemon_control import *

# TODO !!! wrap all the hwif calls in exception handlers

FFT_INDEX_1KHZ = 500

class ImpedanceThread(QtCore.QThread):

    valueChanged = QtCore.pyqtSignal(int)
    maxChanged = QtCore.pyqtSignal(int)
    textChanged = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    statusUpdated = QtCore.pyqtSignal(str)

    def __init__(self, params):
        QtCore.QThread.__init__(self)
        self.params = params
        self.capscale = 0b00    # hardcoded for now
        self.nsamples = 15000   # hardcoded for now
        self.isTerminated = False

    def handleCancel(self):
        """
        This is required to prevent the race condition between QProgressDialog
        and this thread. self.isTerminated is checked before emission of valueChanged.
        """
        self.isTerminated = True
        hwif.disableZCheck()
        hwif.stopStreaming()
        self.terminate()

    def amp2volts(self, amplitude, nsamples):
        """
        Converts a complex FFT amplitude at 1KHz to a sinewave amplitude in volts
        (normal amplitude, not peak-to-peak). The conversion factor between ADC
        counts and volts is 0.195 microvolts per count.
        """
        return abs(amplitude * 2 / nsamples) * 0.195 * 10**-6

    def volts2impedance(self, volts, capacitorscale):
        """
        See pages 28 to 30 of the Intan RHD2000 Series datasheet.
        Formula for impedance:
            (impedance ohms) = (amplitude volts) / (current amps)
        The example given in the Intan datasheet is that with the 1.0pF capacitor
        selected (capacitorscale=1), a 1MOhm total impedance would result in a
        3.8mV signal amplitude.
        This conversion assumes:
          - 1kHz sine max amplitude DAC waveform
          - "normal" ADC and amplifier configuration
        """
        cap2current = {0: 0.38 * 10**-9,  # 0.1pF capacitor
                       1: 3.8 * 10**-9,   # 1.0pF capacitor
                       3: 38.0 * 10**-9}  # 10.0pF capacitor

        impedance = volts / cap2current[capacitorscale]

        return impedance    # always

    def importSnapshot(self, tmpSnapshotFilename, emit=False):
        dataset = WillowDataset(tmpSnapshotFilename, -1)
        dataset.importData()
        return dataset

    def analyzeSnapshot_allChips(self, snapshotDataset, chan):
        for chip in range(32):
            absChan = chip*32+chan
            if chip in snapshotDataset.chipList:
                fft = np.fft.rfft(snapshotDataset.data_raw[absChan, :])
                volts = self.amp2volts(fft[FFT_INDEX_1KHZ], self.nsamples)
                impedance = self.volts2impedance(volts, self.capscale)
                print 'Impedance: ', impedance
                self.impedanceMeasurements[absChan] = impedance
            else:
                print 'Impedance: ', -1
                self.impedanceMeasurements[absChan] = -1

    def analyzeSnapshot_oneChannel(self, snapshotData, absChan):
        fft = np.fft.rfft(snapshotData[absChan, :])
        volts = self.amp2volts(fft[FFT_INDEX_1KHZ], self.nsamples)
        return self.volts2impedance(volts, self.capscale)

    def allChipsRoutine(self):
        dt = datetime.datetime.fromtimestamp(time.time())
        strtime = '%04d%02d%02d-%02d%02d%02d' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        self.impedanceMeasurements = np.zeros(1024)
        # start streaming
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Starting streaming..')
        hwif.startStreaming_boardsamples()
        self.valueChanged.emit(1)
        # main loop
        self.valueChanged.emit(0)
        self.maxChanged.emit(32)
        self.textChanged.emit('Testing all chips...')
        for chan in range(32):
            if not self.isTerminated:
                self.valueChanged.emit(chan)
            # enable ZCheck registers
            hwif.enableZCheck(chan, self.capscale) 
            # take snapshot
            # eventually these can overwrite themselves, but for now i want to evaluate them
            tmpSnapshotFilename = os.path.abspath('../tmp/tmpSnapshot%02d.h5' % chan)
            hwif.takeSnapshot(self.nsamples, tmpSnapshotFilename) # alreadyStreaming branch
            # import snapshot
            snapshotDataset = self.importSnapshot(tmpSnapshotFilename)
            # analyze snapshot
            impedance = self.analyzeSnapshot_allChips(snapshotDataset, chan)
        # disable ZCheck registers
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Disabling Intan impedance check..')
        hwif.disableZCheck()
        self.valueChanged.emit(1)
        # stop streaming
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Turning off streaming..')
        hwif.stopStreaming()
        self.valueChanged.emit(1)
        # save result, post message, and emit finished()
        impedanceFilename = os.path.abspath('../cal/impedance_%s.npy' % strtime)
        np.save(impedanceFilename, self.impedanceMeasurements)
        self.statusUpdated.emit('Impedance measurements saved to %s' % impedanceFilename)
        self.finished.emit()

    def oneChannelRoutine(self):
        # start streaming
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Starting streaming..')
        hwif.startStreaming_boardsamples()
        self.valueChanged.emit(1)
        # enable ZCheck registers
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Enabling Intan impedance check..')
        hwif.enableZCheck(self.absChan % 32, self.capscale) 
        self.valueChanged.emit(1)
        # take snapshot
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Taking snapshot..')
        tmpSnapshotFilename = os.path.abspath('../tmp/tmpSnapshot.h5')
        hwif.takeSnapshot(self.nsamples, tmpSnapshotFilename) # alreadyStreaming branch
        self.valueChanged.emit(1)
        # disable ZCheck registers
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Disabling Intan impedance check..')
        hwif.disableZCheck()
        self.valueChanged.emit(1)
        # stop streaming
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Turning off streaming..')
        hwif.stopStreaming()
        self.valueChanged.emit(1)
        # import snapshot
        self.valueChanged.emit(0)
        self.maxChanged.emit(15)
        self.textChanged.emit('Importing snapshot..')
        snapshotData = self.importSnapshot(tmpSnapshotFilename, emit=True)
        self.valueChanged.emit(15)
        # analyze snapshot
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Analyzing snapshot..')
        impedance = self.analyzeSnapshot_oneChannel(snapshotData, self.absChan)
        self.valueChanged.emit(1)
        self.statusUpdated.emit('Impedance Result for Channel %d: %10.2f' % (self.absChan, impedance))
        self.finished.emit()

    def run(self):
        if hwif.isRecording() or hwif.isStreaming():
            self.statusUpdated.emit('ImpedanceThread: Cannot check impedance while recording or streaming')
            return
        if self.params['routine'] == 0:
            self.allChipsRoutine()
        elif self.params['routine'] == 1:
            self.absChan = self.params['channel']
            self.oneChannelRoutine()

