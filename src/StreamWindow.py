#!/usr/bin/env python2

from PyQt4 import QtCore, QtGui
import subprocess, os, sys, socket
import numpy as np

import config

import numpy as np

import pyqtgraph as pg

import select

import hwif
import WillowDataset as const

INIT_WILLOWCHAN = 0
INIT_YMIN_UV = -6000
INIT_YMAX_UV = 6000
INIT_XRANGE_MS = 1000
INIT_REFRESH_RATE = 20

class StreamWindow(QtGui.QWidget):

    msgPosted = QtCore.pyqtSignal(str)

    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.refreshRate = INIT_REFRESH_RATE

        ###############################
        # stream buffers, timers, etc.
        ###############################

        self.fp = const.MS_PER_SEC // self.refreshRate  # frame period
        self.nbuff = int(const.SAMPLE_RATE * INIT_XRANGE_MS / const.MS_PER_SEC)   # number of samples to display
        self.nrefresh = int(const.SAMPLE_RATE / self.refreshRate)   # new samples collected before refresh
        self.t_relative = (np.arange(self.nbuff) - self.nbuff) / const.SAMPLE_RATE * const.MS_PER_SEC
        self.plotBuff = np.zeros(self.nbuff, dtype='float')
        self.newBuff = np.zeros(self.nrefresh, dtype='uint16')

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updatePlot)

        self.proto2bytes_filename = os.path.join(config.daemonDir, 'build/proto2bytes')

        ###############################
        # pyqtgraph plot
        ###############################

        self.plotWidget = pg.PlotWidget(labels={'left':u'Raw Signal (\N{GREEK SMALL LETTER MU}V)',
                                                'bottom':'Relative Time (ms)'},
                                        title='Willow Channel ####')
        self.plotItem = self.plotWidget.getPlotItem()
        self.plotItem.setXRange(min(self.t_relative), max(self.t_relative))
        self.plotItem.setYRange(INIT_YMIN_UV, INIT_YMAX_UV)
        self.plotItem.setLimits(xMin=min(self.t_relative), xMax=max(self.t_relative),
                                yMin=INIT_YMIN_UV, yMax=INIT_YMAX_UV)
        self.plotWidget.plot(x=self.t_relative, y=self.plotBuff)
        self.plotCurve = self.plotItem.curves[0]

        # install event filters for zooming
        self.plotItem.vb.installEventFilter(self)
        for axesDict in self.plotItem.axes.values():
            axesDict['item'].installEventFilter(self)

        ###################
        # Top-level stuff
        ##################


        self.chanLineEdit = QtGui.QLineEdit(str(INIT_WILLOWCHAN))
        self.chanLineEdit.setValidator(QtGui.QIntValidator(0,1023))
        self.chanLineEdit.setMaximumWidth(100)

        self.startButton = QtGui.QPushButton()
        self.startButton.setIcon(QtGui.QIcon('../img/play.png'))
        self.startButton.setIconSize(QtCore.QSize(40,40))
        self.startButton.clicked.connect(self.startStreaming)

        self.stopButton = QtGui.QPushButton()
        self.stopButton.setIcon(QtGui.QIcon('../img/pause.png'))
        self.stopButton.setIconSize(QtCore.QSize(40,40))
        self.stopButton.clicked.connect(self.stopStreaming)

        self.buttonPanel = QtGui.QWidget()
        self.buttonPanel.setMaximumHeight(70)
        tmp = QtGui.QGridLayout()
        tmp.addWidget(QtGui.QLabel('Willow Channel:'), 0,0)
        tmp.addWidget(self.chanLineEdit, 1,0)
        tmp.addWidget(self.startButton, 0,1, 2,1)
        tmp.addWidget(self.stopButton, 0,2, 2,1)
        self.buttonPanel.setLayout(tmp)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.buttonPanel)
        self.layout.addWidget(self.plotWidget)
        self.setLayout(self.layout)

        self.setWindowTitle('Willow Live Streaming')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))

    def setChannel(self, willowChan):
        self.willowChan = willowChan
        self.chip = self.willowChan // 32
        self.chan = self.willowChan % 32

    def startStreaming(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.setChannel(int(self.chanLineEdit.text()))
        try:
            if hwif.isStreaming():
                self.msgPosted.emit('Hardware was already streaming. Try stopping and restarting stream.')
            else:
                hwif.setSubsamples_byChip(self.chip)
                hwif.startStreaming_subsamples()
                self.toggleStdin(True)
                self.msgPosted.emit('Started streaming.')
                self.plotItem.setTitle('Willow Channel %d' % self.willowChan)
        except hwif.hwifError as e:
            self.msgPosted.emit(e.message)
        QtGui.QApplication.restoreOverrideCursor()

    def stopStreaming(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            hwif.stopStreaming()
            self.msgPosted.emit('Stopped streaming.')
        except hwif.AlreadyError:
            self.toggleStdin(False)
            self.msgPosted.emit('Already not streaming')
        except AttributeError:
            # TODO what's up with this?
            self.msgPosted.emit('AttributeError: Pipe object does not exist')
        except hwif.hwifError as e:
            self.msgPosted.emit(e.message)
        finally:
            self.toggleStdin(False)
        QtGui.QApplication.restoreOverrideCursor()

    def toggleStdin(self, enable):
        if enable:
            self.proto2bytes_po = subprocess.Popen([self.proto2bytes_filename, '-s',
                '-c', str(self.chan)], stdout=subprocess.PIPE, 
                # comment this out to view stderr in terminal (kinda useful for debugging?)
                stderr=subprocess.PIPE
                )
            self.proto2bytes_poller = select.poll()
            self.proto2bytes_poller.register(self.proto2bytes_po.stdout, select.POLLIN)
            self.timer.start(self.fp)
            print 'timer started'
        else:
            self.timer.stop()
            try:
                self.proto2bytes_po.kill()
            except AttributeError:
                pass

    def updatePlot(self):
        if self.proto2bytes_poller.poll(1000):
            for i in range(self.nrefresh):
                self.newBuff[i] = self.proto2bytes_po.stdout.readline()
            self.plotBuff = np.concatenate((self.plotBuff[self.nrefresh:],
                                            (np.array(self.newBuff, dtype=np.float)-2**15)*const.MICROVOLTS_PER_COUNT))
            self.plotCurve.setData(x=self.t_relative, y=self.plotBuff)
        else:
            self.msgPosted.emit('Read from proto2bytes timed out!')
            self.stopStreaming()

    def eventFilter(self, target, ev):
        if ev.type() == QtCore.QEvent.GraphicsSceneWheel:
            if ev.modifiers():
                if ev.modifiers() & QtCore.Qt.ControlModifier:
                    self.plotItem.axes['bottom']['item'].wheelEvent(ev)
                if ev.modifiers() & QtCore.Qt.ShiftModifier:
                    self.plotItem.axes['left']['item'].wheelEvent(ev)
            else:
                self.plotItem.axes['bottom']['item'].wheelEvent(ev)
                self.plotItem.axes['left']['item'].wheelEvent(ev)
            return True
        return False

    def closeEvent(self, event):
        try:
            if hwif.isStreaming():
                self.stopStreaming()
        except hwif.hwifError as e:
            self.msgPosted.emit(e.message)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    streamWindow = StreamWindow()
    streamWindow.show()
    sys.exit(app.exec_())
