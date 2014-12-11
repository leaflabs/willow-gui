import sys, os, time
from PyQt4 import QtCore, QtGui
from StreamWindow import StreamWindow
from PlotWindow import PlotWindow 
from SnapshotDialog import SnapshotParametersDialog, SnapshotProgressDialog
from StreamDialog import StreamDialog
from StateManagement import changeState

from parameters import *
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

import hwif
import CustomExceptions as ex

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

        self.startRecordButton = QtGui.QPushButton('Start Recording')
        self.startRecordButton.clicked.connect(self.startRecording)

        self.stopRecordButton = QtGui.QPushButton('Stop Recording')
        self.stopRecordButton.clicked.connect(self.stopRecording)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addSpacing(20)
        self.layout.addWidget(self.description)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.streamButton)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.snapshotButton)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.startRecordButton)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.stopRecordButton)

        self.setLayout(self.layout)

    def launchStreamWindow(self):
        channel, ymin, ymax, refreshRate, ok = StreamDialog.getParams()
        if ok:
            chip = channel//32
            chan = channel%32
            yrange = [ymin, ymax]
            self.streamWindow = StreamWindow(self, chip, chan, [ymin,ymax], refreshRate)
            self.streamWindow.show()

    def takeSnapshot(self):
        nsamples_requested, filename, plot, ok = SnapshotParametersDialog.getSnapshotParams()
        if ok:
            try:
                nsamples_actual = hwif.takeSnapshot(nsamples=nsamples_requested, filename=filename)
                if nsamples_actual == nsamples_requested:
                    self.parent.statusBox.append('Snapshot complete. Saved %d samples to: %s' %
                                                    (nsamples_actual, filename))
                else:
                    self.parent.statusBox.append('Packets dropped. Saved %d samples to: %s' %
                                                    (nsamples_actual, filename))
                if plot:
                    plotWindow = PlotWindow(self, filename, [0,nsamples_actual-1])
                    plotWindow.show()
            except ex.StateChangeError:
                self.parent.statusBox.append("Can't take snapshot while streaming.")
            except socket.error:
                self.parent.statusBox.append('Socket error: Could not connect to daemon.')
            except tuple(ex.ERROR_DICT.values()) as e:
                self.parent.statusBox.append('Error: %s' % e)

    def startRecording(self):
        try:
            hwif.startRecording()
            self.timer.start(5000)
            self.parent.statusBox.append('Started recording.')
        except ex.AlreadyError:
            self.parent.statusBox.append('Already recording.')
            self.timer.start(5000)
        except socket.error:
            self.parent.statusBox.append('Socket error: Could not connect to daemon.')
        except tuple(ex.ERROR_DICT.values()) as e:
            self.parent.statusBox.append('Error: %s' % e)

    def stopRecording(self):
        try:
            hwif.stopRecording()
            self.timer.stop()
            self.parent.statusBox.append('Stopped recording.')
        except ex.AlreadyError:
            self.parent.statusBox.append('Already not recording.')
            self.timer.stop()
        except socket.error:
            self.parent.statusBox.append('Socket error: Could not connect to daemon.')
        except tuple(ex.ERROR_DICT.values()) as e:
            self.parent.statusBox.append('Error: %s' % e)
