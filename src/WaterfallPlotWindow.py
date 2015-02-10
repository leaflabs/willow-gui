from PyQt4 import QtCore, QtGui
import os, sys, h5py
import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.cm as cm

from ImportThread import ImportThread

class OldControlPanel(QtGui.QWidget):

    def __init__(self, data, sampleRange, canvas):
        QtGui.QWidget.__init__(self)
        self.canvas = canvas
        self.zoomWidget = self.ZoomWidget(sampleRange)
        self.zoomWidget.setMaximumWidth(200)
        self.colorBarWidget = self.ColorBarWidget(data)
        self.colorBarWidget.setMaximumWidth(200)
        self.refreshButton = QtGui.QPushButton('Refresh')
        self.refreshButton.clicked.connect(self.refresh)
        self.refreshButton.setMaximumWidth(200)
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.zoomWidget)
        self.layout.addWidget(self.colorBarWidget)
        self.layout.addWidget(self.refreshButton)
        self.setLayout(self.layout)
        self.setMaximumHeight(100)

    class ZoomWidget(QtGui.QWidget):

        def __init__(self, sampleRange):
            QtGui.QWidget.__init__(self)
            xmin = sampleRange[0]
            xmax = sampleRange[1]
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

    class ColorBarWidget(QtGui.QWidget):

        def __init__(self, data):
            QtGui.QWidget.__init__(self)
            self.minLine = QtGui.QLineEdit(str(np.min(data)))
            self.maxLine = QtGui.QLineEdit(str(np.max(data)))
            self.layout = QtGui.QGridLayout()
            self.layout.addWidget(QtGui.QLabel('ColorBar Min:'), 0,0)
            self.layout.addWidget(self.minLine, 0,1)
            self.layout.addWidget(QtGui.QLabel('ColorBar Max:'), 1,0)
            self.layout.addWidget(self.maxLine, 1,1)
            self.setLayout(self.layout)

    def refresh(self):
        xmin = int(self.zoomWidget.xminLine.text())
        xmax = int(self.zoomWidget.xmaxLine.text())
        ymin = int(self.zoomWidget.yminLine.text())
        ymax = int(self.zoomWidget.ymaxLine.text())
        self.canvas.figure.axes[0].axis([xmin, xmax, ymin, ymax])
        vmin = int(self.colorBarWidget.minLine.text())
        vmax = int(self.colorBarWidget.maxLine.text())
        self.canvas.figure.axesImage.set_clim(vmin, vmax)
        self.canvas.draw()


class PlotPanel(QtGui.QWidget):

    def __init__(self, dataset):
        QtGui.QWidget.__init__(self)
        self.dataset = dataset

        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

    def initialize(self, controlParams):
        self.setChannels(controlParams)


class WaterfallPlotWindow(QtGui.QWidget):

    def __init__(self, dataset):
        QtGui.QWidget.__init__(self)
        self.dataset = dataset

        self.filename = filename

        if data:
            self.data = data
            self.nsamples = data.shape[1]
            self.initializeWaterfallPlot()
        else:
            self.importProgressDialog = QtGui.QProgressDialog('Importing %s' % filename, 'Cancel', 0, 10)
            self.importProgressDialog.setMinimumDuration(1000)
            self.importProgressDialog.setModal(False)
            self.importProgressDialog.setWindowTitle('Data Import Progress')
            self.importProgressDialog.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
            self.importThread = ImportThread(self.filename, sampleRange)
            self.importThread.valueChanged.connect(self.importProgressDialog.setValue)
            self.importThread.maxChanged.connect(self.importProgressDialog.setMaximum)
            self.importThread.finished.connect(self.handleImportFinished)
            self.importThread.canceled.connect(self.importProgressDialog.cancel)
            self.importProgressDialog.canceled.connect(self.importThread.terminate)
            self.importProgressDialog.show()
            self.importThread.start()

    def handleImportFinished(self, filename, data, sampleRange):
        self.data = data            
        self.nsamples = data.shape[1]
        self.sampleRange = sampleRange
        self.initializeWaterfallPlot()

    def initializeWaterfallPlot(self):
        self.initializeMPL()
        self.drawSpectrogram()

        self.controlPanel = self.ControlPanel(self.data, self.sampleRange, self.canvas)

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

        self.setWindowTitle('Waterfall Plot: %s' % self.filename)
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.resize(1600,500)
        self.show()


    def initializeMPL(self):
        self.fig = Figure()
        self.fig.subplots_adjust(left=0.05, bottom=0.08, right=1.0, top=0.92)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)

    def drawSpectrogram(self):
        self.axes = self.fig.add_subplot(111)
        self.fig.axesImage = self.axes.imshow(self.data, cm.Spectral, aspect='auto')
        self.colorbar = self.fig.colorbar(self.fig.axesImage, use_gridspec=True)

if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    waterfall = WaterfallPlotWindow('/home/chrono/sng/data/justin/64chan/neuralRecording_10sec.h5',
        sampleRange=[0,9999])
    app.exec_()
