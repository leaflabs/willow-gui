import socket, os
from PyQt4 import QtCore, QtGui
import hwif
import CustomExceptions as ex

from StreamWindow import StreamWindow
from PlotWindow import PlotWindow 
from SnapshotDialog import SnapshotDialog
from StreamDialog import StreamDialog
from PlotDialog import PlotDialog
from TransferDialog import TransferDialog

from parameters import DAEMON_DIR, DATA_DIR

class ButtonPanel(QtGui.QWidget):

    def __init__(self, statusBox):
        super(ButtonPanel, self).__init__()
        self.statusBox = statusBox

        self.streamButton = QtGui.QPushButton()
        self.streamButton.setIcon(QtGui.QIcon('../img/stream.ico'))
        self.streamButton.setIconSize(QtCore.QSize(48,48))
        self.streamButton.setToolTip('Launch Stream Window')
        self.streamButton.clicked.connect(self.launchStreamWindow)

        self.snapshotButton = QtGui.QPushButton()
        self.snapshotButton.setIcon(QtGui.QIcon('../img/snapshot.ico'))
        self.snapshotButton.setIconSize(QtCore.QSize(48,48))
        self.snapshotButton.setToolTip('Take a Snapshot')
        self.snapshotButton.clicked.connect(self.takeSnapshot)

        self.startRecordingButton = QtGui.QPushButton()
        self.startRecordingButton.setIcon(QtGui.QIcon('../img/startRecording.ico'))
        self.startRecordingButton.setIconSize(QtCore.QSize(48,48))
        self.startRecordingButton.setToolTip('Start Recording')
        self.startRecordingButton.clicked.connect(self.startRecording)

        self.stopRecordingButton = QtGui.QPushButton()
        self.stopRecordingButton.setIcon(QtGui.QIcon('../img/stopRecording.ico'))
        self.stopRecordingButton.setIconSize(QtCore.QSize(48,48))
        self.stopRecordingButton.setToolTip('Stop Recording')
        self.stopRecordingButton.clicked.connect(self.stopRecording)

        self.transferButton = QtGui.QPushButton()
        self.transferButton.setIcon(QtGui.QIcon('../img/transfer.ico'))
        self.transferButton.setIconSize(QtCore.QSize(48,48))
        self.transferButton.setToolTip('Transfer Experiment')
        self.transferButton.clicked.connect(self.transferExperiment)

        self.plotButton = QtGui.QPushButton()
        self.plotButton.setIcon(QtGui.QIcon('../img/plot.ico'))
        self.plotButton.setIconSize(QtCore.QSize(48,48))
        self.plotButton.setToolTip('Launch Plot Window')
        self.plotButton.clicked.connect(self.launchPlotWindow)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.streamButton, 0,0)
        layout.addWidget(self.snapshotButton, 0,1)
        layout.addWidget(self.startRecordingButton, 1,0)
        layout.addWidget(self.stopRecordingButton, 1,1)
        layout.addWidget(self.transferButton, 2,0)
        layout.addWidget(self.plotButton, 2,1)

        self.setLayout(layout)

    def launchStreamWindow(self):
        dlg = StreamDialog()
        if dlg.exec_():
            params = dlg.getParams()
            channel = params['channel']
            ymin = params['ymin']
            ymax = params['ymax']
            refreshRate = params['refreshRate']
            chip = channel//32
            chan = channel%32
            yrange = [ymin, ymax]
            self.streamWindow = StreamWindow(self, chip, chan, [ymin,ymax], refreshRate, self.statusBox)
            self.streamWindow.show()

    def takeSnapshot(self):
        dlg = SnapshotDialog()
        if dlg.exec_():
            params = dlg.getParams()
            nsamples_requested = params['nsamples']
            filename = params['filename']
            plot = params['plot']
            try:
                nsamples_actual = hwif.takeSnapshot(nsamples=nsamples_requested, filename=filename)
                if nsamples_actual == nsamples_requested:
                    self.statusBox.append('Snapshot complete. Saved %d samples to: %s' %
                                                    (nsamples_actual, filename))
                else:
                    self.statusBox.append('Packets dropped. Saved %d samples to: %s' %
                                                    (nsamples_actual, filename))
                if plot:
                    plotWindow = PlotWindow(self, filename, [0,nsamples_actual-1])
                    plotWindow.show()
            except ex.StateChangeError:
                self.statusBox.append("Can't take snapshot while streaming.")
            except socket.error:
                self.statusBox.append('Socket error: Could not connect to daemon.')
            except tuple(ex.ERROR_DICT.values()) as e:
                self.statusBox.append('Error: %s' % e)

    def startRecording(self):
        try:
            hwif.startRecording()
            self.statusBox.append('Started recording.')
        except ex.AlreadyError:
            self.statusBox.append('Already recording.')
        except socket.error:
            self.statusBox.append('Socket error: Could not connect to daemon.')
        except tuple(ex.ERROR_DICT.values()) as e:
            self.statusBox.append('Error: %s' % e)

    def stopRecording(self):
        try:
            hwif.stopRecording()
            self.statusBox.append('Stopped recording.')
        except ex.AlreadyError:
            self.statusBox.append('Already not recording.')
        except socket.error:
            self.statusBox.append('Socket error: Could not connect to daemon.')
        except tuple(ex.ERROR_DICT.values()) as e:
            self.statusBox.append('Error: %s' % e)

    def transferExperiment(self):
        dlg = TransferDialog()
        if dlg.exec_():
            params = dlg.getParams()
            nsamples = params['nsamples']
            filename = params['filename']
            if not filename:
                filename = os.path.join(DATA_DIR, 'test_transfer.h5') # TODO
            try:
                if (nsamples==None) and (hwif.doRegRead(3,3)==0):
                    self.statusBox.append('Error: Could not transfer experiment because BSI is missing.')
                    self.statusBox.append('Please specify nsamples in the Transfer Dialog and try again.')
                else:
                    hwif.doTransfer(nsamples, filename)
                    self.statusBox.append('Transfer complete: %s' % filename)
            except ex.NoResponseError:
                # should not get this anymore; delete after confirming
                self.statusBox.append('NoResponseError - Weird!')
            except ex.StateChangeError:
                self.statusbox.append('Cannot do transfer while recording or streaming')
            except socket.error:
                self.statusBox.append('Socket error: Could not connect to daemon.')
            except tuple(ex.ERROR_DICT.values()) as e:
                self.statusBox.append('Error: %s' % e)

    def launchPlotWindow(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Import Data File', DATA_DIR)
        if filename:
            dlg = PlotDialog()
            if dlg.exec_():
                params = dlg.getParams()
                sampleRange = params['sampleRange']
                plotWindow = PlotWindow(self, str(filename), sampleRange)
                plotWindow.show()
