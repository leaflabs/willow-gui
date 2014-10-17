import socket
from PyQt4 import QtCore, QtGui
from StateManagement import *   # implicitly imports * from daemon_control

GOOD_STYLE = 'QLabel {background-color: #8fdb90; font: bold}'
UNKNOWN_STYLE = 'QLabel {background-color: gray; font: bold}'
BAD_STYLE = 'QLabel {background-color: orange; font: bold}'

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

        self.watchdogTimer = QtCore.QTimer()
        self.watchdogTimer.timeout.connect(self.watchdogCallback)

        self.startWatchdog()
        self.watchdogCheckbox.setChecked(True)

    def toggleWatchdog(self, state):
        if state:
            self.startWatchdog()
        else:
            self.stopWatchdog()

    def startWatchdog(self):
        self.watchdogTimer.start(1000) # ms

    def stopWatchdog(self):
        self.watchdogTimer.stop()

    def watchdogCallback(self):
        try:
            pingDatanode()
            self.daemonLabel.setStyleSheet(GOOD_STYLE)
            self.datanodeLabel.setStyleSheet(GOOD_STYLE)
            # Firmware Label
            firmwareVersion = doRegRead(MOD_CENTRAL, CENTRAL_GIT_SHA_PIECE)
            self.firmwareLabel.setText('Firmware: %x' % firmwareVersion)
            self.firmwareLabel.setStyleSheet(GOOD_STYLE)
            # Error Label
            self.errorLabel.setText('No Errors')
            self.errorLabel.setStyleSheet(GOOD_STYLE)
            # Stream/Record
            state = checkState()
            if (state & 0b001):
                self.streamLabel.setText('Streaming')
                self.streamLabel.setStyleSheet(GOOD_STYLE)
            else:
                self.streamLabel.setText('Not Streaming')
                self.streamLabel.setStyleSheet(GOOD_STYLE)
            if (state & 0b100):
                self.recordLabel.setText('Recording')
                self.recordLabel.setStyleSheet(GOOD_STYLE)
            else:
                self.recordLabel.setText('Not Recording')
                self.recordLabel.setStyleSheet(GOOD_STYLE)
        except socket.error:
            self.daemonLabel.setStyleSheet(BAD_STYLE)
            self.datanodeLabel.setStyleSheet(UNKNOWN_STYLE)
            self.firmwareLabel.setText('Firmware: xxxxxxxx')
            self.firmwareLabel.setStyleSheet(UNKNOWN_STYLE)
            self.errorLabel.setText('(errors)')
            self.errorLabel.setStyleSheet(UNKNOWN_STYLE)
            self.streamLabel.setText('stream unknown')
            self.streamLabel.setStyleSheet(UNKNOWN_STYLE)
            self.recordLabel.setText('record unknown')
            self.recordLabel.setStyleSheet(UNKNOWN_STYLE)
        except (NO_DNODE_error, DNODE_DIED_error) as e:
            # datanode is not connected
            self.daemonLabel.setStyleSheet(GOOD_STYLE)
            self.datanodeLabel.setStyleSheet(BAD_STYLE)
            self.firmwareLabel.setText('Firmware: xxxxxxxx')
            self.firmwareLabel.setStyleSheet(UNKNOWN_STYLE)
            self.errorLabel.setText('(errors)')
            self.errorLabel.setStyleSheet(UNKNOWN_STYLE)
            self.streamLabel.setText('stream unknown')
            self.streamLabel.setStyleSheet(UNKNOWN_STYLE)
            self.recordLabel.setText('record unknown')
            self.recordLabel.setStyleSheet(UNKNOWN_STYLE)
        except DNODE_error:
            # datanode is connected, but there is an error condition on the board
            self.daemonLabel.setStyleSheet(GOOD_STYLE)
            self.datanodeLabel.setStyleSheet(GOOD_STYLE)
            #
            firmwareVersion = doRegRead(MOD_CENTRAL, CENTRAL_GIT_SHA_PIECE)
            self.firmwareLabel.setText('Firmware: %x' % firmwareVersion)
            self.firmwareLabel.setStyleSheet(GOOD_STYLE)
            #
            errorState = doRegRead(MOD_ERR, ERR_ERR0)
            self.errorLabel.setText('Errors: %s' % bin(errorState)[2:].zfill(6))
            self.errorLabel.setStyleSheet(BAD_STYLE)
            state = checkState()
            if (state & 0b001):
                self.streamLabel.setText('Streaming')
                self.streamLabel.setStyleSheet(GOOD_STYLE)
            else:
                self.streamLabel.setText('Not Streaming')
                self.streamLabel.setStyleSheet(GOOD_STYLE)
            if (state & 0b100):
                self.recordLabel.setText('Recording')
                self.recordLabel.setStyleSheet(GOOD_STYLE)
            else:
                self.recordLabel.setText('Not Recording')
                self.recordLabel.setStyleSheet(GOOD_STYLE)


