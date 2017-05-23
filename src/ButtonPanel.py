from PyQt4 import QtCore, QtGui
import os, h5py

import hwif

from StreamPickDialog import StreamPickDialog
from StreamHandler import StreamHandler
from StreamWindow import StreamWindow
from StreamDialog import StreamDialog

from DataExplorerWindow import DataExplorerWindow

from SnapshotDialog import SnapshotDialog
from SnapshotThread import SnapshotThread
from SnapshotAnalysisThread import SnapshotAnalysisThread

from ImportDialog import SnapshotImportDialog

from TransferDialog import TransferDialog
from TransferThread import TransferThread

from ImpedanceDialog import ImpedanceDialog
from ImpedanceThread import ImpedanceThread
from ImpedancePlotWindow import ImpedancePlotWindow

from SettingsWindow import SettingsWindow

from WillowDataset import WillowDataset

import config

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

def isCalibrationFile(filename):
    f = h5py.File(filename)
    return 'impedanceMeasurements' in f.keys()

def isSnapshotFile(filename):
    dataset = WillowDataset(filename, -1)
    return dataset.type == 'snapshot'

class ButtonPanel(QtGui.QWidget):

    logPackageRequested = QtCore.pyqtSignal()

    def __init__(self, msgLog):
        super(ButtonPanel, self).__init__()

        self.msgLog = msgLog
        self.streamWindow = None
        self.settingsWindow = None

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
        self.impedanceButton.clicked.connect(self.handleImpedanceStart)

        self.settingsButton = QtGui.QPushButton()
        self.settingsButton.setIcon(QtGui.QIcon('../img/settings.png'))
        self.settingsButton.setIconSize(QtCore.QSize(48,48))
        self.settingsButton.setToolTip('Configure Settings')
        self.settingsButton.clicked.connect(self.configureSettings)

        self.logPackageLabel = QtGui.QLabel('Zip error logs (for bug reporting)')
        self.logPackageButton = QtGui.QPushButton('Zip logs')
        self.logPackageButton.pressed.connect(self.logPackageRequested)

        layout = QtGui.QVBoxLayout()
        logPackageLayout = QtGui.QGridLayout()
        logPackageLayout.addWidget(self.logPackageLabel, 0,0)
        logPackageLayout.addWidget(self.logPackageButton, 0,1)
        layout.addLayout(logPackageLayout)

        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(self.streamButton, 0,0)
        gridLayout.addWidget(self.snapshotButton, 0,1)
        gridLayout.addWidget(self.startRecordingButton, 1,0)
        gridLayout.addWidget(self.stopRecordingButton, 1,1)
        gridLayout.addWidget(self.transferButton, 2,0)
        gridLayout.addWidget(self.plotButton, 2,1)
        gridLayout.addWidget(self.impedanceButton, 3,0)
        gridLayout.addWidget(self.settingsButton, 3,1)
        layout.addLayout(gridLayout)

        self.subprocessThreads = []

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
        dlg = StreamPickDialog()
        if dlg.exec_():
            streamChoice = dlg.getChoice()
            if streamChoice == 'default':
                self.msgLog.post(str("default streaming window chosen"), 
                        log=self.msgLog.actionLog)
                # request parameters
                dlg = StreamDialog()
                if dlg.exec_():
                    params = dlg.getParams()
                    self.msgLog.post(str("the following streaming params requested:"+"\n"+str(params)),
                        log=self.msgLog.actionLog)
                    self.streamWindow = StreamWindow(params, self.msgLog)
                    self.streamWindow.show()
            else:
                self.msgLog.post(str("the following streaming script chosen:"+"\n"+str(streamChoice)),
                    log=self.msgLog.actionLog)
                self.streamHandler = StreamHandler(streamChoice)
                self.streamHandler.msgPosted.connect(self.postStatus)
                self.streamHandler.run()

    def takeSnapshot(self):
        dlg = SnapshotDialog()
        if dlg.exec_():
            params = dlg.getParams()
            self.msgLog.post(str("the following snapshot params requested:"+"\n"+str(params)),
                log=self.msgLog.actionLog)
            self.snapshotThread = SnapshotThread(params)
            self.snapshotProgressDialog = QtGui.QProgressDialog('Taking Snapshot..', 'Cancel', 0, 0)
            self.snapshotProgressDialog.setWindowTitle('Snapshot Progress')
            self.snapshotProgressDialog.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
            self.snapshotProgressDialog.canceled.connect(self.snapshotThread.handleCancel)
            self.snapshotThread.msgPosted.connect(self.postStatus) # TODO see others
            self.snapshotThread.finished.connect(self.snapshotProgressDialog.reset) # necessary?
            self.snapshotThread.finished.connect(self.handleSnapshotFinished)
            self.snapshotProgressDialog.show()
            self.snapshotThread.start()

    def handleSnapshotFinished(self, params):
        finalAction = params['whenFinished'][0]
        if finalAction == -3: # "willowgui data explorer"
            self.launchPlotWindow(params['filename'])
        elif finalAction == -4: # custom script
            sat = SnapshotAnalysisThread(params)
            sat.msgPosted.connect(self.postStatus)
            self.subprocessThreads.append(sat) # necessary to prevent garbage collection
            sat.start()

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

    def handleImpedanceStart(self):
        try:
            if hwif.isRecording():
                self.msgLog.post('Cannot check impedance while recording. Please complete recording and try again.')
                return
            elif hwif.isStreaming():
                self.msgLog.post('Halting current data stream to perform impedance test.')
                self.streamWindow.stopStreaming()
                self.runImpedanceTest()
            else:
                self.runImpedanceTest()
        except hwif.hwifError as e:
            self.msgLog.post(e.message)

    def handleDiskFillup(self):
        try:
            hwif.stopRecording()
            diskIndex = hwif.getSataBSI()
            self.msgLog.post('Disk fillup detected! Recording stopped at disk index %d' % diskIndex)
        except hwif.AlreadyError:
            self.msgLog.post('Already not recording.')
        except hwif.hwifError as e:
            self.msgLog.post(e.message)

    def transferExperiment(self):
        dlg = TransferDialog()
        if dlg.exec_():
            params = dlg.getParams()
            self.msgLog.post(str("the following transfer params requested:"+"\n"+str(params)),
                    log=self.msgLog.actionLog)
            self.transferThread = TransferThread(params)
            self.transferProgressDialog = QtGui.QProgressDialog('Transferring Experiment..', 'Cancel', 0, 0)
            self.transferProgressDialog.setWindowTitle('Transfer Progress')
            self.transferProgressDialog.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
            self.transferProgressDialog.setModal(True)  #TODO setup protection so that this can be non-modal
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
            self.msgLog.post(str("imported:"+"\n"+filename),
                    log=self.msgLog.actionLog)
            if isCalibrationFile(filename):
                self.msgLog.post("(calibration file)",
                        log=self.msgLog.actionLog)
                self.launchImpedancePlotWindow(filename)
            elif isSnapshotFile(filename):
                self.msgLog.post("(snapshot file)",
                        log=self.msgLog.actionLog)
                dlg = SnapshotImportDialog()
                if dlg.exec_():
                    params = dlg.getParams()
                    if params['customScript']:
                        # TODO make this consistent with the original SAI routines
                        params['filename'] = filename
                        params['whenFinished'] = (-4, params['customScript'])
                        sat = SnapshotAnalysisThread(params)
                        sat.msgPosted.connect(self.postStatus)
                        self.subprocessThreads.append(sat) # necessary to prevent garbage collection
                        sat.start()
                    else:
                        self.launchPlotWindow(filename)
            else:
                self.msgLog.post("(experiment file)",
                        log=self.msgLog.actionLog)
                self.launchPlotWindow(filename)

    def launchPlotWindow(self, filename):
        self.plotWindow = DataExplorerWindow(filename)
        self.plotWindow.show()

    def launchImpedancePlotWindow(self, filename):
        self.impedancePlotWindow = ImpedancePlotWindow(str(filename))
        self.impedancePlotWindow.show()
        
