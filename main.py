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

class WiredLeafState():

    def __init__(self, daemonRunning=False, daqRunning=False):
        self.daemonRunning = daemonRunning
        self.daqRunning = daqRunning

    def setDaemonRunning(self, value):
        self.daemonRunning = value

    def setDaqRunning(self, value):
        self.daqRunning = value

    def isDaemonRunning(self):
        return self.daemonRunning

    def isDaqRunning(self):
        return self.daqRunning


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

        ###

        self.state = WiredLeafState(daemonRunning=False, daqRunning=False)
        self.startDaemon()

    def startDaemon(self):
        subprocess.call([os.path.join(DAEMON_DIR, 'build/leafysd'), '-A', '192.168.1.2'])
        self.state.setDaemonRunning(True)
        self.statusBox.append('Daemon started.')

    def exit(self):
        print 'Cleaning up, then exiting..'
        if self.state.isDaqRunning():
            subprocess.call([DAEMON_DIR+'util/acquire.py', 'stop'])
        if self.state.isDaemonRunning():
            subprocess.call(['killall', 'leafysd'])

if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec_()
    main.exit()
