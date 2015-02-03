#!/usr/bin/env python

"""
Willow Control Panel GUI
Initiated on 20140522 by Chris Chronopoulos (chrono@leaflabs.com)
"""

import sys, os, time, subprocess, socket

import numpy as np
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from PyQt4 import QtCore, QtGui

from StatusBar import StatusBar
from ButtonPanel import ButtonPanel
from MessageLog import MessageLog

from parameters import DAEMON_DIR, DATA_DIR
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

import hwif

if not os.path.isdir('../log'):
    os.mkdir('../log')
oFile = open('../log/oFile', 'w')
eFile = open('../log/eFile', 'w')

class MainWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.statusBar = StatusBar()

        ###

        self.msgLog = MessageLog()

        ###

        self.buttonPanel = ButtonPanel(self.msgLog)

        ###

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.statusBar)
        mainLayout.addWidget(self.buttonPanel)
        mainLayout.addWidget(self.msgLog)

        ###

        self.setLayout(mainLayout)
        self.setWindowTitle('Willow Control Panel')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        #self.resize(400,200)
        self.center()

        ###

        self.startDaemon()
        try:
            hwif.init()
        except socket.error:
            print 'could not connect to daemon after 100 tries.. quitting.'
            sys.exit(1)

        self.statusBar

    def startDaemon(self):
        #subprocess.call([os.path.join(DAEMON_DIR, 'build/leafysd'), '-A', '192.168.1.2'])
        subprocess.call(['killall', 'leafysd'])
        self.daemonProcess = subprocess.Popen([os.path.join(DAEMON_DIR, 'build/leafysd'),
                                                '-N', '-A', '192.168.1.2', '-I', 'eth0'], stdout=oFile, stderr=eFile)
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
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec_()
    main.exit()

