#!/usr/bin/env python

"""
WiredLeaf Control Panel GUI
Created on 20140522 by Chris Chronopoulos.
"""

import sys, time, subprocess

import numpy as np
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from PyQt4 import QtCore, QtGui

from SetupTab import SetupTab
from StreamTab import StreamTab
from RecordTab import RecordTab
from RegisterTab import RegisterTab
from DebugTab import DebugTab


DAEMON_DIR = '/home/chrono/sng/sng-daemon/'

class MainWindow(QtGui.QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setup()

    def setup(self):

        # TODO sort out sizing policies with this logo..
        self.logo = QtGui.QLabel()
        #self.logo.setPixmap(QtGui.QPixmap('round_logo_60x60_text.png'))
        self.logo.setPixmap(QtGui.QPixmap('newlogo.png'))
        self.logo.setAlignment(QtCore.Qt.AlignHCenter)
        #logoscale = 2.
        #self.logo.setMaximumSize(QtCore.QSize(825*logoscale,450*logoscale))
        #self.logo.setScaledContents(True)
        #self.logo.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)

        self.tabDialog = QtGui.QTabWidget()
        self.setupTab = SetupTab(self)
        self.tabDialog.addTab(self.setupTab, 'Setup')
        self.streamTab = StreamTab(self)
        self.tabDialog.addTab(self.streamTab, 'Stream')
        self.recordTab = RecordTab(self)
        self.tabDialog.addTab(self.recordTab, 'Record')
        self.registerTab = RegisterTab(self)
        self.tabDialog.addTab(self.registerTab, 'Registers')
        self.debugTab = DebugTab(self)
        self.tabDialog.addTab(self.debugTab, 'Debug')

        self.leftColumn = QtGui.QWidget()
        tmp = QtGui.QVBoxLayout()
        tmp.addWidget(self.logo)
        tmp.addSpacing(20)
        tmp.addWidget(self.tabDialog)
        self.leftColumn.setLayout(tmp)

        ###

        self.fig = Figure((5.0, 4.0), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_title('Data Window')
        self.axes.set_xlabel('Samples')
        self.axes.set_ylabel('Counts')
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

        self.statusBox = QtGui.QLabel('Status Box')

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.LRSplitter)
        mainLayout.addWidget(self.statusBox)

        self.setLayout(mainLayout)
        self.setWindowTitle('WiredLeaf Control Panel')
        self.setWindowIcon(QtGui.QIcon('round_logo_60x60.png'))
        self.resize(1200,500)

        ###

        self.waveform = self.axes.plot(np.arange(30000), np.array([2**15]*30000), color='y')
        self.canvas.draw()

    def testRTPlotting(self):
        if self.state:
            self.waveform[0].set_data(self.xvalues, self.sinewave)
            self.canvas.draw()
        else:
            self.waveform[0].set_data(self.xvalues, self.flatline)
            self.canvas.draw()
        self.state = not self.state


if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec_()

