#!/usr/bin/python
"""
WiredLeaf Control Panel GUI
Chris Chronopoulos, 20140522
"""

import sys, time, subprocess
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

        # Test keypress
        self.keypressCheckbox = QtGui.QCheckBox('Test Keypress')
        self.shcut = QtGui.QShortcut(self)
        self.shcut.setKey("space")
        self.shcut.activated.connect(self.handleKeypress)

        self.ethConfigButton = QtGui.QPushButton('Expand Ethernet Buffers')
        self.ethConfigButton.clicked.connect(self.configureEthernet)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.daemonCheckbox)
        self.layout.addWidget(self.keypressCheckbox)
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

        self.parent.statusBox.setText('Please enter password in terminal..')
        subprocess.call(DAEMON_DIR+'util/expand_eth_buffers.sh')
        self.parent.statusBox.setText('Ethernet buffers expanded!')

    def handleKeypress(self):
        if self.keypressCheckbox.isChecked():
            self.keypressCheckbox.setChecked(False)
        else:
            self.keypressCheckbox.setChecked(True)



class StreamTab(QtGui.QWidget):

    def __init__(self, parent):
        super(StreamTab, self).__init__(None)
        self.parent = parent

        self.chipNumLine = QtGui.QLineEdit('3')
        self.channelNumLine = QtGui.QLineEdit('3')

        self.standbyCheckbox = QtGui.QCheckBox('Standby')
        self.standbyCheckbox.clicked.connect(self.toggleStandby)

        self.streamCheckbox = QtGui.QCheckBox('Stream')
        self.streamCheckbox.stateChanged.connect(self.toggleStream)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel('Chip Number:'))
        self.layout.addWidget(self.chipNumLine)
        self.layout.addWidget(QtGui.QLabel('Channel Number:'))
        self.layout.addWidget(self.channelNumLine)
        self.layout.addSpacing(100)
        self.layout.addWidget(self.standbyCheckbox)
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

    def toggleStandby(self):
        """
        Decided to separate out standby mode because the setup is kind of slow (~5 seconds)
        and you probably only want to do this occasionally, while starting/stopping the stream
        you would do more frequently, without having to wait.
        """
        if self.parent.setupTab.daemonCheckbox.isChecked():
            if self.standbyCheckbox.isChecked():
                subprocess.call([DAEMON_DIR+'util/acquire.py', 'subsamples', '--constant', 'chip', self.chipNumLine.text()])
                subprocess.call([DAEMON_DIR+'util/acquire.py', 'start'])
                subprocess.call([DAEMON_DIR+'util/acquire.py', 'forward', 'start', '-f', '-t', 'subsample'])
                self.parent.statusBox.setText('Standby mode activated')
            else:
                subprocess.call([DAEMON_DIR+'util/acquire.py', 'stop'])
                self.parent.statusBox.setText('Standby mode de-activated')
        else:
            #TODO gray-out the checkbox when the daemon is not running
            self.parent.statusBox.setText('Please start daemon first!')
            self.standbyCheckbox.setChecked(False)
                

    def toggleStream(self):
        """
        This works as long as the daemon was started externally,
        and the GUI was started with data piped in from proto2bytes:

        $ ~/sng/sng-daemon/build/proto2bytes -s -c 3 | ./wiredLeaf.py

        otherwise, this will crash the GUI.
        """
        if self.parent.setupTab.daemonCheckbox.isChecked():
            if self.streamCheckbox.isChecked():
                self.proto2bytes_po = subprocess.Popen([DAEMON_DIR+'build/proto2bytes', '-s', '-c', self.channelNumLine.text()], stdout=subprocess.PIPE)
                self.timer.start(self.fp)
                self.parent.statusBox.setText('Started streaming')
            else:
                self.timer.stop()
                self.proto2bytes_po.kill()
                self.parent.statusBox.setText('Stopped streaming')
        else:
            #TODO gray-out the checkbox when the daemon is not running
            self.parent.statusBox.setText('Please start daemon first!')
            self.streamCheckbox.setChecked(False)



    def updatePlot(self):
        for i in range(self.nrefresh):
            self.newBuff[i] = self.proto2bytes_po.stdout.readline()
        self.plotBuff = np.concatenate((self.plotBuff[self.nrefresh:],self.newBuff))
        self.parent.waveform[0].set_data(self.xvalues, self.plotBuff)
        self.parent.canvas.draw()


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


class DiskTab(QtGui.QWidget):

    def __init__(self, parent):
        super(DiskTab, self).__init__(None)
        self.parent = parent

        self.placeholderMessage = QtGui.QLabel("Disk utility coming soon!")

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.placeholderMessage)
        self.setLayout(self.layout)


class MainWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setup()

    def setup(self):

        # TODO sort out sizing policies with this logo..
        self.logo = QtGui.QLabel()
        #self.logo.setPixmap(QtGui.QPixmap('round_logo_60x60_text.png'))
        self.logo.setPixmap(QtGui.QPixmap('newlogo.png'))
        self.logo.setAlignment(QtCore.Qt.AlignHCenter)
        #logoscale = 2.
        #self.logo.setMaximumSize(QtCore.QSize(825*logoscale,450*logoscale))
        #self.logo.setScaledContents(True)
        #self.logo.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)

        self.tabDialog = QtGui.QTabWidget()
        self.setupTab = SetupTab(self)
        self.tabDialog.addTab(self.setupTab, 'Setup')
        self.streamTab = StreamTab(self)
        self.tabDialog.addTab(self.streamTab, 'Stream')
        self.recordTab = RecordTab(self)
        self.tabDialog.addTab(self.recordTab, 'Record')
        self.diskTab = DiskTab(self)
        self.tabDialog.addTab(self.diskTab, 'Disk')

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
        self.axes.set_axis_bgcolor('k')
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
        self.resize(1000,500)

        ###

        self.waveform = self.axes.plot(np.arange(30000), np.array([2**15]*30000), color='y')
        self.canvas.draw()

    def testRTPlotting(self):
        if self.state:
            self.waveform[0].set_data(self.xvalues, self.sinewave)
            self.canvas.draw()
        else:
            self.waveform[0].set_data(self.xvalues, self.flatline)
            self.canvas.draw()
        self.state = not self.state


if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec_()

