import socket
from PyQt4 import QtCore, QtGui
import hwif
from WatchdogThread import WatchdogThread
import config
import datetime, time

import pprint

GOOD_STYLE = 'QLabel {background-color: #8fdb90; font: bold}'
UNKNOWN_STYLE = 'QLabel {background-color: gray; font: bold}'
BAD_STYLE = 'QLabel {background-color: orange; font: bold}'
STREAM_STYLE = 'QLabel {background-color: rgb(0,191,255); font: bold}'
RECORD_STYLE = 'QLabel {background-color: red; font: bold}'

MAX_DISK_INDEX = 250e3*config.storageCapacity_GB
DISK_FILLUP_FRACTION = 0.97


CENTRAL_ERRORDICT = {
    0 : 'Configuration Error'
}

SATA_ERRORDICT = {
    0 :  'Configuration Error',
    1 :  'Disk Not Ready',
    2 :  'SATA-UDP FIFO Underflow',
    3 :  'SATA-UDP FIFO Overflow',
    4 :  'SATA Read FIFO Underflow',
    5 :  'SATA Read FIFO Overflow',
    6 :  'Disk Removed',
    7 :  'Other error',
    8 :  'Low-Level SATA Error' # (see bits 23:16)
}

DAQ_ERRORDICT = {
    0 :  'Configuration Error',
    1 :  'DAQ-UDP FIFO Underflow',
    2 :  'DAQ-UDP FIFO Overflow',
    3 :  'DAQ-SATA FIFO Underflow',
    4 :  'DAQ-SATA FIFO Overflow'
}

UDP_ERRORDICT = {
    0 : 'Configuration Error',
    7 : 'Other Error'
}

GPIO_ERRORDICT = {
    0 : 'Configuration error'
}

ERRORDICT_DICT = {
    1 : ('Central', CENTRAL_ERRORDICT),
    2 : ('SATA', SATA_ERRORDICT),
    3 : ('DAQ', DAQ_ERRORDICT),
    4 : ('UDP', UDP_ERRORDICT),
    5 : ('GPIO', GPIO_ERRORDICT)
}

class DaemonRestartDialog(QtGui.QDialog):

    daemonRestartPasser = QtCore.pyqtSignal()
    daemonDontRestartPasser = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(DaemonRestartDialog, self).__init__(parent)

        label = QtGui.QLabel('Daemon died. Manually restart?\n(Strongly recommended)')
        label.setAlignment(QtCore.Qt.AlignHCenter)
        
        dialogButtons = QtGui.QWidget()
        OkButton = QtGui.QPushButton("OK")
        OkButton.pressed.connect(self.okHandler)
        CancelButton = QtGui.QPushButton("Cancel")
        CancelButton.pressed.connect(self.cancelHandler)
        dialogButtonsLayout = QtGui.QHBoxLayout()
        dialogButtonsLayout.addWidget(OkButton)
        dialogButtonsLayout.addWidget(CancelButton)
        dialogButtons.setLayout(dialogButtonsLayout)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(dialogButtons)

        self.setLayout(layout)
        self.setWindowTitle('Daemon control')
        self.resize(200,100)

    def okHandler(self):
        self.daemonRestartPasser.emit()
        self.close()

    def cancelHandler(self):
        self.daemonDontRestartPasser.emit()
        self.close()

def getErrorInfo(errorRegister):
    infoText = ''
    for i in range(1,6):
        if (errorRegister & 1<<i):
            moduleName, errorDict = ERRORDICT_DICT[i]
            errorBitmask = hwif.getErrorBitmask(i)
            for j in range(9):
                if (errorBitmask & 1<<j):
                    errorMsg = errorDict[j]
                    infoText += '%s: %s, ' % (moduleName, errorMsg)
    return infoText[:-2]

