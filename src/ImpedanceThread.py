from PyQt4 import QtCore, QtGui
import sys, os, h5py
import numpy as np
import hwif

from parameters import *
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

# TODO !!! wrap all the hwif calls in exception handlers

class ImpedanceThread(QtCore.QThread):

    valueChanged = QtCore.pyqtSignal(int)
    maxChanged = QtCore.pyqtSignal(int)
    textChanged = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, chip, chan, statusBox):
        super(ImpedanceThread, self).__init__()
        self.chip = chip
        self.chan = chan
        self.capscale = 0b01    # hard-coded for now
        self.statusBox = statusBox

    def amp2volts(self, amplitude, nsamples):
        # copied from impedance_tool.py
        """
        Converts a complex FFT amplitude at 1KHz to a sinewave amplitude in volts
        (normal amplitude, not peak-to-peak).

        The conversion factor between ADC counts and volts is 0.195 microvolts per
        count.
        """
        return abs(amplitude * 2 / nsamples) * 0.195 * 10**-6

    def volts2impedance(self, volts, capacitorscale):
        # copied from impedance_tool.py
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

        if volts < 10**-6:
            # dodge a divide-by-zero or numerical glitch
            return 'short (null data)'

        impedance = volts / cap2current[capacitorscale]

        if impedance > 10**7:
            # above 10 MOhm, assume we've got an open circuit 
            return 'open (> 10 MOhm)'
        elif impedance <= 0.1: # very small, probably numerical
            return 'short (< 0.1 Ohm)'
        else:
            return impedance

    def getChipsAlive(self):
            # borrowed from impedance_tool.py
            mask = hwif.doRegRead(3, 4)
            return [i for i in range(32) if (mask & (0x1 << i))]

    def setChannelList(self, l):
        # borrowed from debug_tool.py
        """ 
        Takes a list of 32 (chip, chan) tuples and tells to data node to return
        those channel pairings as the 32 "virtual channels" in live-streaming
        sub-sample packets.
        """
        for i in range(32):
            chip = l[i][0] & 0b00011111
            chan = l[i][1] & 0b00011111
            hwif.doRegWrite(3, 128+i, (chip << 8) | chan)

    def configureZCheck(self, chan, capscale):
        """
        inspired by configure_dac in impedance_tool.py
        capscale should be 0b00, 0b01, or 0b11
        """
        # first set DAC configuration register
        enable = 0b1
        power = (0b1 << 6)
        scale = (capscale & 0b11) << 3
        cmd = ((0x1 << 24) |        # aux command write enable
               (0xFF << 16) |       # all chips (required by h/w)
               (0b10000101 << 8) |  # write to register 5 (DAC config)
               (enable | power | scale))   # settings
        hwif.doRegWrite(3, 5, cmd)
        # then set the DAC channel register
        chan = chan & 0b11111
        cmd = ((0x1 << 24) |        # aux command write enable
               (0xFF << 16) |       # all chips
               (0b10000111 << 8) |  # write to register 7 (DAC chan select)
               (chan))              # channel select
        hwif.doRegWrite(3, 5, cmd)
        # finally, clear the CMD register
        hwif.doRegWrite(3, 5, 0)

    def importSnapshot(self, tmpSnapshotFilename, nsamples):
        f = h5py.File(tmpSnapshotFilename)
        dset = f['wired-dataset']
        data = np.zeros((1024,nsamples), dtype='uint16')
        for i in range(nsamples):
            data[:,i] = dset[i][3][:1024]
            if (i%1000==0):
                self.valueChanged.emit(i/1000)
        #data_uv = (np.array(self.data, dtype='float')-2**15)*0.2
        return data

    def analyzeSnapshot(self, data):
        absChan = self.chip*32 + self.chan
        fft = np.fft.rfft(data[absChan, :])
        volts = self.amp2volts(fft[500], 15000) # TODO fix this hard-coding!
        return self.volts2impedance(volts, self.capscale)


    def allChipsRoutine(self):
        # tmp message
        self.statusBox.append('ImpedanceThead: All Chips Routine not implemented yet.')
        self.finished.emit()

    def oneChipRoutine(self):
        nsamples = 15000
        # start streaming
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Starting streaming..')
        hwif.startStreaming_boardsamples()
        self.valueChanged.emit(1)
        # configure zcheck registers
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Configuring zcheck registers..')
        self.configureZCheck(self.chan, self.capscale)
        self.valueChanged.emit(1)
        # take snapshot
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Taking snapshot..')
        tmpSnapshotFilename = os.path.join(DATA_DIR, 'tmpSnapshot.h5')
        hwif.takeSnapshot(nsamples, tmpSnapshotFilename)
        self.valueChanged.emit(1)
        # import snapshot
        self.valueChanged.emit(0)
        self.maxChanged.emit(15)
        self.textChanged.emit('Importing snapshot..')
        data = self.importSnapshot(tmpSnapshotFilename, nsamples)
        self.valueChanged.emit(15)
        # analyze snapshot
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Analyzing snapshot..')
        impedance = self.analyzeSnapshot(data)
        self.valueChanged.emit(15)
        #if type(impedance)==str:
        #    self.statusBox.append('Impedance Result: %s' % impedance)
        #else:
        #    self.statusBox.append('Impedance Result: %10.2f' % impedance)
        #self.statusBox.append('ImpedanceThread: stopping streaming')
        self.valueChanged.emit(0)
        self.maxChanged.emit(1)
        self.textChanged.emit('Turning off streaming..')
        hwif.stopStreaming()
        self.valueChanged.emit(15)
        self.finished.emit()

    def run(self):
        if hwif.isRecording() or hwif.isStreaming():
            self.statusBox.append('ImpedanceThread: Cannot check impedance while recording or streaming')
            return
        if self.chip == -1:
            self.allChipsRoutine()
        else:
            chipAliveList = self.getChipsAlive()
            if not self.chip in chipAliveList:
                self.statusBox.append('ImpedanceThread: Chip %d requested is not alive.' % self.chip)
                return
            self.oneChipRoutine()

