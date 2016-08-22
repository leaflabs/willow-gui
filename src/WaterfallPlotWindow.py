#!/usr/bin/python

from PyQt4 import QtCore, QtGui
import os, sys, h5py
import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.cm as cm

from WillowDataset import WillowDataset
from collections import OrderedDict

LAYOUT_DICT = OrderedDict([(1,(1,1)),
                            (2,(2,1)),
                            (3,(3,1)),
                            (4,(4,1)),
                            (5,(5,1)),
                            (6,(3,2)),
                            (8,(4,2)),
                            (10,(5,2)),
                            (12,(6,2)),
                            (16,(4,4))
                            ])

class HistoControl(QtGui.QWidget):

    uvMin = -6553.6
    uvMax = 6553.6

    limitsChanged = QtCore.pyqtSignal(int, int)

    def __init__(self, dataset):
        QtGui.QWidget.__init__(self)
        self.dataset = dataset

        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.mpl_connect('button_press_event', self.onclick)

        # initialize with subset = entire dataset
        c1, c2 = 0, self.dataset.data_uv.shape[0]
        t1, t2 = 0, self.dataset.data_uv.shape[1]
        self.setDataSubset(c1, c2, t1, t2 )

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        #self.setMaximumWidth(220)

    def onclick(self, event):
        if event.button==1:
            if event.xdata < self.vmax:
                self.vmin = event.xdata
                self.vlineL.remove()
                self.vlineL = self.axes.axvline(x=self.vmin, linewidth=2, color='r')
                self.canvas.draw()
                self.limitsChanged.emit(self.vmin, self.vmax)
        elif event.button==3:
            if event.xdata > self.vmin:
                self.vmax = event.xdata
                self.vlineR.remove()
                self.vlineR = self.axes.axvline(x=self.vmax, linewidth=2, color='b')
                self.canvas.draw()
                self.limitsChanged.emit(self.vmin, self.vmax)

    def handleNewRange(self, controlParams):
        """
        This handler gets called when ControlPanel emits rangeUpdated(dict)
        """
        if controlParams['probeMode']:
            c1, c2 = 0, controlParams['probeType']
        else:
            c1, c2 = controlParams['channelRange']
        time1, time2 = controlParams['timeRange']
        timeIndices = np.where((time1 <= self.dataset.time_ms) & (self.dataset.time_ms < time2))
        t1 = timeIndices[0][0]
        t2 = timeIndices[0][-1] + 1
        self.setDataSubset(c1, c2, t1, t2)
        self.limitsChanged.emit(self.vmin, self.vmax)
        

    def setDataSubset(self, c1, c2, t1, t2):
        self.subsetMin = np.min(self.dataset.data_uv[c1:c2, t1:t2])
        self.subsetMax = np.max(self.dataset.data_uv[c1:c2, t1:t2])
        self.subsetRange = self.subsetMax - self.subsetMin
        self.hist = np.histogram(self.dataset.data_uv[c1:c2, t1:t2],
            bins=np.linspace(self.subsetMin, self.subsetMax, 256))
        self.x = self.hist[1][:-1]
        self.y = self.hist[0][:]
        self.width = self.x[1] - self.x[0]
        self.fig.clear()
        self.axes = self.fig.add_subplot(111)
        self.axes.set_axis_bgcolor('k')
        self.axes.bar(self.x,self.y, width=self.width, color='#8fdb90')
        self.axes.set_title('Value Histogram (microVolts)', fontsize=10)
        self.axes.set_xlim([self.subsetMin-self.subsetRange/5., self.subsetMax+self.subsetRange/5.])
        self.axes.get_yaxis().set_visible(False)
        self.fig.subplots_adjust(left=0.05, bottom=0.08, right=0.92, top=0.92)
        # vlines
        self.vmin = self.subsetMin
        self.vmax = self.subsetMax
        self.vlineL = self.axes.axvline(x=self.vmin, linewidth=2, color='r')
        self.vlineR = self.axes.axvline(x=self.vmax, linewidth=2, color='b')
        self.canvas.draw()

        

