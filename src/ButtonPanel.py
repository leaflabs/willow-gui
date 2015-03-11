import socket, os, datetime
from PyQt4 import QtCore, QtGui
import hwif
import CustomExceptions as ex

from StreamWindow import StreamWindow
from PlotWindow import PlotWindow 
from SnapshotDialog import SnapshotDialog
from StreamDialog import StreamDialog

from SnapshotThread import SnapshotThread

from ImportDialog import ImportDialog
from ImportThread import ImportThread

from TransferDialog import TransferDialog
from TransferThread import TransferThread

from ImpedanceDialog import ImpedanceDialog
from ImpedanceThread import ImpedanceThread
from ImpedancePlotWindow import ImpedancePlotWindow

from SettingsWindow import SettingsWindow

import config

import h5py

from WillowDataset import WillowDataset

def isSampleRangeValid(sampleRange):
    if isinstance(sampleRange, list) and (len(sampleRange)==2):
        if (sampleRange[1]>sampleRange[0]) and (sampleRange[0]>=0):
            return True
        else:
            return False
    elif sampleRange==-1:
        return True
    else:
        return False

def targetDirExists(filename):
    targetDir = os.path.split(filename)[0]
    return os.path.exists(targetDir)

class ButtonPanel(QtGui.QWidget):

    def __init__(self, msgLog):
        super(ButtonPanel, self).__init__()
        self.msgLog = msgLog

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
        self.plotButton.clicked.connect(self.plotData)

        self.impedanceButton = QtGui.QPushButton()
        self.impedanceButton.setIcon(QtGui.QIcon('../img/impedance.png'))
        self.impedanceButton.setIconSize(QtCore.QSize(48,48))
        self.impedanceButton.setToolTip('Run Impedance Test')
        self.impedanceButton.clicked.connect(self.runImpedanceTest)

        self.settingsButton = QtGui.QPushButton()
        self.settingsButton.setIcon(QtGui.QIcon('../img/settings.png'))
        self.settingsButton.setIconSize(QtCore.QSize(48,48))
        self.settingsButton.setToolTip('Configure Settings')
        self.settingsButton.clicked.connect(self.configureSettings)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.streamButton, 0,0)
        layout.addWidget(self.snapshotButton, 0,1)
        layout.addWidget(self.startRecordingButton, 1,0)
        layout.addWidget(self.stopRecordingButton, 1,1)
        layout.addWidget(self.transferButton, 2,0)
        layout.addWidget(self.plotButton, 2,1)
        layout.addWidget(self.impedanceButton, 3,0)
        layout.addWidget(self.settingsButton, 3,1)

        self.setLayout(layout)

    def runImpedanceTest(self):
        dlg = ImpedanceDialog()
        if dlg.exec_():
            params = dlg.getParams()
            self.impedanceProgressDialog = QtGui.QProgressDialog('Impedance Testing Progress', 'Cancel', 0, 10)
            self.impedanceProgressDialog.setAutoReset(False)
            self.impedanceProgressDialog.setMinimumDuration(0)
            self.impedanceProgressDialog.setModal(False)
            self.impedanceProgressDialog.setWindowTitle('Impedance Testing Progress')
            self.impedanceProgressDialog.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
            self.impedanceThread = ImpedanceThread(params)
            self.impedanceThread.progressUpdated.connect(self.impedanceProgressDialog.setValue)
            self.impedanceThread.maxChanged.connect(self.impedanceProgressDialog.setMaximum)
            self.impedanceThread.textChanged.connect(self.impedanceProgressDialog.setLabelText)
            self.impedanceThread.finished.connect(self.impedanceProgressDialog.reset)
            self.impedanceThread.msgPosted.connect(self.postStatus)
            self.impedanceThread.dataReady.connect(self.launchImpedancePlotWindow)
            self.impedanceProgressDialog.canceled.connect(self.impedanceThread.handleCancel)
            self.impedanceProgressDialog.show()
            self.impedanceThread.start()

    def configureSettings(self):
        self.settingsWindow = SettingsWindow()
        self.settingsWindow.show()

    def launchStreamWindow(self):
        dlg = StreamDialog()
        if dlg.exec_():
            params = dlg.getParams()
            self.streamWindow = StreamWindow(params, self.msgLog)
            self.streamWindow.show()

    def takeSnapshot(self):
        dlg = SnapshotDialog()
        if dlg.exec_():
            params = dlg.getParams()
            self.snapshotThread = SnapshotThread(params)
            self.snapshotProgressDialog = QtGui.QProgressDialog('Taking Snapshot..', 'Cancel', 0, 0)
            self.snapshotProgressDialog.setWindowTitle('Snapshot Progress')
            self.snapshotProgressDialog.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
            self.snapshotProgressDialog.canceled.connect(self.snapshotThread.handleCancel)
            self.snapshotThread.msgPosted.connect(self.postStatus) # TODO see others
            self.snapshotThread.importFinished.connect(self.launchPlotWindow)
            self.snapshotThread.labelChanged.connect(self.snapshotProgressDialog.setLabelText)
            self.snapshotThread.maxChanged.connect(self.snapshotProgressDialog.setMaximum)
            self.snapshotThread.progressUpdated.connect(self.snapshotProgressDialog.setValue)
            self.snapshotThread.finished.connect(self.snapshotProgressDialog.reset) # necessary?
            self.snapshotProgressDialog.show()
            self.snapshotThread.start()


    def startRecording(self):
        try:
            hwif.startRecording()
            self.msgLog.post('Started recording.')
        except hwif.AlreadyError:
            self.msgLog.post('Already recording.')
        except hwif.hwifError as e:
            self.msgLog.post(e.message)

    def stopRecording(self):
        try:
            hwif.stopRecording()
            self.msgLog.post('Stopped recording.')
        except hwif.AlreadyError:
            self.msgLog.post('Already not recording.')
        except hwif.hwifError as e:
            self.msgLog.post(e.message)

    def transferExperiment(self):
        dlg = TransferDialog()
        if dlg.exec_():
            params = dlg.getParams()
            sampleRange = params['sampleRange']
            filename = params['filename'] # this is an absolute filename, or False
            if not isSampleRangeValid(sampleRange):
                self.msgLog.post('Sample range not valid: [%d, %d]' % tuple(sampleRange))
                return
            if isinstance(filename, str) and (not targetDirExists(filename)):
                self.msgLog.post('Target directory does not exist: %s' % os.path.split(filename)[0])
                return
            self.transferThread = TransferThread(filename, sampleRange)
            self.transferProgressDialog = QtGui.QProgressDialog('Transfering Experiment..', 'Cancel', 0, 0)
            self.transferProgressDialog.setWindowTitle('Transfer Progress')
            self.transferProgressDialog.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
            self.transferProgressDialog.setModal(True)
            self.transferProgressDialog.canceled.connect(self.transferThread.handleCancel)
            self.transferThread.statusUpdated.connect(self.postStatus)
            self.transferThread.finished.connect(self.transferProgressDialog.reset)
            self.transferProgressDialog.show()
            self.transferThread.start()

    def postStatus(self, msg):
        self.msgLog.post(msg)

    def plotData(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Import Data File', config.dataDir)
        if filename:
            filename = str(filename)
            dlg = ImportDialog()
            if dlg.exec_():
                params = dlg.getParams()
                sampleRange = params['sampleRange']
                if not isSampleRangeValid(sampleRange):
                    self.msgLog.post('Sample range not valid: [%d, %d]' % tuple(sampleRange))
                    return
                try:
                    dataset = WillowDataset(filename, sampleRange)
                    self.importProgressDialog = QtGui.QProgressDialog('Importing %s' % filename,
                        'Cancel', 0, dataset.nsamples)
                    self.importProgressDialog.setMinimumDuration(1000)
                    self.importProgressDialog.setModal(False)
                    self.importProgressDialog.setWindowTitle('Data Import Progress')
                    self.importProgressDialog.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
                    self.importThread = ImportThread(dataset)
                    self.importThread.progressUpdated.connect(self.importProgressDialog.setValue)
                    self.importThread.msgPosted.connect(self.postStatus) # TODO convert these to postMessage name
                    self.importThread.finished.connect(self.launchPlotWindow)
                    self.importThread.canceled.connect(self.importProgressDialog.cancel)
                    self.importProgressDialog.canceled.connect(self.importThread.terminate)
                    self.importProgressDialog.show()
                    self.importThread.start()
                except IndexError as e:
                    self.msgLog.post(e.message)

    def launchPlotWindow(self, willowDataset):
        self.plotWindow = PlotWindow(willowDataset)
        self.plotWindow.show()

    def launchImpedancePlotWindow(self, impedanceMeasurements):
        self.impedancePlotWindow = ImpedancePlotWindow(impedanceMeasurements)
        self.impedancePlotWindow.show()
        
