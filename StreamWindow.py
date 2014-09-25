from PyQt4 import QtCore, QtGui
import subprocess, os, sys, socket
import numpy as np

from parameters import *
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

import numpy as np
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from StateManagement import checkState, changeState, DaemonControlError

class StreamWindow(QtGui.QWidget):

    def __init__(self, parent, chip, chan):
        super(StreamWindow, self).__init__(None)

        self.parent = parent
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
        self.axes = self.fig.add_subplot(111)
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

        self.waveform = self.axes.plot(np.arange(30000), np.array([2**15]*30000), color='#8fdb90')
        #self.waveform = self.axes.plot(np.arange(30000), np.array([2**15]*30000), color='#b2d89f')
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
        try:
            changeState('start streaming')
            self.toggleStdin(True)
            self.parent.parent.statusBox.append('Started streaming.')
        except socket.error, DaemonControlError:
            pass # error messages printed by changeState

    def stopStreaming(self):
        try:
            self.toggleStdin(False)
            changeState('stop streaming')
            self.parent.parent.statusBox.append('Stopped streaming.')
        except socket.error, DaemonControlError:
            pass # error messages printed by changeState

    def toggleStdin(self, enable):
        if enable:
            # why does this still print GAPs?
            self.proto2bytes_po = subprocess.Popen([self.proto2bytes, '-s',
                '-c', str(self.chan)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.timer.start(self.fp)
        else:
            self.timer.stop()
            self.proto2bytes_po.kill()

    def updatePlot(self):
        for i in range(self.nrefresh):
            self.newBuff[i] = self.proto2bytes_po.stdout.readline()
        self.plotBuff = np.concatenate((self.plotBuff[self.nrefresh:],self.newBuff))
        self.waveform[0].set_data(self.xvalues, self.plotBuff)
        self.canvas.draw()

    def closeEvent(self, event):
        if checkState() & 0b001:
            self.stopStreaming()

