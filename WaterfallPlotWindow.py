from PyQt4 import QtCore, QtGui
import os, sys, h5py
import numpy as np
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.cm as cm

class WaterfallPlotWindow(QtGui.QWidget):

    def __init__(self, parent):
        super(WaterfallPlotWindow, self).__init__(None)

        self.parent = parent

        self.initializeMPL()
        self.drawSpectrogram()

        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.mplLayout = QtGui.QVBoxLayout()
        self.mplLayout.addWidget(self.canvas)
        self.mplLayout.addWidget(self.mpl_toolbar)
        self.mplWindow = QtGui.QWidget()
        self.mplWindow.setLayout(self.mplLayout)

        ###################
        # Top-level stuff
        ##################

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.mplWindow)
        self.setLayout(self.layout)

        self.setWindowTitle('Waterfall Plot: %s' % self.parent.filename)
        self.setWindowIcon(QtGui.QIcon('round_logo_60x60.png'))
        self.resize(1600,500)

    def initializeMPL(self):
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)

    def drawSpectrogram(self):
        self.axes = self.fig.add_subplot(111)
        self.axesImage = self.axes.imshow(self.parent.data, cm.gist_ncar, aspect='auto')

