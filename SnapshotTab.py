from PyQt4 import QtCore, QtGui
import subprocess, h5py, os, sys
import numpy as np
from progressbar import ProgressBar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from parameters import DAEMON_DIR, DATA_DIR

sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

DEFAULT_FORWARD_ADDR = '127.0.0.1'
DEFAULT_FORWARD_PORT = 7654      # for proto2bytes
CHANNELS_PER_CHIP = 32
CHIPS_PER_DATANODE = 32

class SnapshotTab(QtGui.QWidget):

    def __init__(self, parent):
        super(SnapshotTab, self).__init__(None)
        self.parent = parent

        self.nsampLine = QtGui.QLineEdit('30000')
        self.dirLine = QtGui.QLineEdit(DATA_DIR)
        self.filenameLine = QtGui.QLineEdit()
        self.recordButton = QtGui.QPushButton('Take a Snapshot')
        self.recordButton.clicked.connect(self.takeSnapshot)
        self.plotRecentButton = QtGui.QPushButton('Plot Most Recent')
        self.plotRecentButton.clicked.connect(self.plotRecent)
        self.mostRecentFilename = None

        self.plotSpecificButton = QtGui.QPushButton('Plot Specific File:')
        self.plotSpecificButton.clicked.connect(self.plotSpecific)
        self.specificLine = QtGui.QLineEdit()

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel('Number of Samples:'))
        self.layout.addWidget(self.nsampLine)
        self.layout.addWidget(QtGui.QLabel('Directory:'))
        self.layout.addWidget(self.dirLine)
        self.layout.addWidget(QtGui.QLabel('Filename:'))
        self.layout.addWidget(self.filenameLine)
        self.layout.addWidget(self.recordButton)
        self.layout.addSpacing(100)
        self.layout.addWidget(self.plotRecentButton)
        tmpLayout = QtGui.QHBoxLayout()
        tmpLayout.addWidget(self.plotSpecificButton)
        tmpLayout.addWidget(self.specificLine)
        tmpWidget = QtGui.QWidget()
        tmpWidget.setLayout(tmpLayout)
        self.layout.addWidget(tmpWidget)

        self.setLayout(self.layout)

        self.acquireDotPy = os.path.join(DAEMON_DIR,'util/acquire.py')

    def takeSnapshot(self):
        if self.parent.isDaemonRunning:
            filename = os.path.join(str(self.dirLine.text()), str(self.filenameLine.text()))
            nsamples = int(self.nsampLine.text())
            if self.parent.isDaqRunning:
                self.parent.statusBox.append('Cannot issue ControlCmd because DAQ is currently running.')
            else:

                # TODO why doesn't this show up until after do_control_cmds returns??
                self.parent.statusBox.append('Taking snapshot...') 
                cmds = []

                cmd = ControlCommand(type=ControlCommand.FORWARD)
                # issuing this command seems like overkill, but right now it's
                # the only way to start the DAQ without saving to SATA
                cmd.forward.sample_type = BOARD_SUBSAMPLE
                cmd.forward.force_daq_reset = True
                try:
                    aton = socket.inet_aton(DEFAULT_FORWARD_ADDR)
                except socket.error:
                    self.parent.statusBox.append('Invalid address: ' + DEFAULT_FORWARD_ADDR)
                    sys.exit(1)
                cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
                cmd.forward.dest_udp_port = DEFAULT_FORWARD_PORT
                cmd.forward.enable = True
                cmds.append(cmd)

                cmd = ControlCommand(type=ControlCommand.STORE)
                cmd.store.path = filename
                cmd.store.nsamples = nsamples
                cmds.append(cmd)

                cmd = ControlCommand(type=ControlCommand.ACQUIRE)
                cmd.acquire.enable = False
                cmds.append(cmd)

                resps = do_control_cmds(cmds)

                if True: # TODO test for resps here
                    self.parent.statusBox.append('Saved %d samples to %s' % (nsamples, filename))
                    self.mostRecentFilename = filename
        else:
            self.parent.statusBox.append('Daemon is not running.')

    def plotFromFile(self, filename):
        """
        f = h5py.File(filename)
        dset = f['wired-dataset'] # each element is this convoluted tuple
        ns = len(dset)  # number of samples
        data = np.zeros((1024,ns), dtype='uint16')      # 1024 channels at 30 kHz
        pbar = ProgressBar(maxval=ns-1).start()
        self.parent.statusBox.append('Reading in data from '+filename)
        print 'Reading in data from '+filename
        for i in range(ns):
            pbar.update(i)
            data[:,i] = dset[i][3][:1024]
        pbar.finish()
        self.parent.statusBox.append('Done.')
        bank = 3
        self.parent.statusBox.append('Plotting multi-channel data...')
        newFig = Figure((5.,4.), dpi=100)
        self.parent.fig.clear()
        for i in range(32):
            ax = self.parent.fig.add_subplot(8,4,i+1)
            ax.set_axis_bgcolor('k')
            ax.plot(data[bank*32+i,:], color='y')
            ax.set_ylim([0,2**16-1])
            ax.xaxis.set_ticklabels([]) # this makes the axes text invisible (but not the ticks themselves)
            ax.yaxis.set_ticklabels([]) # this makes the axes text invisible (but not the ticks themselves)
        self.parent.fig.subplots_adjust(left=0.,bottom=0.,right=1.,top=1., wspace=0.04, hspace=0.1)
        self.parent.canvas.draw()
        self.parent.statusBox.append('Done.')
        """
        self.parent.statusBox.append('This does nothing yet')

    def plotRecent(self):
        if self.mostRecentFilename:
            self.plotFromFile(self.mostRecentFilename)
        else:
            self.parent.statusBox.append('Nothing recorded yet.')

    def plotSpecific(self):
        datadir = str(self.dirLine.text())
        specificFilename = str(self.specificLine.text())
        filename = os.path.join(datadir, specificFilename)
        if specificFilename:
            if os.path.exists(filename):
                self.plotFromFile(filename)
            else:
                self.parent.statusBox.append('File does not exist: '+filename)
        else:
            self.parent.statusBox.append('Please enter filename to plot.')
