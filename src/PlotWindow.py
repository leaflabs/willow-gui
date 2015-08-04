from PyQt4 import QtCore, QtGui
import os, sys, h5py

import numpy as np

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from collections import OrderedDict
from WaterfallPlotWindow import WaterfallPlotWindow

from WillowDataset import WillowDataset

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

class ControlPanel(QtGui.QWidget):

    channelsUpdated = QtCore.pyqtSignal(dict)
    zoomUpdated = QtCore.pyqtSignal(dict)

    def __init__(self, dataset):
        QtGui.QWidget.__init__(self)
        self.dataset = dataset
        self.createChannelsGroup()
        self.createZoomGroup()
        self.waterfallButton = QtGui.QPushButton('Waterfall Plot')
        self.waterfallButton.setMaximumWidth(220)
        self.waterfallButton.clicked.connect(self.launchWaterfall)
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.channelsGroup)
        self.layout.addWidget(self.zoomGroup)
        self.layout.addWidget(self.waterfallButton)
        self.setLayout(self.layout)
        self.setMaximumHeight(220)

    def createChannelsGroup(self):
        self.channelsGroup = QtGui.QGroupBox('Channel Control')
        self.nchannelsDropdown = QtGui.QComboBox()
        for item in LAYOUT_DICT.items():
            self.nchannelsDropdown.addItem(str(item[0]))
        self.nchannelsDropdown.setCurrentIndex(6)
        self.nchannelsDropdown.currentIndexChanged.connect(self.handleNChannelChange)

        self.bankSpinBox = QtGui.QSpinBox()
        nchannels = int(self.nchannelsDropdown.currentText())
        self.bankSpinBox.setMaximum(1023//nchannels)
        self.bankSpinBox.valueChanged.connect(self.handleBankChange)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('Number of Channels:'))
        layout.addWidget(self.nchannelsDropdown)
        layout.addWidget(QtGui.QLabel('Bank:'))
        layout.addWidget(self.bankSpinBox)
        self.channelsGroup.setLayout(layout)
        self.channelsGroup.setMaximumWidth(220)

    def handleNChannelChange(self, index):
        # Q: how to handle overloaded pyqt signal to get the value?
        nchannels = int(self.nchannelsDropdown.currentText())
        self.bankSpinBox.setValue(0)
        self.bankSpinBox.setMaximum(1023//nchannels)
        self.channelsUpdated.emit(self.getParams())

    def handleBankChange(self, bank):
        nchannels = int(self.nchannelsDropdown.currentText())
        self.channelsUpdated.emit(self.getParams())

    def createZoomGroup(self):

        self.zoomGroup = QtGui.QGroupBox('Zoom Control')

        xmin, xmax, ymin, ymax = self.dataset.limits
        ####
        self.autoButton = QtGui.QRadioButton('Auto')
        self.autoButton.setChecked(True)
        self.autoButton.toggled.connect(self.switchModes)
        self.manualButton = QtGui.QRadioButton('Manual')
        self.manualButton.toggled.connect(self.switchModes)
        self.xminLine = QtGui.QLineEdit(str(xmin))
        self.xmaxLine = QtGui.QLineEdit(str(xmax))
        self.yminLine = QtGui.QLineEdit('-6000.0')
        self.ymaxLine = QtGui.QLineEdit('6000.0')
        self.refreshButton = QtGui.QPushButton('Refresh')
        self.refreshButton.clicked.connect(self.handleZoomRefresh)
        self.defaultButton = QtGui.QPushButton('Default')
        self.defaultButton.clicked.connect(self.handleZoomDefault)
        self.switchModes() # initialize
        ###
        modes = QtGui.QWidget()
        modesLayout = QtGui.QHBoxLayout()
        modesLayout.addWidget(self.autoButton)
        modesLayout.addWidget(self.manualButton)
        modes.setLayout(modesLayout)
        ###
        grid = QtGui.QWidget()
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(QtGui.QLabel('X-Range (ms):'), 0,0)
        gridLayout.addWidget(self.xminLine, 0,1)
        gridLayout.addWidget(self.xmaxLine, 0,2)
        gridLayout.addWidget(QtGui.QLabel('Y-Range (uv):'), 1,0)
        gridLayout.addWidget(self.yminLine, 1,1)
        gridLayout.addWidget(self.ymaxLine, 1,2)
        grid.setLayout(gridLayout)
        ###
        buttons = QtGui.QWidget()
        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.refreshButton)
        buttonLayout.addWidget(self.defaultButton)
        buttons.setLayout(buttonLayout)
        ###
        layout = QtGui.QVBoxLayout()
        layout.addWidget(modes)
        layout.addWidget(grid)
        layout.addWidget(buttons)

        self.zoomGroup.setLayout(layout)
        self.zoomGroup.setMaximumWidth(300)


    def switchModes(self):
        if self.autoButton.isChecked():
            self.autoMode = True
            for widg in [self.xminLine, self.xmaxLine, self.yminLine, self.ymaxLine,
                            self.refreshButton, self.defaultButton]:
                widg.setEnabled(False)
            self.handleZoomDefault()
        elif self.manualButton.isChecked():
            self.autoMode = False
            for widg in [self.xminLine, self.xmaxLine, self.yminLine, self.ymaxLine,
                            self.refreshButton, self.defaultButton]:
                widg.setEnabled(True)

    def setZoom(self, xmin, xmax, ymin, ymax):
        self.xminLine.setText(str(xmin))
        self.xmaxLine.setText(str(xmax))
        self.yminLine.setText(str(ymin))
        self.ymaxLine.setText(str(ymax))

    def handleZoomRefresh(self):
        self.zoomUpdated.emit(self.getParams())

    def handleZoomDefault(self):
        defaultParams = {}
        defaultParams['nchannels'] = int(self.nchannelsDropdown.currentText())
        defaultParams['bank'] = int(self.bankSpinBox.value())
        defaultParams['xrange'] = [0,0]
        defaultParams['yrange'] = [0,0]
        defaultParams['autoMode'] = True
        self.zoomUpdated.emit(defaultParams)
        # after plotpanel calculates autozoom parameters, it sends a signal back,
        # which gets handled by ControlPanel.setZoom()

    def launchWaterfall(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.waterfallPlotWindow = WaterfallPlotWindow(self.dataset)
        self.waterfallPlotWindow.show()
        QtGui.QApplication.restoreOverrideCursor()

    def getParams(self):
        params = {}
        params['nchannels'] = int(self.nchannelsDropdown.currentText())
        params['bank'] = int(self.bankSpinBox.value())
        params['xrange'] = [float(self.xminLine.text()), float(self.xmaxLine.text())]
        params['yrange'] = [float(self.yminLine.text()), float(self.ymaxLine.text())]
        params['autoMode'] = self.autoMode
        return params


class PlotPanel(QtGui.QWidget):

    autoZoomCalculated = QtCore.pyqtSignal(int, int, int, int)

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

    def setChannels(self, controlParams):
        nchannels = controlParams['nchannels']
        bank = controlParams['bank']
        nrows, ncols = LAYOUT_DICT[nchannels]
        self.channelList = range(bank*nchannels,(bank+1)*nchannels)
        self.fig.clear()
        self.axesList = []
        for i in range(nchannels):
            channel = self.channelList[i]
            axes = self.fig.add_subplot(nrows, ncols, i+1)
            axes.set_title('Channel %d' % channel, fontsize=10, fontweight='bold')
            axes.set_axis_bgcolor('k')
            axes.plot(self.dataset.time_ms, self.dataset.data_uv[channel,:], color='#8fdb90')
            self.axesList.append(axes)
        self.fig.subplots_adjust(left=0.05, bottom=0.08, right=0.98, top=0.92, wspace=0.08, hspace=0.4)
        self.setZoom(controlParams)

    def setZoom(self, controlParams):
        autoMode = controlParams['autoMode']
        if autoMode:
            xmin = self.dataset.timeMin
            xmax = self.dataset.timeMax
            ymin_hard = np.min(self.dataset.data_uv[self.channelList,:])
            ymax_hard = np.max(self.dataset.data_uv[self.channelList,:])
            deltay = ymax_hard - ymin_hard
            ymin = ymin_hard - deltay//2
            ymax = ymax_hard + deltay//2
            self.autoZoomCalculated.emit(xmin, xmax, ymin, ymax)
        else:
            xmin, xmax = controlParams['xrange']
            ymin, ymax = controlParams['yrange']
        for axes in self.axesList:
            axes.axis([xmin, xmax, ymin, ymax], fontsize=10)
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.canvas.draw()
        QtGui.QApplication.restoreOverrideCursor()

class PlotWindow(QtGui.QWidget):

    def __init__(self, dataset):
        QtGui.QWidget.__init__(self)
        self.dataset = dataset

        self.controlPanel = ControlPanel(self.dataset)
        self.plotPanel = PlotPanel(self.dataset)
        self.controlPanel.channelsUpdated.connect(self.plotPanel.setChannels)
        self.controlPanel.zoomUpdated.connect(self.plotPanel.setZoom)
        self.plotPanel.autoZoomCalculated.connect(self.controlPanel.setZoom)
        self.plotPanel.setChannels(self.controlPanel.getParams())

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.controlPanel)
        self.layout.addWidget(self.plotPanel)
        self.setLayout(self.layout)

        self.setWindowTitle('Plotting: %s' % self.dataset.filename)
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.resize(1600,800)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    def closeEvent(self, event):
        # clear matplotlib objects
        for ax in self.plotPanel.axesList:
            ax.lines = []
            ax.cla()
        self.plotPanel.fig.clf()

if __name__=='__main__':
    print 'PID = %d' % os.getpid()
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
        plotWindow = PlotWindow(dataset)
        plotWindow.show()
        app.exec_()
