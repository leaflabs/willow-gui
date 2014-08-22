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

# more parameters
DEFAULT_FORWARD_ADDR = '127.0.0.1'
DEFAULT_FORWARD_PORT = 7654      # for proto2bytes
CHANNELS_PER_CHIP = 32
CHIPS_PER_DATANODE = 32

class RecordTab(QtGui.QWidget):

    def __init__(self, parent):
        super(RecordTab, self).__init__(None)
        self.parent = parent

        self.description = QtGui.QLabel("Record an experiment on the datanode's disk storage.")

        self.statusBar = QtGui.QLabel('Not Recording')
        self.statusBar.setAlignment(QtCore.Qt.AlignCenter)
        self.statusBar.setStyleSheet('QLabel {background-color: gray; font: bold}')

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
        self.layout.addWidget(self.statusBar)
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
        if self.parent.isConnected():
            self.progressBar.setValue(0)

            cmds = []

            if self.parent.state.isStreaming():
                cmd = ControlCommand(type=ControlCommand.FORWARD)
                cmd.forward.enable = False
                cmds.append(cmd)

            cmd = ControlCommand(type=ControlCommand.ACQUIRE)
            cmd.acquire.exp_cookie = long(time())
            cmd.acquire.start_sample = 0
            cmd.acquire.enable = True
            cmds.append(cmd)

            if self.parent.state.isStreaming():
                cmd = ControlCommand(type=ControlCommand.FORWARD)
                cmd.forward.sample_type = BOARD_SUBSAMPLE
                cmd.forward.force_daq_reset = False
                try:
                    aton = socket.inet_aton(DEFAULT_FORWARD_ADDR)
                except socket.error:
                    self.parent.statusBox.append('Invalid address: ' + DEFAULT_FORWARD_ADDR)
                    sys.exit(1)
                cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
                cmd.forward.dest_udp_port = DEFAULT_FORWARD_PORT
                cmd.forward.enable = True
                cmds.append(cmd)

            resps = do_control_cmds(cmds)
            # TODO implement resp-checking
            self.parent.state.setRecording(True)
            self.parent.statusBox.append('Started recording')
            self.timer.start(5000)
            self.statusBar.setText('Recording')
            self.statusBar.setStyleSheet('QLabel {background-color: red; font: bold}')
            """
            if resp.type==2:
                self.parent.state.setRecording(True)
                self.parent.statusBox.append('Started recording')
                self.timer.start(5000)
                self.statusBar.setText('Recording')
                self.statusBar.setStyleSheet('QLabel {background-color: red; font: bold}')
            else:
                self.parent.statusBox.append('Something went wrong')
            """

    def stopRecording(self):
        if self.parent.isConnected():
            cmds = []

            cmd = ControlCommand(type=ControlCommand.ACQUIRE)
            cmd.acquire.enable = False
            cmds.append(cmd)

            if self.parent.state.isStreaming():
                cmd = ControlCommand(type=ControlCommand.FORWARD)
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

            resps = do_control_cmds(cmds)
            # TODO implement resp-checking
            self.parent.state.setRecording(False)
            self.parent.statusBox.append('Stopped recording')
            self.timer.stop()
            self.statusBar.setText('Not Recording')
            self.statusBar.setStyleSheet('QLabel {background-color: gray; font: bold}')
            """
            if resp.type==2:
                self.parent.state.setRecording(False)
                self.parent.statusBox.append('Stopped recording')
                self.timer.stop()
                self.statusBar.setText('Not Recording')
                self.statusBar.setStyleSheet('QLabel {background-color: gray; font: bold}')
            else:
                self.parent.statusBox.append('Something went wrong')
            """

    def toggleStream(self):
        if self.streamCheckbox.isChecked():
            self.withStreaming = True
        else:
            self.withStreaming = False