class ControlPanel(QtGui.QWidget):

    rangeUpdated = QtCore.pyqtSignal(dict)

    def __init__(self, dataset):
        QtGui.QWidget.__init__(self)
        self.dataset = dataset

        self.createChannelGroup()
        self.createTimeGroup()
        self.createButtons()
        self.histoControl = HistoControl(self.dataset)
        self.rangeUpdated.connect(self.histoControl.handleNewRange)
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.channelGroup, 0,0, 1,1)
        self.layout.addWidget(self.timeGroup, 1,0, 1,1)
        self.layout.addWidget(self.buttons, 2,0, 1,1)
        self.layout.addWidget(self.histoControl, 0,1, 3,3)
        self.setLayout(self.layout)
        self.setMaximumHeight(260)

    def createChannelGroup(self):
        self.channelGroup = QtGui.QGroupBox('Channel Range')
        self.probeButton = QtGui.QRadioButton('By Probe Type')
        self.probeButton.setChecked(True)
        self.probeButton.toggled.connect(self.switchModes)
        self.probeDropdown = QtGui.QComboBox()
        for n in [64, 128, 256, 512, 1024]:
            self.probeDropdown.addItem('%d chan' % n)
        self.probeDropdown.setCurrentIndex(4)
        self.probeDropdown.currentIndexChanged.connect(self.handleRefresh)
        self.manualButton = QtGui.QRadioButton('Manual')
        self.manualButton.setChecked(False)
        self.manualButton.toggled.connect(self.switchModes)
        self.chanMinLine = QtGui.QLineEdit('0')
        self.chanMaxLine = QtGui.QLineEdit('1024')
        self.switchModes() # initialize
        layout = QtGui.QGridLayout()
        layout.addWidget(self.probeButton, 0,0, 1,1)
        layout.addWidget(self.probeDropdown, 0,1, 1,2)
        layout.addWidget(self.manualButton, 1,0, 1,1)
        layout.addWidget(self.chanMinLine, 1,1, 1,1)
        layout.addWidget(self.chanMaxLine, 1,2, 1,1)
        self.channelGroup.setLayout(layout)
        self.channelGroup.setMaximumWidth(250)

    def createTimeGroup(self):
        self.timeGroup = QtGui.QGroupBox('Time Range (ms)')
        self.timeMinLine = QtGui.QLineEdit(str(int(self.dataset.timeMin)))
        # bit of a kludge to make the formatting of the initial timerange
        #   look reasonable:
        self.timeMaxLine = QtGui.QLineEdit(str(self.dataset.nsamples/30))
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.timeMinLine)
        layout.addWidget(self.timeMaxLine)
        self.timeGroup.setLayout(layout)
        self.timeGroup.setMaximumWidth(250)

    def createButtons(self):
        self.buttons = QtGui.QWidget()
        self.refreshButton = QtGui.QPushButton('Refresh')
        self.refreshButton.clicked.connect(self.handleRefresh)
        self.defaultButton = QtGui.QPushButton('Default')
        self.defaultButton.clicked.connect(self.handleDefault)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.refreshButton)
        layout.addWidget(self.defaultButton)
        self.buttons.setLayout(layout)

    def handleRefresh(self):
        self.rangeUpdated.emit(self.getParams())

    def handleDefault(self):
        self.chanMinLine.setText('0')
        self.chanMaxLine.setText('1024')
        self.timeMinLine.setText(str(self.dataset.timeMin))
        self.timeMaxLine.setText(str(self.dataset.timeMax))
        self.probeDropdown.setCurrentIndex(4)
        self.probeButton.setChecked(True)
        self.rangeUpdated.emit(self.getParams())

    def switchModes(self):
        if self.probeButton.isChecked():
            self.probeMode = True
            self.probeDropdown.setEnabled(True)
            self.chanMinLine.setEnabled(False)
            self.chanMaxLine.setEnabled(False)
        elif self.manualButton.isChecked():
            self.probeMode = False
            self.probeDropdown.setEnabled(False)
            self.chanMinLine.setEnabled(True)
            self.chanMaxLine.setEnabled(True)

    def getParams(self):
        params = {}
        params['probeType'] = int(str(self.probeDropdown.currentText()).split()[0])
        params['channelRange'] = [int(self.chanMinLine.text()), int(self.chanMaxLine.text())]
        params['timeRange'] = [float(self.timeMinLine.text()), float(self.timeMaxLine.text())]
        params['probeMode'] = self.probeMode
        return params

