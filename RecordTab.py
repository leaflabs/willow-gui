from PyQt4 import QtCore, QtGui
import h5py, os, sys
import numpy as np
from progressbar import ProgressBar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from time import time

from parameters import DAEMON_DIR, DATA_DIR

sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

BSI_INTERVAL = 1920

class RecordTab(QtGui.QWidget):

    def __init__(self, parent):
        super(RecordTab, self).__init__(None)
        self.parent = parent

        self.description = QtGui.QLabel("Record an experiment on the datanode's disk storage.")

        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(125e6)  # TODO what is this number exactly?
        self.progressBar.setValue(0)

        self.streamCheckbox = QtGui.QCheckBox('Enable Streaming')
        self.streamCheckbox.stateChanged.connect(self.toggleStream)

        self.startButton = QtGui.QPushButton('Start')
        self.startButton.clicked.connect(self.startRecording)
        self.stopButton = QtGui.QPushButton('Stop')
        self.stopButton.clicked.connect(self.stopRecording)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addSpacing(20)
        self.layout.addWidget(self.description)
        self.layout.addSpacing(20)
        self.layout.addWidget(QtGui.QLabel('Disk Usage:'))
        self.layout.addWidget(self.progressBar)
        self.layout.addSpacing(40)
        #self.layout.addWidget(self.streamCheckbox)
        self.layout.addWidget(self.startButton)
        self.layout.addWidget(self.stopButton)

        self.setLayout(self.layout)

        self.withStreaming = False

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateProgressBar)

    def updateProgressBar(self):
        resp = do_control_cmd(reg_read(2, 7)) # SATA module, Last Write Index (4B)
        if resp is None or resp.type != 255:
            self.parent.statusBox.append("%s\nNo response! Is daemon running?" % resp)
        else:
            diskIndex = resp.reg_io.val
            self.progressBar.setValue(diskIndex)

    def startRecording(self):
        if self.parent.state.isDaemonRunning():
            if self.withStreaming:
                self.parent.statusBox.append('No recording with streaming yet')
            else:
                self.progressBar.setValue(0)
                cmd = ControlCommand(type=ControlCommand.ACQUIRE)
                cmd.acquire.exp_cookie = long(time())
                cmd.acquire.start_sample = 0
                cmd.acquire.enable = True
                resp = do_control_cmd(cmd)
                self.parent.statusBox.append('Started recording')
                self.timer.start(5000)
        else:
            self.parent.statusBox.append('Please start daemon first.')

    def stopRecording(self):
        if self.parent.state.isDaemonRunning():
            cmd = ControlCommand(type=ControlCommand.ACQUIRE)
            cmd.acquire.enable = False
            resp = do_control_cmd(cmd)
            self.parent.statusBox.append('Stopped recording')
            self.timer.stop()
        else:
            self.parent.statusBox.append('Please start daemon first.')

    def toggleStream(self):
        if self.streamCheckbox.isChecked():
            self.withStreaming = True
        else:
            self.withStreaming = False
