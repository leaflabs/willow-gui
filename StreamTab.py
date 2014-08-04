from PyQt4 import QtCore, QtGui
import subprocess, os, sys
import numpy as np

from parameters import DAEMON_DIR, DATA_DIR

sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

# more parameters
DEFAULT_FORWARD_ADDR = '127.0.0.1'
DEFAULT_FORWARD_PORT = 7654      # for proto2bytes
CHANNELS_PER_CHIP = 32
CHIPS_PER_DATANODE = 32

class StreamTab(QtGui.QWidget):

    def __init__(self, parent):
        super(StreamTab, self).__init__(None)
        self.parent = parent

        self.chipNumLine = QtGui.QLineEdit('3')
        self.channelNumLine = QtGui.QLineEdit('3')

        self.streamCheckbox = QtGui.QCheckBox('Stream')
        self.streamCheckbox.stateChanged.connect(self.toggleStream)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel('Chip Number:'))
        self.layout.addWidget(self.chipNumLine)
        self.layout.addWidget(QtGui.QLabel('Channel Number:'))
        self.layout.addWidget(self.channelNumLine)
        self.layout.addSpacing(200)
        #self.layout.addWidget(self.standbyCheckbox)
        self.layout.addWidget(self.streamCheckbox)
        self.setLayout(self.layout)

        # stream buffers, etc.
        sr = 30000  # sample rate
        fr = 30      # frame rate
        self.fp = 1000//fr  # frame period
        n = 30000   # number of samples to display
        self.nrefresh = sr//fr   # new samples collected before refresh
        self.xvalues = np.arange(n, dtype='int')
        self.plotBuff = np.zeros(n, dtype='uint16')
        self.newBuff = np.zeros(self.nrefresh, dtype='uint16')

        # timer stuff
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updatePlot)

        self.acquireDotPy = os.path.join(DAEMON_DIR, 'util/acquire.py')
        self.proto2bytes = os.path.join(DAEMON_DIR, 'build/proto2bytes')

    def toggleStream(self):
        if (self.parent.isDaemonRunning and not self.parent.isDaqRunning):
            if self.streamCheckbox.isChecked():
                self.setSubsamples()
                self.toggleForwarding(True)
                self.toggleStdin(True)
                self.parent.statusBox.append('Started streaming.')
            else:
                self.toggleStdin(False)
                self.toggleForwarding(False)
                self.parent.statusBox.append('Stopped streaming.')
        else:
            #TODO gray-out the checkbox when this condition is met
            self.parent.statusBox.append('Make sure daemon is started, and DAQ is NOT running!')
            self.streamCheckbox.setChecked(False) #TODO bug: this still gets checked 1 in 3 times (??)

    def setSubsamples(self):
        chip = int(self.chipNumLine.text())
        chipchanList = [(chip, chan) for chan in range(32)]
        cmds = []
        for i,chipchan in enumerate(chipchanList):
            chip = chipchan[0] & 0b00011111
            chan = chipchan[1] & 0b00011111
            cmds.append(reg_write(MOD_DAQ, DAQ_SUBSAMP_CHIP0+i,
                           (chip << 8) | chan))
        resps = do_control_cmds(cmds)

    def toggleForwarding(self, enable):
        if self.parent.isDaqRunning:
            self.parent.statusBox.append('Turn off acquisition before streaming!')
        else:
            cmds = []
            cmd = ControlCommand(type=ControlCommand.FORWARD)
            if enable:
                cmd.forward.sample_type = BOARD_SUBSAMPLE
                cmd.forward.force_daq_reset = True # !!! Make sure you're not already acquiring!!!
                try:
                    aton = socket.inet_aton(DEFAULT_FORWARD_ADDR)
                except socket.error:
                    self.parent.statusBox.append('Invalid address: ' + DEFAULT_FORWARD_ADDR)
                    sys.exit(1)
                cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
                cmd.forward.dest_udp_port = DEFAULT_FORWARD_PORT
                cmd.forward.enable = True
                cmds.append(cmd)
            else:
                cmd.forward.enable = False
                cmds.append(cmd)
                cmd = ControlCommand(type=ControlCommand.ACQUIRE)
                cmd.acquire.enable = False
                cmds.append(cmd)
            resps = do_control_cmds(cmds)

    def toggleStdin(self, enable):
        if enable:
            self.proto2bytes_po = subprocess.Popen([self.proto2bytes, '-s', '-c', self.channelNumLine.text()], stdout=subprocess.PIPE)
            self.timer.start(self.fp)
        else:
            self.timer.stop()
            self.proto2bytes_po.kill()

    def updatePlot(self):
        for i in range(self.nrefresh):
            self.newBuff[i] = self.proto2bytes_po.stdout.readline()
        self.plotBuff = np.concatenate((self.plotBuff[self.nrefresh:],self.newBuff))
        self.parent.waveform[0].set_data(self.xvalues, self.plotBuff)
        self.parent.canvas.draw()

