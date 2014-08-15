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

from RecordTab import RecordTab
from SnapshotTab import SnapshotTab
from StreamTab import StreamTab
from TransferTab import TransferTab
from PlotTab import PlotTab

from parameters import DAEMON_DIR, DATA_DIR
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

oFile = open('oFile', 'w')
eFile = open('eFile', 'w')

class WiredLeafState():

    def __init__(self, daemonRunning=False, daqRunning=False, streaming=False, recording=False):
        self.daemonRunning = daemonRunning
        self.daqRunning = daqRunning
        self.streaming = streaming
        self.recording = recording

    def setDaemonRunning(self, value):
        self.daemonRunning = value

    def setDaqRunning(self, value):
        self.daqRunning = value

    def setStreaming(self, value):
        self.streaming = value

    def setRecording(self, value):
        self.recording = value

    def isDaemonRunning(self):
        return self.daemonRunning

    def isDaqRunning(self):
        return self.daqRunning

    def isStreaming(self):
        return self.streaming

    def isRecording(self):
        return self.recording


class MainWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        """        
        self.logo = QtGui.QLabel()
        self.logo.setPixmap(QtGui.QPixmap('newlogo.png'))
        self.logo.setAlignment(QtCore.Qt.AlignHCenter)
        """

        self.tabDialog = QtGui.QTabWidget()

        self.streamTab = StreamTab(self)
        self.tabDialog.addTab(self.streamTab, 'Stream')

        self.snapshotTab = SnapshotTab(self)
        self.tabDialog.addTab(self.snapshotTab, 'Snapshot')

        self.recordTab = RecordTab(self)
        self.tabDialog.addTab(self.recordTab, 'Record')

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
        self.setWindowIcon(QtGui.QIcon('round_logo_60x60.png'))
        self.resize(400,400)
        self.center()

        ###

        self.state = WiredLeafState(daemonRunning=False, daqRunning=False, streaming=False, recording=False)
        self.startDaemon()

    def startDaemon(self):
        #subprocess.call([os.path.join(DAEMON_DIR, 'build/leafysd'), '-A', '192.168.1.2'])
        self.daemonProcess = subprocess.Popen([os.path.join(DAEMON_DIR, 'build/leafysd'),
                                                '-N', '-A', '192.168.1.2'], stdout=oFile, stderr=eFile)
        self.state.setDaemonRunning(True)
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
        if self.state.isDaqRunning():
            subprocess.call([DAEMON_DIR+'util/acquire.py', 'stop'])
        if self.state.isDaemonRunning():
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

