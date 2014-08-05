from PyQt4 import QtCore, QtGui
import subprocess, os, sys
import numpy as np

from parameters import DAEMON_DIR, DATA_DIR
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

import numpy as np
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

# more parameters
DEFAULT_FORWARD_ADDR = '127.0.0.1'
DEFAULT_FORWARD_PORT = 7654      # for proto2bytes
CHANNELS_PER_CHIP = 32
CHIPS_PER_DATANODE = 32

class StreamWindow(QtGui.QWidget):

    def __init__(self, chip, chan):
        super(StreamWindow, self).__init__(None)

        self.chip = chip
        self.chan= chan

        self.setSubsamples_byChip(self.chip)

        ###################
        # Matplotlib Setup
        ###################

        #self.fig = Figure((5.0, 4.0), dpi=100)
        self.fig = Figure()
        #self.fig.subplots_adjust(left=0.,bottom=0.,right=1.,top=1., wspace=0.04, hspace=0.1)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.axes = self.fig.add_subplot(self.nchannels, 1, i+1)
        self.axes.set_title('Chip %d, Channel %d' % (self.chip, chan))
        self.axes.yaxis.set_ticklabels([])
        self.axes.set_axis_bgcolor('k')
        self.axes.axis([0,30000,0,2**16-1])
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)

        self.mplLayout = QtGui.QVBoxLayout()
        self.mplLayout.addWidget(self.canvas)
        self.mplLayout.addWidget(self.mpl_toolbar)
        self.mplWindow = QtGui.QWidget()
        self.mplWindow.setLayout(self.mplLayout)

        self.waveform = self.axes.plot(np.arange(30000), np.array([2**15]*30000), color='y')
        self.canvas.draw()

        ###############################
        # stream buffers, timers, etc.
        ###############################

        sr = 30000  # sample rate
        fr = 30      # frame rate
        self.fp = 1000//fr  # frame period
        n = 30000   # number of samples to display
        self.nrefresh = sr//fr   # new samples collected before refresh
        self.xvalues = np.arange(n, dtype='int')
        self.plotBuff = np.zeros(n, dtype='uint16')
        self.newBuff = np.zeros(self.nrefresh, dtype='uint16')

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updatePlot)

        self.proto2bytes = os.path.join(DAEMON_DIR, 'build/proto2bytes')

        ###################
        # Top-level stuff
        ##################

        self.startButton = QtGui.QPushButton('Start')
        self.startButton.clicked.connect(self.startStreaming)

        self.stopButton = QtGui.QPushButton('Stop')
        self.stopButton.clicked.connect(self.stopStreaming)

        self.buttonPanel = QtGui.QWidget()
        tmp = QtGui.QHBoxLayout()
        tmp.addWidget(self.startButton)
        tmp.addWidget(self.stopButton)
        self.buttonPanel.setLayout(tmp)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.buttonPanel)
        self.layout.addWidget(self.mplWindow)
        self.setLayout(self.layout)

        self.setWindowTitle('WiredLeaf Live Streaming')
        self.setWindowIcon(QtGui.QIcon('round_logo_60x60.png'))

        self.isStreaming = False

    def setSubsamples_cherryPick(self):
        """
        Right now proto2bytes only allows subsample channels to all be on one chip
        (or one channel across all chips).
        But you can configure the subsamples manually through the reg_writes.
        So ideally we'd use this function to cherrypick those channels.
        TODO: implement this
        """
        cmds = []
        for i, chipchan in enumerate(self.chipchanVector):
            chip_str, chan_str = chipchan.split(',')
            chip = int(chip_str) & 0b00011111
            chan = int(chan_str) & 0b00011111
            cmds.append(reg_write(MOD_DAQ, DAQ_SUBSAMP_CHIP0+i,
                           (chip << 8) | chan))
        resps = do_control_cmds(cmds)

    def setSubsamples_byChip(self, chip):
        chipchanList = [(chip, chan) for chan in range(32)]
        cmds = []
        for i,chipchan in enumerate(chipchanList):
            chip = chipchan[0] & 0b00011111
            chan = chipchan[1] & 0b00011111
            cmds.append(reg_write(MOD_DAQ, DAQ_SUBSAMP_CHIP0+i,
                           (chip << 8) | chan))
        resps = do_control_cmds(cmds)

    def startStreaming(self):
        if self.isStreaming:
            print 'already streaming'
        else:
            self.toggleForwarding(True)
            self.toggleStdin(True)
            print 'started streaming'
            self.isStreaming = True

    def stopStreaming(self):
        if self.isStreaming:
            self.toggleStdin(False)
            self.toggleForwarding(False)
            print 'stopped streaming'
            self.isStreaming = False 
        else:
            print 'already not streaming'

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

    def toggleForwarding(self, enable):
        #if self.parent.isDaqRunning:
        if False:
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
            self.proto2bytes_po = subprocess.Popen([self.proto2bytes, '-s', '-c', str(self.chan)], stdout=subprocess.PIPE)
            self.timer.start(self.fp)
        else:
            self.timer.stop()
            self.proto2bytes_po.kill()

    def updatePlot(self):
        for i in range(self.nrefresh):
            self.newBuff[i] = self.proto2bytes_po.stdout.readline()
        self.plotBuff = np.concatenate((self.plotBuff[self.nrefresh:],self.newBuff))
        self.waveformList[0].set_data(self.xvalues, self.plotBuff)
        self.canvas.draw()

    def closeEvent(self, event):
        self.stopStreaming()
        print 'closing'

