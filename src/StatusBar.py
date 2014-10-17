import socket
from PyQt4 import QtCore, QtGui
from StateManagement import *   # implicitly imports * from daemon_control

class StatusBar(QtGui.QStatusBar):

    def __init__(self):
        super(StatusBar, self).__init__()

        self.goodStyle = 'QLabel {background-color: #8fdb90; font: bold}'
        self.unknownStyle = 'QLabel {background-color: gray; font: bold}'
        self.badStyle = 'QLabel {background-color: orange; font: bold}'

        self.daemonLabel = QtGui.QLabel('Daemon')
        self.daemonLabel.setStyleSheet(self.unknownStyle)
        self.addWidget(self.daemonLabel)

        self.datanodeLabel = QtGui.QLabel('Datanode')
        self.datanodeLabel.setStyleSheet(self.unknownStyle)
        self.addWidget(self.datanodeLabel)

        self.firmwareLabel = QtGui.QLabel('(firmware)')
        self.firmwareLabel.setStyleSheet(self.unknownStyle)
        self.addWidget(self.firmwareLabel)

        self.errorLabel = QtGui.QLabel('(errors)')
        self.errorLabel.setStyleSheet(self.unknownStyle)
        self.addWidget(self.errorLabel)

        self.watchdogCheckbox = QtGui.QCheckBox('Watchdog')
        self.watchdogCheckbox.stateChanged.connect(self.toggleWatchdog)
        self.addWidget(self.watchdogCheckbox)

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
            self.daemonLabel.setStyleSheet(self.goodStyle)
            self.datanodeLabel.setStyleSheet(self.goodStyle)
            #
            firmwareVersion = doRegRead(MOD_CENTRAL, CENTRAL_GIT_SHA_PIECE)
            self.firmwareLabel.setText('Firmware: %x' % firmwareVersion)
            self.firmwareLabel.setStyleSheet(self.goodStyle)
            #
            errorState = doRegRead(MOD_ERR, ERR_ERR0)
            if errorState==0:
                self.errorLabel.setText('No Errors')
                self.errorLabel.setStyleSheet(self.goodStyle)
            else:
                self.errorLabel.setText('Errors: %s' % bin(errorState)[2:])
                self.errorLabel.setStyleSheet(self.alertStyle)
        except socket.error:
            self.daemonLabel.setStyleSheet(self.badStyle)
            self.datanodeLabel.setStyleSheet(self.unknownStyle)
            self.firmwareLabel.setText('Firmware: xxxxxxxx')
            self.firmwareLabel.setStyleSheet(self.unknownStyle)
            self.errorLabel.setText('(errors)')
            self.errorLabel.setStyleSheet(self.unknownStyle)
        except (NO_DNODE_error, DNODE_DIED_error):
            # datanode is not connected
            self.daemonLabel.setStyleSheet(self.goodStyle)
            self.datanodeLabel.setStyleSheet(self.badStyle)
            self.firmwareLabel.setText('Firmware: xxxxxxxx')
            self.firmwareLabel.setStyleSheet(self.unknownStyle)
            self.errorLabel.setText('(errors)')
            self.errorLabel.setStyleSheet(self.unknownStyle)
        except DNODE_error:
            # datanode is connected, but there is an error condition on the board
            self.daemonLabel.setStyleSheet(self.goodStyle)
            self.datanodeLabel.setStyleSheet(self.goodStyle)
            #
            firmwareVersion = doRegRead(MOD_CENTRAL, CENTRAL_GIT_SHA_PIECE)
            self.firmwareLabel.setText('Firmware: %x' % firmwareVersion)
            self.firmwareLabel.setStyleSheet(self.goodStyle)
            #
            errorState = doRegRead(MOD_ERR, ERR_ERR0)
            self.errorLabel.setText('Errors: %s' % bin(errorState)[2:])
            self.errorLabel.setStyleSheet(self.badStyle)


