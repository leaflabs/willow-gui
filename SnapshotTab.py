from PyQt4 import QtCore, QtGui
import subprocess, h5py, os, sys
import numpy as np
from progressbar import ProgressBar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PlotWindow import PlotWindow 

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

        self.description = QtGui.QLabel('Take a snapshot: a short recording from all 1024 channels, saved directly your filesystem.')

        self.nsamplesWidget = self.NSamplesWidget(self)
        self.filenameBrowseWidget = self.FilenameBrowseWidget(self)
        self.recordButton = QtGui.QPushButton('Take a Snapshot')
        self.recordButton.clicked.connect(self.takeSnapshot)
        self.plotRecentButton = QtGui.QPushButton('Plot Most Recent')
        self.plotRecentButton.clicked.connect(self.plotRecent)
        self.mostRecentFilename = None

        self.layout = QtGui.QVBoxLayout()
        self.layout.addSpacing(20)
        self.layout.addWidget(self.description)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.nsamplesWidget)
        self.layout.addWidget(self.filenameBrowseWidget)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.recordButton)
        self.layout.addWidget(self.plotRecentButton)

        self.setLayout(self.layout)

        self.plotWindows = []

    class FilenameBrowseWidget(QtGui.QWidget):

        def __init__(self, parent):
            super(parent.FilenameBrowseWidget, self).__init__()
            self.filenameLine = QtGui.QLineEdit()
            self.browseButton = QtGui.QPushButton('Browse')
            self.browseButton.clicked.connect(self.browse)
            self.layout = QtGui.QHBoxLayout()
            self.layout.addWidget(QtGui.QLabel('Filename:'))
            self.layout.addWidget(self.filenameLine)
            self.layout.addWidget(self.browseButton)
            self.setLayout(self.layout)

        def browse(self):
            filename = QtGui.QFileDialog.getSaveFileName(self, 'Save To...', DATA_DIR)
            self.filenameLine.setText(filename)

    class NSamplesWidget(QtGui.QWidget):

        def __init__(self, parent):
            super(parent.NSamplesWidget, self).__init__()
            self.nsamplesLine = QtGui.QLineEdit()
            self.layout = QtGui.QHBoxLayout()
            self.layout.addWidget(QtGui.QLabel('Number of samples:'))
            self.layout.addWidget(self.nsamplesLine)
            self.setLayout(self.layout)

    def takeSnapshot(self):
        filename = str(self.filenameBrowseWidget.filenameLine.text())
        if filename:
            if self.parent.state.isDaemonRunning():
                if self.parent.state.isDaqRunning():
                    self.parent.statusBox.append('Cannot issue ControlCmd because DAQ is currently running.')
                else:
                    # TODO why doesn't this show up until after do_control_cmds returns??
                    self.parent.statusBox.append('Taking snapshot...') 

                    nsamples = int(self.nsamplesWidget.nsamplesLine.text())

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
        else:
            self.parent.statusBox.append('Please enter target filename.')

    def plotRecent(self):
        if self.mostRecentFilename:
            plotWindow = PlotWindow(self, self.mostRecentFilename, -1)
            self.plotWindows.append(plotWindow)   # TODO garbage collect this array
            plotWindow.show()
        else:
            self.parent.statusBox.append('Nothing recorded yet.')
