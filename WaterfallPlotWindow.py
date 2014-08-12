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
        self.data = self.parent.data

        self.initializeMPL()
        self.drawSpectrogram()

        self.controlPanel = self.ControlPanel(self)

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
        self.layout.addWidget(self.controlPanel)
        self.layout.addWidget(self.mplWindow)
        self.setLayout(self.layout)

        self.setWindowTitle('Waterfall Plot: %s' % self.parent.filename)
        self.setWindowIcon(QtGui.QIcon('round_logo_60x60.png'))
        self.resize(1600,500)

    def initializeMPL(self):
        self.fig = Figure()
        self.fig.subplots_adjust(left=0.05, bottom=0.08, right=1.0, top=0.92)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)

    def drawSpectrogram(self):
        self.axes = self.fig.add_subplot(111)
        self.axesImage = self.axes.imshow(self.data, cm.gist_ncar, aspect='auto')
        self.fig.colorbar(self.axesImage, use_gridspec=True)

    class ControlPanel(QtGui.QWidget):

        def __init__(self, parent):
            super(parent.ControlPanel, self).__init__()
            self.parent = parent
            self.zoomWidget = self.ZoomWidget(self)
            self.zoomWidget.setMaximumWidth(200)
            self.refreshButton = QtGui.QPushButton('Refresh')
            self.refreshButton.clicked.connect(self.refresh)
            self.refreshButton.setMaximumWidth(200)
            self.layout = QtGui.QHBoxLayout()
            self.layout.addWidget(self.zoomWidget)
            self.layout.addWidget(self.refreshButton)
            self.setLayout(self.layout)
            self.setMaximumHeight(100)

        class ZoomWidget(QtGui.QWidget):

            def __init__(self, parent):
                super(parent.ZoomWidget, self).__init__()
                self.parent = parent
                xmin = self.parent.parent.parent.sampleRange[0]
                xmax = self.parent.parent.parent.sampleRange[1]
                ymin = 0
                ymax = 1023
                self.xminLine = QtGui.QLineEdit(str(xmin))
                self.xmaxLine = QtGui.QLineEdit(str(xmax))
                self.yminLine = QtGui.QLineEdit(str(ymin))
                self.ymaxLine = QtGui.QLineEdit(str(ymax))
                self.layout = QtGui.QGridLayout()
                self.layout.addWidget(QtGui.QLabel('X-Range:'), 0,0)
                self.layout.addWidget(self.xminLine, 0,1)
                self.layout.addWidget(self.xmaxLine, 0,2)
                self.layout.addWidget(QtGui.QLabel('Y-Range:'), 1,0)
                self.layout.addWidget(self.yminLine, 1,1)
                self.layout.addWidget(self.ymaxLine, 1,2)
                self.setLayout(self.layout)

        def refresh(self):
            xmin = int(self.zoomWidget.xminLine.text())
            xmax = int(self.zoomWidget.xmaxLine.text())
            ymin = int(self.zoomWidget.yminLine.text())
            ymax = int(self.zoomWidget.ymaxLine.text())
            self.parent.axes.axis([xmin, xmax, ymin, ymax])
            self.parent.canvas.draw()


