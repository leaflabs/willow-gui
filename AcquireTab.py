import sys, os, time
from PyQt4 import QtCore, QtGui
from StreamWindow import StreamWindow
from PlotWindow import PlotWindow 
from SnapshotDialog import SnapshotParametersDialog, SnapshotProgressDialog
from StateManagement import changeState

from parameters import *
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

from StateManagement import checkState, changeState, DaemonControlError, StateChangeError

class MessageWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        super(MessageWindow, self).__init__(None)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('hello'))
        layout.addWidget(QtGui.QLabel('world'))
        self.setLayout(layout)

class AcquireTab(QtGui.QWidget):

    def __init__(self, parent):
        super(AcquireTab, self).__init__(None)
        self.parent = parent

        self.description = QtGui.QLabel(
            "<i>Control the system's Data Acquisition (DAQ) module.</i>")

        self.streamButton = QtGui.QPushButton('Launch Stream Window')
        self.streamButton.clicked.connect(self.launchStreamWindow)

        self.snapshotButton = QtGui.QPushButton('Take Snapshot')
        self.snapshotButton.clicked.connect(self.takeSnapshot)

        self.recordWidget = self.RecordWidget(self)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.description)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.streamButton)
        self.layout.addWidget(self.snapshotButton)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.recordWidget)

        self.setLayout(self.layout)

        self.plotWindows = []

    def launchStreamWindow(self):
        result, ok = QtGui.QInputDialog.getText(self, 'Configure Stream', 'Channel Number:')
        if ok:
            channel = int(result)
            chip = channel//32
            chan = channel%32
            self.streamWindow = StreamWindow(self, chip, chan)
            self.streamWindow.show()

    def takeSnapshot(self):
        nsamples, filename, plot, ok = SnapshotParametersDialog.getSnapshotParams()
        if ok:
            try:
                changeState('take snapshot', nsamples=nsamples, filename=filename)
                self.parent.statusBox.append('Snapshot complete: %s' % filename)
                if plot:
                    plotWindow = PlotWindow(self, filename, [0,nsamples-1])
                    self.plotWindows.append(plotWindow)
                    plotWindow.show()
            except StateChangeError:
                self.parent.statusBox.append("Can't take snapshot while streaming.")
            except socket.error, DaemonControlError:
                pass # error messages printed by changeState

    class RecordWidget(QtGui.QWidget):

        def __init__(self, parent):
            super(AcquireTab.RecordWidget, self).__init__() # does this work?
            self.parent = parent

            self.statusBar = QtGui.QLabel('Not Recording')
            self.statusBar.setAlignment(QtCore.Qt.AlignCenter)
            self.statusBar.setStyleSheet('QLabel {background-color: gray; font: bold}')

            self.progressBar = QtGui.QProgressBar()
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(125e6)  # TODO what is this number exactly?
            self.progressBar.setValue(0)
            
            self.startButton = QtGui.QRadioButton('Start')
            self.startButton.clicked.connect(self.startRecording)
            self.stopButton = QtGui.QRadioButton('Stop')
            self.stopButton.setChecked(True)
            self.stopButton.clicked.connect(self.stopRecording)

            self.layout = QtGui.QGridLayout()
            self.layout.addWidget(self.statusBar, 0,0,1,2)
            self.layout.addWidget(QtGui.QLabel('Disk Usage:'), 1,0,1,2)
            self.layout.addWidget(self.progressBar, 2,0,1,2)
            self.layout.addWidget(self.startButton, 3,0,1,1)
            self.layout.addWidget(self.stopButton, 3,1,1,1)

            self.setLayout(self.layout)

            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.updateProgressBar)

        def startRecording(self):
            try:
                changeState('start recording')
                self.timer.start(5000)
                self.statusBar.setText('Recording')
                self.statusBar.setStyleSheet('QLabel {background-color: red; font: bold}')
                self.parent.parent.statusBox.append('Started recording.')
            except socket.error, DaemonControlError:
                pass # error messages printed by changeState

        def stopRecording(self):
            try:
                changeState('stop recording')
                self.timer.stop()
                self.statusBar.setText('Not Recording')
                self.statusBar.setStyleSheet('QLabel {background-color: gray; font: bold}')
                self.parent.parent.statusBox.append('Stopped recording.')
            except socket.error, DaemonControlError:
                pass # error messages printed by changeState

        def updateProgressBar(self):
            resp = do_control_cmd(reg_read(2, 7)) # SATA module, Last Write Index (4B)
            if resp is None or resp.type != 255:
                self.parent.statusBox.append("%s\nNo response! Is daemon running?" % resp)
            else:
                diskIndex = resp.reg_io.val
                self.progressBar.setValue(diskIndex)
