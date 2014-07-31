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
from StreamTab import StreamTab
from TransferTab import TransferTab

from parameters import DAEMON_DIR, DATA_DIR


class MainWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.logo = QtGui.QLabel()
        #self.logo.setPixmap(QtGui.QPixmap('round_logo_60x60_text.png'))
        self.logo.setPixmap(QtGui.QPixmap('newlogo.png'))
        self.logo.setAlignment(QtCore.Qt.AlignHCenter)
        #logoscale = 2.
        #self.logo.setMaximumSize(QtCore.QSize(825*logoscale,450*logoscale))
        #self.logo.setScaledContents(True)
        #self.logo.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)

        self.tabDialog = QtGui.QTabWidget()
        self.streamTab = StreamTab(self)
        self.tabDialog.addTab(self.streamTab, 'Stream')
        self.recordTab = RecordTab(self)
        self.tabDialog.addTab(self.recordTab, 'Record')
        self.transferTab = TransferTab(self)
        self.tabDialog.addTab(self.transferTab, 'Transfer')
        self.tabDialog.setMovable(True)

        self.leftColumn = QtGui.QWidget()
        tmp = QtGui.QVBoxLayout()
        tmp.addWidget(self.logo)
        tmp.addSpacing(20)
        tmp.addWidget(self.tabDialog)
        self.leftColumn.setLayout(tmp)

        ###################
        # Matplotlib stuff
        ###################
        # TODO this whole setup is a little ugly, especially
        #  the way it switches between stream view and record
        #  view. Needs a general overhaul.

        self.fig = Figure((5.0, 4.0), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.axes = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.,bottom=0.,right=1.,top=1., wspace=0.04, hspace=0.1)
        self.axes.xaxis.set_ticklabels([])
        self.axes.yaxis.set_ticklabels([])
        self.axes.set_axis_bgcolor('k')
        self.axes.axis([0,30000,0,2**16-1])
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.mplLayout = QtGui.QVBoxLayout()
        self.mplLayout.addWidget(self.canvas)
        self.mplLayout.addWidget(self.mpl_toolbar)
        self.mplWindow = QtGui.QWidget()
        self.mplWindow.setLayout(self.mplLayout)

        ###

        self.LRSplitter = QtGui.QSplitter()
        self.LRSplitter.addWidget(self.leftColumn)
        self.LRSplitter.addWidget(self.mplWindow)

        ###

        self.statusBox = QtGui.QTextEdit()
        self.statusBox.setReadOnly(True)

        self.statusBox_withLabel = QtGui.QWidget()
        tmp = QtGui.QVBoxLayout()
        tmp.addWidget(QtGui.QLabel('Message Log'))
        tmp.addWidget(self.statusBox)
        self.statusBox_withLabel.setLayout(tmp)

        ###

        self.TBSplitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.TBSplitter.addWidget(self.LRSplitter)
        self.TBSplitter.addWidget(self.statusBox_withLabel)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.TBSplitter)

        self.setLayout(mainLayout)
        self.setWindowTitle('WiredLeaf Control Panel')
        self.setWindowIcon(QtGui.QIcon('round_logo_60x60.png'))
        self.resize(1200,500)

        ###

        self.waveform = self.axes.plot(np.arange(30000), np.array([2**15]*30000), color='y')
        self.canvas.draw()

        self.isDaemonRunning = False
        self.isDaqRunning = False

        ###

        self.startDaemon()

    def startDaemon(self):
        subprocess.call([os.path.join(DAEMON_DIR, 'build/leafysd'), '-A', '192.168.1.2'])
        self.isDaemonRunning = True
        self.statusBox.append('Daemon started.')

    def exit(self):
        print 'Cleaning up, then exiting..'
        if self.isDaqRunning:
            subprocess.call([DAEMON_DIR+'util/acquire.py', 'stop'])
        if self.isDaemonRunning:
            subprocess.call(['killall', 'leafysd'])

if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec_()
    main.exit()

