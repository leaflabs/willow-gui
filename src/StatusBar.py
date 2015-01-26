import socket
from PyQt4 import QtCore, QtGui
import hwif
from WatchdogThread import WatchdogThread

GOOD_STYLE = 'QLabel {background-color: #8fdb90; font: bold}'
UNKNOWN_STYLE = 'QLabel {background-color: gray; font: bold}'
BAD_STYLE = 'QLabel {background-color: orange; font: bold}'
STREAM_STYLE = 'QLabel {background-color: rgb(0,191,255); font: bold}'
RECORD_STYLE = 'QLabel {background-color: red; font: bold}'

class StatusBar(QtGui.QWidget):

    def __init__(self):
        super(StatusBar, self).__init__()

        layout = QtGui.QGridLayout()

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
        self.watchdogThread.vitalsChecked.connect(self.updateGUI)

        self.startWatchdog()
        self.watchdogCheckbox.setChecked(True)

    def toggleWatchdog(self, state):
        if state:
            self.startWatchdog()
        else:
            self.stopWatchdog()

    def startWatchdog(self):
        self.watchdogLoop = True
        self.watchdogThread.start()

    def stopWatchdog(self):
        self.watchdogLoop = False

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
            self.firmwareLabel.setText('Firmware: %x' % tmp)
            self.firmwareLabel.setStyleSheet(GOOD_STYLE)

        tmp = vitals['errors']
        if tmp == None:
            self.errorLabel.setText('(errors)')
            self.errorLabel.setStyleSheet(UNKNOWN_STYLE)
        elif tmp == 0:
            self.errorLabel.setText('No Errors')
            self.errorLabel.setStyleSheet(GOOD_STYLE)
        else:
            self.errorLabel.setText('Errors: %s' % bin(tmp)[2:].zfill(6))
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
            """
            TODO
            If vitals['record']==True, then subsequent hwif commands *should* work,
            but this is subject to a race condition, so this should be wrapped in
            some carefully chosen exception handlers.
            """
            diskIndex = hwif.doRegRead(2,7)
            self.recordLabel.setText('Recording: %5.2f%%' % (diskIndex/250e4))
            self.recordLabel.setStyleSheet(RECORD_STYLE)
        elif tmp == False:
            self.recordLabel.setText('Not Recording')
            self.recordLabel.setStyleSheet(GOOD_STYLE)
        elif tmp == None:
            self.recordLabel.setText('(record)')
            self.recordLabel.setStyleSheet(UNKNOWN_STYLE)

        if self.watchdogLoop:
            self.watchdogThread.start()