class StatusBar(QtGui.QWidget):

    diskFillupDetected = QtCore.pyqtSignal()
    daemonRestartRequested = QtCore.pyqtSignal()

    def __init__(self, msgLog):
        QtGui.QWidget.__init__(self)

        self.msgLog = msgLog

        layout = QtGui.QGridLayout()

        self.keepDaemonDead = None

        self.watchdogCheckbox = QtGui.QCheckBox('Watchdog')
        self.watchdogCheckbox.stateChanged.connect(self.toggleWatchdog)
        layout.addWidget(self.watchdogCheckbox, 0,0)

        self.daemonLabel = QtGui.QLabel('Daemon')
        self.daemonLabel.setStyleSheet(UNKNOWN_STYLE)
        layout.addWidget(self.daemonLabel, 1,0)

        self.datanodeLabel = QtGui.QLabel('Datanode')
        self.datanodeLabel.setStyleSheet(UNKNOWN_STYLE)
        layout.addWidget(self.datanodeLabel, 1,1)

        self.firmwareLabel = QtGui.QLabel('(firmware)')
        self.firmwareLabel.setStyleSheet(UNKNOWN_STYLE)
        layout.addWidget(self.firmwareLabel, 2,0)

        self.errorLabel = QtGui.QLabel('(errors)')
        #self.errorLabel = QtGui.QPushButton('(errors)')
        self.errorLabel.setToolTip('No Errors')
        self.errorLabel.setStyleSheet(UNKNOWN_STYLE)
        layout.addWidget(self.errorLabel, 2,1)

        self.streamLabel = QtGui.QLabel('Not Streaming')
        self.streamLabel.setStyleSheet(UNKNOWN_STYLE)
        layout.addWidget(self.streamLabel)

        self.recordLabel = QtGui.QLabel('Not Recording')
        self.recordLabel.setStyleSheet(UNKNOWN_STYLE)
        layout.addWidget(self.recordLabel)

        self.setLayout(layout)

        ###

        self.watchdogThread = WatchdogThread()
        self.vitalsLog = QtGui.QTextEdit()
        self.vitalsLog.setReadOnly(True)
        self.watchdogThread.vitalsChecked.connect(self.updateGUI)
        self.watchdogThread.vitalsChecked.connect(self.noteNewVitals)

    def dontRestartDaemon(self):
        self.keepDaemonDead = True

    def toggleWatchdog(self, state):
        if state:
            self.startWatchdog()
        else:
            self.stopWatchdog()

    def initializeWatchdog(self):
        self.startWatchdog()
        self.watchdogCheckbox.setChecked(True)

    def startWatchdog(self):
        self.watchdogLoop = True
        self.watchdogThread.start()

    def stopWatchdog(self):
        self.watchdogLoop = False

    def noteNewVitals(self, vitals):
        dt = datetime.datetime.fromtimestamp(time.time())
        prefix = '<b>[%02d:%02d:%02d] \n</b> ' % (dt.hour, dt.minute, dt.second)
        formatted = pprint.pformat(vitals)
        self.vitalsLog.append(prefix)
        self.vitalsLog.append(formatted)

    def writeVitalsLog(self, filename):
        vitalsText = self.vitalsLog.toPlainText()
        with open(filename, 'w') as f:
            f.write(vitalsText)


    def updateGUI(self, vitals):
        tmp = vitals['daemon']
        if tmp == True:
            self.daemonLabel.setStyleSheet(GOOD_STYLE)
        elif tmp == False:
            self.daemonLabel.setStyleSheet(BAD_STYLE)
            #if not self.keepDaemonDead:
            #    dRD = DaemonRestartDialog()
            #    dRD.daemonRestartPasser.connect(self.daemonRestartRequested)
            #    dRD.daemonDontRestartPasser.connect(self.dontRestartDaemon)
            #    if dRD.exec_():
            #        dRD.show()
        elif tmp == None:
            self.daemonLabel.setStyleSheet(UNKNOWN_STYLE)

        tmp = vitals['datanode']
        if tmp == True:
            self.datanodeLabel.setStyleSheet(GOOD_STYLE)
        elif tmp == False:
            self.datanodeLabel.setStyleSheet(BAD_STYLE)
        elif tmp == None:
            self.datanodeLabel.setStyleSheet(UNKNOWN_STYLE)

        tmp = vitals['firmware']
        if tmp == None:
            self.firmwareLabel.setText('(firmware)')
            self.firmwareLabel.setStyleSheet(UNKNOWN_STYLE)
        else:
            w = 255 & (tmp >> 24)
            x = 255 & (tmp >> 16)
            y = 255 & (tmp >> 8)
            z = 255 & (tmp >> 0)
            z = chr(ord('a') + (z-1))
            self.firmwareLabel.setText('Firmware: %d.%d.%d.%s' % (w,x,y,z))
            self.firmwareLabel.setStyleSheet(GOOD_STYLE)

        tmp = vitals['errors']
        if tmp == None:
            self.errorLabel.setText('(errors)')
            self.errorLabel.setStyleSheet(UNKNOWN_STYLE)
        elif tmp == 0:
            self.errorLabel.setText('No Errors')
            self.errorLabel.setStyleSheet(GOOD_STYLE)
        else:
            self.errorLabel.setText('Errors (mouseover)')
            self.errorLabel.setToolTip(getErrorInfo(tmp))
            self.errorLabel.setStyleSheet(BAD_STYLE)

        tmp = vitals['stream']
        if tmp == True:
            self.streamLabel.setText('Streaming')
            self.streamLabel.setStyleSheet(STREAM_STYLE)
        elif tmp == False:
            self.streamLabel.setText('Not Streaming')
            self.streamLabel.setStyleSheet(GOOD_STYLE)
        elif tmp == None:
            self.streamLabel.setText('(stream)')
            self.streamLabel.setStyleSheet(UNKNOWN_STYLE)

        tmp = vitals['record']
        if tmp == True:
            try:
                diskIndex = hwif.getSataBSI()
                if (diskIndex >= DISK_FILLUP_FRACTION*MAX_DISK_INDEX):
                    self.diskFillupDetected.emit()
                self.recordLabel.setText('Recording: %5.2f%%' % (diskIndex/MAX_DISK_INDEX*100))
                self.recordLabel.setStyleSheet(RECORD_STYLE)
            except hwif.hwifError as e:
                self.msgLog.post('StatusBar Error while trying to read disk index: %s' % e.message)
        elif tmp == False:
            self.recordLabel.setText('Not Recording')
            self.recordLabel.setStyleSheet(GOOD_STYLE)
        elif tmp == None:
            self.recordLabel.setText('(record)')
            self.recordLabel.setStyleSheet(UNKNOWN_STYLE)

        if self.watchdogLoop:
            self.watchdogThread.start()

