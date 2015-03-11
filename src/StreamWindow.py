from PyQt4 import QtCore, QtGui
import subprocess, os, sys, socket
import numpy as np

import config

import numpy as np
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

import hwif
import CustomExceptions as ex

def calculateTicks(axisrange):
    delta = axisrange[1] - axisrange[0]
    # delta must be greater than 1 but less than 100000; check for this somewhere
    increments = [10**i for i in range(4,-1,-1)]
    i = 0
    increment = None
    while not increment:
        inc = increments[i]
        if delta > 3*inc:
            increment = inc
        i += 1
    multiple = axisrange[0]//increment
    tick0 = (multiple+1)*increment
    ticks = range(tick0, axisrange[1], increment)
    return ticks

class StreamWindow(QtGui.QWidget):

    def __init__(self, params, msgLog):
        super(StreamWindow, self).__init__(None)
        self.msgLog = msgLog

        channel = params['channel']
        self.chip = channel//32
        self.chan = channel%32
        ymin = params['ymin']
        ymax = params['ymax']
        self.yrange_uV = [ymin, ymax]
        self.yrange_cnts = [int(y*5+2**15) for y in self.yrange_uV]
        self.refreshRate = params['refreshRate']

        try:
            hwif.setSubsamples_byChip(self.chip)
        except hwif.hwifError as e:
            self.msgLog.post(e.message)

        ###################
        # Matplotlib Setup
        ###################

        #self.fig = Figure((5.0, 4.0), dpi=100)
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_title('Chip %d, Channel %d' % (self.chip, self.chan))
        self.axes.set_ylabel('microVolts')
        self.axes.set_xlabel('Samples')
        self.axes.set_axis_bgcolor('k')
        self.axes.axis([0, 30000, self.yrange_cnts[0], self.yrange_cnts[1]])

        yticks_uV = calculateTicks(self.yrange_uV)
        yticklabels = [str(tick) for tick in yticks_uV]
        yticks = [int(tick*5+2**15) for tick in yticks_uV]
        self.axes.set_yticks(yticks)
        self.axes.set_yticklabels(yticklabels)

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
        fr = self.refreshRate      # frame rate
        self.fp = 1000//fr  # frame period
        n = 30000   # number of samples to display
        self.nrefresh = sr//fr   # new samples collected before refresh
        self.xvalues = np.arange(n, dtype='int')
        self.plotBuff = np.zeros(n, dtype='uint16')
        self.newBuff = np.zeros(self.nrefresh, dtype='uint16')

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updatePlot)

        self.proto2bytes = os.path.join(config.daemonDir, 'build/proto2bytes')

        ###################
        # Top-level stuff
        ##################

        self.startButton = QtGui.QPushButton()
        self.startButton.setIcon(QtGui.QIcon('../img/play.png'))
        self.startButton.setIconSize(QtCore.QSize(48,48))
        self.startButton.clicked.connect(self.startStreaming)

        self.stopButton = QtGui.QPushButton()
        self.stopButton.setIcon(QtGui.QIcon('../img/pause.png'))
        self.stopButton.setIconSize(QtCore.QSize(48,48))
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

        self.setWindowTitle('Willow Live Streaming')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))

    def startStreaming(self):
        try:
            hwif.startStreaming_subsamples()
            self.toggleStdin(True)
            self.msgLog.post('Started streaming.')
        except hwif.AlreadyError:
            #self.toggleStdin(True) # ideally this would start the plot updating, but for now it fails
            self.msgLog.post('Hardware was already streaming. Try stopping and restarting stream.')
        except hwif.hwifError as e:
            self.msgLog.post(e.message)

    def stopStreaming(self):
        try:
            hwif.stopStreaming()
            self.toggleStdin(False)
            self.msgLog.post('Stopped streaming.')
        except hwif.AlreadyError:
            self.toggleStdin(False)
            self.msgLog.post('Already not streaming')
        except AttributeError:
            # TODO what's up with this?
            self.msgLog.post('AttributeError: Pipe object does not exist')
        except hwif.hwifError as e:
            self.msgLog.post(e.message)

    def toggleStdin(self, enable):
        if enable:
            self.proto2bytes_po = subprocess.Popen([self.proto2bytes, '-s',
                '-c', str(self.chan)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.timer.start(self.fp)
            print 'timer started'
        else:
            self.timer.stop()
            try:
                self.proto2bytes_po.kill()
            except AttributeError:
                pass

    def updatePlot(self):
        for i in range(self.nrefresh):
            self.newBuff[i] = self.proto2bytes_po.stdout.readline()
        self.plotBuff = np.concatenate((self.plotBuff[self.nrefresh:],self.newBuff))
        self.waveform[0].set_data(self.xvalues, self.plotBuff)
        self.canvas.draw()

    def closeEvent(self, event):
        try:
            if hwif.isStreaming():
                self.stopStreaming()
        except hwif.hwifError as e:
            self.msgLog.post(e.message)

