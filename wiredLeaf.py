#!/usr/bin/python
"""
WiredLeaf Control Panel GUI
Chris Chronopoulos, 20140522
"""

import sys, subprocess
from PyQt4 import QtCore, QtGui

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np

DAEMON_DIR = '/home/chrono/sng/sng-daemon/'

class SetupTab(QtGui.QWidget):

    def __init__(self, parent):
        super(SetupTab, self).__init__(None)
        self.parent = parent

        self.daemonCheckbox = QtGui.QCheckBox('Daemon Running')
        self.daemonCheckbox.stateChanged.connect(self.toggleDaemon)

        self.ethConfigButton = QtGui.QPushButton('Expand Ethernet Buffers')
        self.ethConfigButton.clicked.connect(self.configureEthernet)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.daemonCheckbox)
        self.layout.addWidget(self.ethConfigButton)
        self.setLayout(self.layout)

    def toggleDaemon(self):

        if self.daemonCheckbox.isChecked():
            subprocess.call([DAEMON_DIR+'build/leafysd', '-A', '192.168.1.2'])
            self.parent.statusBox.setText('Daemon started')
        else:
            subprocess.call(['killall', 'leafysd'])
            self.parent.statusBox.setText('Daemon stopped')
        pass

    def configureEthernet(self):
        """
        Probably this should just be run on init()
        """

        subprocess.call(DAEMON_DIR+'util/expand_eth_buffers.sh')
        self.parent.statusBox.setText('Ethernet buffers expanded!')


class RecordTab(QtGui.QWidget):

    def __init__(self, parent):
        super(RecordTab, self).__init__(None)
        self.parent = parent

        self.nsampLine = QtGui.QLineEdit('30000')
        self.dirLine = QtGui.QLineEdit('/home/chrono/sng/data')
        self.filenameLine = QtGui.QLineEdit()
        self.recordButton = QtGui.QPushButton('Record Data')
        self.recordButton.clicked.connect(self.recordData)
        self.plotButton = QtGui.QPushButton('Plot Most Recent')
        self.plotButton.clicked.connect(self.plotRecent)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel('Number of Samples:'))
        self.layout.addWidget(self.nsampLine)
        self.layout.addWidget(QtGui.QLabel('Directory:'))
        self.layout.addWidget(self.dirLine)
        self.layout.addWidget(QtGui.QLabel('Filename:'))
        self.layout.addWidget(self.filenameLine)
        self.layout.addWidget(self.recordButton)
        self.layout.addWidget(self.plotButton)
        self.layout.addStretch(1)

        self.setLayout(self.layout)

    def recordData(self):
        DATA_DIR = self.dirLine.text()
        if DATA_DIR[-1] != '/':
            DATA_DIR = DATA_DIR + '/'
        filename = self.filenameLine.text()
        nsamp = self.nsampLine.text()
        status1 = subprocess.call([DAEMON_DIR+'util/acquire.py', 'start'])
        status2 = subprocess.call([DAEMON_DIR+'util/acquire.py', 'save_stream', DATA_DIR+filename, nsamp])
        status3 = subprocess.call([DAEMON_DIR+'util/acquire.py', 'stop'])
        if (status1==1 or status2==1 or status3==1):
            self.parent.statusBox.setText('Error')
        else:
            self.parent.statusBox.setText('Saved '+nsamp+' samples to: '+DATA_DIR+filename)
            self.mostRecentFilename = DATA_DIR+filename

    def plotRecent(self):
        self.parent.statusBox.setText('This does nothing yet')


class StreamTab(QtGui.QWidget):

    def __init__(self, parent):
        super(StreamTab, self).__init__(None)
        self.parent = parent

        self.streamCheckbox = QtGui.QCheckBox('Stream Data')
        self.streamCheckbox.stateChanged.connect(self.toggleStream)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.streamCheckbox)
        self.setLayout(self.layout)

    def toggleStream(self):
        if self.streamCheckbox.isChecked():
            self.parent.timer.start(500)
            self.parent.statusBox.setText('Started streaming')
        else:
            self.parent.timer.stop()
            self.parent.statusBox.setText('Stopped streaming')

class MainWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setup()
        self.drawFlatline()

    def setup(self):

        # TODO sort out sizing policies with this logo..
        self.logo = QtGui.QLabel()
        self.logo.setPixmap(QtGui.QPixmap('round_logo_60x60_text.png'))
        #self.logo.setPixmap(QtGui.QPixmap('newLogo.png'))
        #self.logo.setAlignment(QtCore.Qt.AlignHCenter)
        logoscale = 0.3
        self.logo.setMaximumSize(QtCore.QSize(825*logoscale,450*logoscale))
        #self.logo.setScaledContents(True)
        #self.logo.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)

        self.tabDialog = QtGui.QTabWidget()
        self.tabDialog.addTab(SetupTab(self), 'Setup')
        self.tabDialog.addTab(StreamTab(self), 'Stream')
        self.tabDialog.addTab(RecordTab(self), 'Record')

        self.leftColumn = QtGui.QWidget()
        tmp = QtGui.QVBoxLayout()
        tmp.addWidget(self.logo)
        tmp.addWidget(self.tabDialog)
        self.leftColumn.setLayout(tmp)

        ###

        self.fig = Figure((5.0, 4.0), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_title('Data Window')
        self.axes.set_xlabel('Samples')
        self.axes.set_ylabel('Counts')
        self.axes.axis([0,30000,0,2**16-1])
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.mplLayout = QtGui.QVBoxLayout()
        self.mplLayout.addWidget(self.canvas)
        self.mplLayout.addWidget(self.mpl_toolbar)
        self.mplWindow = QtGui.QWidget()
        self.mplWindow.setLayout(self.mplLayout)

        ###

        self.LRSplitter = QtGui.QSplitter()
        self.LRSplitter.addWidget(self.leftColumn)
        self.LRSplitter.addWidget(self.mplWindow)

        ###

        self.statusBox = QtGui.QLabel('Status Box')

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.LRSplitter)
        mainLayout.addWidget(self.statusBox)

        self.setLayout(mainLayout)
        self.setWindowTitle('WiredLeaf Control Panel')
        self.setWindowIcon(QtGui.QIcon('round_logo_60x60.png'))

        ### Timer Shit

        self.xvalues = np.arange(30000)
        self.flatline = np.array([2**15]*30000)
        self.sinewave = np.sin(self.xvalues/1000.)*10000+2**15

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timerCallback)

        self.state = True

    def timerCallback(self):
        if self.state:
            self.waveform[0].set_data(self.xvalues, self.sinewave)
            self.canvas.draw()
        else:
            self.waveform[0].set_data(self.xvalues, self.flatline)
            self.canvas.draw()
        self.state = not self.state
            

    def drawFlatline(self):
        self.waveform = self.axes.plot(self.xvalues, self.flatline)
        self.canvas.draw()


if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec_()

