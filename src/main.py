#!/usr/bin/env python

"""
WiredLeaf Control Panel GUI
Created on 20140522 by Chris Chronopoulos.
"""

import sys, os, time, subprocess

import numpy as np
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from PyQt4 import QtCore, QtGui

from AcquireTab import AcquireTab
from TransferTab import TransferTab
from PlotTab import PlotTab

from parameters import DAEMON_DIR, DATA_DIR
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

oFile = open('../log/oFile', 'w')
eFile = open('../log/eFile', 'w')

class MainWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.tabDialog = QtGui.QTabWidget()

        self.acquireTab= AcquireTab(self)
        self.tabDialog.addTab(self.acquireTab, 'Acquire')

        self.transferTab = TransferTab(self)
        self.tabDialog.addTab(self.transferTab, 'Transfer')

        self.plotTab = PlotTab(self)
        self.tabDialog.addTab(self.plotTab, 'Plot')

        self.tabDialog.setMovable(True)

        self.topHalf = QtGui.QWidget()
        tmp = QtGui.QVBoxLayout()
        #tmp.addWidget(self.logo)
        #tmp.addSpacing(10)
        tmp.addWidget(self.tabDialog)
        self.topHalf.setLayout(tmp)

        ###

        self.statusBox = QtGui.QTextEdit()
        self.statusBox.setReadOnly(True)

        self.bottomHalf = QtGui.QWidget()
        tmp = QtGui.QVBoxLayout()
        tmp.addWidget(QtGui.QLabel('Message Log'))
        tmp.addWidget(self.statusBox)
        self.bottomHalf.setLayout(tmp)

        ###

        self.TBSplitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.TBSplitter.addWidget(self.topHalf)
        self.TBSplitter.addWidget(self.bottomHalf)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.TBSplitter)

        self.setLayout(mainLayout)
        self.setWindowTitle('WiredLeaf Control Panel')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.resize(400,400)
        self.center()

        ###

        self.startDaemon()

    def startDaemon(self):
        #subprocess.call([os.path.join(DAEMON_DIR, 'build/leafysd'), '-A', '192.168.1.2'])
        self.daemonProcess = subprocess.Popen([os.path.join(DAEMON_DIR, 'build/leafysd'),
                                                '-N', '-A', '192.168.1.2', '-I', 'eth0'], stdout=oFile, stderr=eFile)
        self.statusBox.append('Daemon started.')

    def isDaemonRunning(self):
        rc = self.daemonProcess.poll()
        return rc==None

    def isConnected(self):
        if self.isDaemonRunning():
            cmd = ControlCommand(type=ControlCommand.PING_DNODE)
            resp = do_control_cmd(cmd)
            if resp.type==2:
                return True
            else:
                self.statusBox.append('Datanode is not connected!')
                return False
        else:
            self.statusBox.append('Daemon is not running!')
            return False

    def exit(self):
        print 'Cleaning up, then exiting..'
        subprocess.call(['killall', 'leafysd'])

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

