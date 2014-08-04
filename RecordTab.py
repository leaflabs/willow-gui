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

        self.startButton = QtGui.QPushButton('Start')
        self.startButton.clicked.connect(self.startRecording)
        self.stopButton = QtGui.QPushButton('Stop')
        self.stopButton.clicked.connect(self.stopRecording)

        self.streamCheckbox = QtGui.QCheckBox('Enable Streaming')
        self.streamCheckbox.stateChanged.connect(self.toggleStream)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.streamCheckbox)
        self.layout.addWidget(self.startButton)
        self.layout.addWidget(self.stopButton)

        self.setLayout(self.layout)

    def startRecording(self):
        if self.parent.isDaemonRunning:
            if self.withStreaming:
                self.parent.statusBox.append('No recording with streaming yet')
            else:
                cmd = ControlCommand(type=ControlCommand.ACQUIRE)
                cmd.acquire.exp_cookie = long(time())
                cmd.acquire.start_sample = 0
                cmd.acquire.enable = True
                resp = do_control_cmd(cmd)
                self.parent.statusBox.append('Started recording')
        else:
            self.parent.statusBox.append('Please start daemon first!')

    def stopRecording(self):
        cmd = ControlCommand(type=ControlCommand.ACQUIRE)
        cmd.acquire.enable = False
        resp = do_control_cmd(cmd)
        self.parent.statusBox.append('Stopped recording')

    def toggleStream(self):
        if self.streamCheckbox.isChecked():
            self.withStreaming = True
        else:
            self.withStreaming = False
