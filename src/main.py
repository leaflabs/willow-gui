#!/usr/bin/env python

"""
Willow Control Panel GUI

Chris Chronopoulos (chrono@leaflabs.com) - 20140522
"""

import sys, os, subprocess, socket

from PyQt4 import QtCore, QtGui

# change workdir to src/
os.chdir(os.path.dirname(os.path.realpath(__file__)))

from StatusBar import StatusBar
from ButtonPanel import ButtonPanel
from MessageLog import MessageLog
import config
import hwif

if not os.path.isdir('../log'):
    os.mkdir('../log')
oFile = open('../log/oFile', 'w')
eFile = open('../log/eFile', 'w')

class MainWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)

        self.msgLog = MessageLog()
        self.statusBar = StatusBar(self.msgLog)
        self.buttonPanel = ButtonPanel(self.msgLog)
        self.statusBar.diskFillupDetected.connect(self.buttonPanel.handleDiskFillup)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.statusBar)
        mainLayout.addWidget(self.buttonPanel)
        mainLayout.addWidget(self.msgLog)
        self.setLayout(mainLayout)

        self.setWindowTitle('Willow Control Panel')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        #self.resize(400,200)
        self.center()

        ###

        self.startDaemon()
        try:
            hwif.init()
            self.statusBar.initializeWatchdog()
            self.msgLog.post('Daemon connection established, watchdog started')
        except socket.error:
            self.msgLog.post('Could not establish a connection with the daemon.')

    def startDaemon(self):
        subprocess.call(['killall', 'leafysd'])
        self.daemonProcess = subprocess.Popen([os.path.join(config.daemonDir, 'build/leafysd'),
                                                '-N', '-A', '192.168.1.2', '-I', config.networkInterface],
                                                stdout=oFile, stderr=eFile)
        self.msgLog.post('Daemon started.')
        print 'daemon started'

    def exit(self):
        print 'Cleaning up, then exiting..'
        self.statusBar.watchdogThread.terminate()
        subprocess.call(['killall', 'leafysd'])
        subprocess.call(['killall', 'proto2bytes'])

    def center(self):
        windowCenter = self.frameGeometry().center()
        screenCenter = QtGui.QDesktopWidget().availableGeometry().center()
        self.move(screenCenter-windowCenter)


if __name__=='__main__':
    print 'PID = %d' % os.getpid()
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec_()
    main.exit()

