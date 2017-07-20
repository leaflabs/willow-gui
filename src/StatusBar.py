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

MAX_SAMPLE_INDEX = 250e3*config.storageCapacity_GB
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


def getErrorInfo(errorRegister):
    infoText = ''
    # iterate over modules
    for i in range(1,6):
        if (errorRegister & 1<<i):
            moduleName, errorDict = ERRORDICT_DICT[i]
            errorCode = hwif.getErrorCode(i)
            # iterate over error bits for each module
            for j in range(32):
                if (errorCode & 1<<j):
                    try:
                        errorMsg = errorDict[j]
                    except KeyError:
                        errorMsg = 'Unknown Error %d' % j
                    infoText += '%s: %s, ' % (moduleName, errorMsg)
    return infoText[:-2]

class StatusBar(QtGui.QWidget):

    diskFillupDetected = QtCore.pyqtSignal()

    def __init__(self, msgLog):
        QtGui.QWidget.__init__(self)

        self.msgLog = msgLog

        layout = QtGui.QGridLayout()

        self.acknowledgedError = None

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

        self.hwLabel = QtGui.QLabel('(hardware status)')
        self.hwLabel.setStyleSheet(UNKNOWN_STYLE)
        layout.addWidget(self.hwLabel, 2,1)

        self.streamLabel = QtGui.QLabel('Not Streaming')
        self.streamLabel.setStyleSheet(UNKNOWN_STYLE)
        layout.addWidget(self.streamLabel, 3,0)

        self.recordLabel = QtGui.QLabel('Not Recording')
        self.recordLabel.setStyleSheet(UNKNOWN_STYLE)
        layout.addWidget(self.recordLabel, 3,1)

        self.setLayout(layout)

        ###

        self.watchdogThread = WatchdogThread()
        self.vitalsLog = QtGui.QTextEdit()
        self.vitalsLog.setReadOnly(True)
        self.watchdogThread.vitalsChecked.connect(self.updateGUI)
        self.watchdogThread.vitalsChecked.connect(self.noteNewVitals)
        self.watchdogThread.statusUpdated.connect(self.msgLog.post)
        self.watchdogThread.finished.connect(self.handleWatchdogStopped)

    def toggleWatchdog(self, state):
        if state:
            self.startWatchdog()
        else:
            self.stopWatchdog()

    def initializeWatchdog(self):
        self.watchdogCheckbox.setChecked(True)

    def startWatchdog(self):
        self.msgLog.post('Starting watchdog thread.')
        self.watchdogThread.start()

    def stopWatchdog(self):
        self.watchdogThread.running = False

    def handleWatchdogStopped(self):
        time.sleep(1) # to ensure that the checkbox remains checked for a second
        self.msgLog.post('Watchdog stopped.')
        self.watchdogCheckbox.setChecked(False)

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
        if tmp == 0:
            tmp = vitals['chips_live']
            if isinstance(tmp, list):
                self.hwLabel.setText('{0} chips live'.format(len(tmp)))
                self.hwLabel.setToolTip('chips {0} alive'.format(', '.join([str(c) for c in tmp])))
            else:
                self.hwLabel.setText('(chips live)')
            self.hwLabel.setStyleSheet(GOOD_STYLE)
        elif tmp ==  None:
            self.hwLabel.setText('(hardware status)')
            self.hwLabel.setStyleSheet(UNKNOWN_STYLE)
        else:
            self.hwLabel.setText('Hardware Error') 
            self.hwLabel.setStyleSheet(BAD_STYLE)
            self.hwLabel.setToolTip(getErrorInfo(tmp))

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
            sampleIndex = vitals['sample_index']
            if (sampleIndex >= DISK_FILLUP_FRACTION*MAX_SAMPLE_INDEX):
                self.diskFillupDetected.emit()
            self.recordLabel.setText('Recording: %5.2f%%' % (sampleIndex/MAX_SAMPLE_INDEX*100))
            self.recordLabel.setStyleSheet(RECORD_STYLE)
        elif tmp == False:
            self.recordLabel.setText('Not Recording')
            self.recordLabel.setStyleSheet(GOOD_STYLE)
        elif tmp == None:
            self.recordLabel.setText('(record)')
            self.recordLabel.setStyleSheet(UNKNOWN_STYLE)