class PlotPanel(QtGui.QWidget):


    def __init__(self, dataset):
        QtGui.QWidget.__init__(self)
        self.dataset = dataset

        self.fig = Figure()
        self.fig.subplots_adjust(left=0.05, bottom=0.08, right=1.0, top=0.92)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

    def drawWaterfall(self):
        self.axes = self.fig.add_subplot(111)
        self.axesImage = self.axes.imshow(self.dataset.data_uv, cm.Spectral, aspect='auto',
            extent=[self.dataset.timeMin, self.dataset.timeMax, 1024, 0])
        self.axes.set_xlabel('Time (ms)')
        self.axes.set_ylabel('Channel Count')
        self.colorbar = self.fig.colorbar(self.axesImage, use_gridspec=True)
        self.colorbar.set_label('microVolts')

    def setRange(self, controlParams):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        timeMin, timeMax = controlParams['timeRange']
        probeMode = controlParams['probeMode']
        if probeMode:
            probeType = controlParams['probeType']
            chanMin, chanMax = 0, probeType
        else:
            chanMin, chanMax = controlParams['channelRange']
        self.axes.axis([timeMin, timeMax, chanMin, chanMax])
        self.canvas.draw()
        QtGui.QApplication.restoreOverrideCursor()

    def setColorBar(self, vmin, vmax):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.axesImage.set_clim(vmin, vmax)
        self.canvas.draw()
        QtGui.QApplication.restoreOverrideCursor()

class WaterfallPlotWindow(QtGui.QWidget):

    def __init__(self, dataset):
        QtGui.QWidget.__init__(self)
        self.dataset = dataset

        self.controlPanel = ControlPanel(self.dataset)
        self.plotPanel = PlotPanel(self.dataset)
        self.plotPanel.drawWaterfall()

        self.controlPanel.histoControl.limitsChanged.connect(self.plotPanel.setColorBar)
        self.controlPanel.rangeUpdated.connect(self.plotPanel.setRange)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.controlPanel)
        self.layout.addWidget(self.plotPanel)
        self.setLayout(self.layout)

        self.setWindowTitle('Waterfall Plot: %s' % self.dataset.filename)
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.resize(1600,800)

    def initializeWaterfallPlot(self):
        self.drawSpectrogram()

        self.controlPanel = self.ControlPanel(self.data, self.sampleRange, self.canvas)

        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.mplLayout = QtGui.QVBoxLayout()
        self.mplLayout.addWidget(self.canvas)
        self.mplLayout.addWidget(self.mpl_toolbar)
        self.mplWindow = QtGui.QWidget()
        self.mplWindow.setLayout(self.mplLayout)

    def closeEvent(self, event):
        # memory management
        del(self.plotPanel.axesImage)
        self.plotPanel.axes.cla()
        self.plotPanel.fig.clf()

if __name__=='__main__':
    import config
    from ImportDialog import ImportDialog
    app = QtGui.QApplication(sys.argv)
    filename = str(QtGui.QFileDialog.getOpenFileName(None,
        'Select Data File', config.dataDir))
    if filename:
        dlg = ImportDialog()
        if dlg.exec_():
            params = dlg.getParams()
            sampleRange = params['sampleRange']
            dataset = WillowDataset(filename, sampleRange)
            dataset.importData()
            waterfallPlotWindow = WaterfallPlotWindow(dataset)
            waterfallPlotWindow.show()
            app.exec_()
