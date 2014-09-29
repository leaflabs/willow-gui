from PyQt4 import QtCore, QtGui
import os, sys, h5py

import numpy as np

from progressbar import ProgressBar
from ProgressBarWindow import ProgressBarWindow

from parameters import DAEMON_DIR, DATA_DIR
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

import numpy as np
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from collections import OrderedDict
from WaterfallPlotWindow import WaterfallPlotWindow

def createLabelLine(labelText, lineWidget):
    widget = QtGui.QWidget()
    layout = QtGui.QHBoxLayout()
    layout.addWidget(QtGui.QLabel(labelText))
    layout.addWidget(lineWidget)
    widget.setLayout(layout)
    return widget

class PlotWindow(QtGui.QWidget):

    def __init__(self, parent, filename, sampleRange):
        super(PlotWindow, self).__init__(None)

        self.parent = parent
        self.filename = filename
        self.sampleRange = sampleRange
        self.importData()


        ###################
        # Control Panel
        ###################

        self.controlPanel = self.ControlPanel(self)

        ###################
        # Matplotlib Setup
        ###################

        self.initializeMPL()
        self.updateChannels()

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

        self.setWindowTitle('Plotting: %s' % self.filename)
        self.setWindowIcon(QtGui.QIcon('round_logo_60x60.png'))
        self.resize(1600,800)

    class ControlPanel(QtGui.QWidget):

        def __init__(self, parent):
            super(parent.ControlPanel, self).__init__()
            self.parent = parent
            self.channelsGroup = self.ChannelsGroup(self)
            self.zoomGroup = self.ZoomGroup(self)
            self.waterfallButton = QtGui.QPushButton('Waterfall')
            self.waterfallButton.clicked.connect(self.parent.launchWaterfall)
            self.layout = QtGui.QHBoxLayout()
            self.layout.addWidget(self.channelsGroup)
            self.layout.addWidget(self.zoomGroup)
            self.layout.addWidget(self.waterfallButton)
            self.setLayout(self.layout)
            self.setMaximumHeight(200)

        class ChannelsGroup(QtGui.QGroupBox):

            def __init__(self, parent):
                super(parent.ChannelsGroup, self).__init__()
                self.parent = parent
                self.setTitle('Channel Control')

                self.nchannelsDropdown = QtGui.QComboBox()
                self.nchannelsLayoutDict = OrderedDict([(1,(1,1)),
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
                for item in self.nchannelsLayoutDict.items():
                    self.nchannelsDropdown.addItem(str(item[0]))
                self.nchannelsDropdown.setCurrentIndex(6)
                self.nchannelsDropdown.currentIndexChanged.connect(self.handleNChannelChange)

                self.bankSpinBox = QtGui.QSpinBox()
                nchannels = int(self.nchannelsDropdown.currentText())
                self.bankSpinBox.setMaximum(1023//nchannels)
                self.bankSpinBox.valueChanged.connect(self.handleBankChange)

                self.layout = QtGui.QVBoxLayout()
                self.layout.addWidget(QtGui.QLabel('Number of Channels:'))
                self.layout.addWidget(self.nchannelsDropdown)
                self.layout.addWidget(QtGui.QLabel('Bank:'))
                self.layout.addWidget(self.bankSpinBox)
                self.setLayout(self.layout)
                self.setMaximumWidth(220)

            def handleNChannelChange(self, index):
                nchannels = int(self.nchannelsDropdown.currentText())
                self.bankSpinBox.setMaximum(1023//nchannels)
                self.parent.parent.updateChannels()

            def handleBankChange(self):
                self.parent.parent.updateChannels()

        class ZoomGroup(QtGui.QGroupBox):

            def __init__(self, parent):
                super(parent.ZoomGroup, self).__init__()
                self.parent = parent
                self.setTitle('Zoom Control')
                xmin = self.parent.parent.sampleRange[0]
                xmax = self.parent.parent.sampleRange[1]
                ymin = 0
                ymax = 2**16-1
                #
                self.autoButton = QtGui.QRadioButton('Auto')
                self.autoButton.setChecked(True)
                self.mode = 'auto'
                self.autoButton.toggled.connect(self.switchModes)
                self.manualButton = QtGui.QRadioButton('Manual')
                self.manualButton.toggled.connect(self.switchModes)
                self.xminLine = QtGui.QLineEdit(str(xmin))
                self.xmaxLine = QtGui.QLineEdit(str(xmax))
                self.yminLine = QtGui.QLineEdit(str(ymin))
                self.ymaxLine = QtGui.QLineEdit(str(ymax))
                grid = QtGui.QWidget()
                gridLayout = QtGui.QGridLayout()
                gridLayout.addWidget(self.autoButton, 0,0)
                gridLayout.addWidget(self.manualButton, 0,1)
                gridLayout.addWidget(QtGui.QLabel('X-Range:'), 1,0)
                gridLayout.addWidget(self.xminLine, 1,1)
                gridLayout.addWidget(self.xmaxLine, 1,2)
                gridLayout.addWidget(QtGui.QLabel('Y-Range:'), 2,0)
                gridLayout.addWidget(self.yminLine, 2,1)
                gridLayout.addWidget(self.ymaxLine, 2,2)
                grid.setLayout(gridLayout)

                self.refreshButton = QtGui.QPushButton('Refresh')
                self.refreshButton.clicked.connect(self.parent.parent.updateZoom_redraw)
                self.defaultButton = QtGui.QPushButton('Default')
                self.defaultButton.clicked.connect(self.parent.parent.defaultZoom)
                buttons = QtGui.QWidget()
                buttonLayout = QtGui.QHBoxLayout()
                buttonLayout.addWidget(self.refreshButton)
                buttonLayout.addWidget(self.defaultButton)
                buttons.setLayout(buttonLayout)

                self.layout = QtGui.QVBoxLayout()
                self.layout.addWidget(grid)
                self.layout.addWidget(buttons)

                self.setLayout(self.layout)
                self.setMaximumWidth(300)

                self.switchModes()

            def switchModes(self):
                if self.autoButton.isChecked():
                    self.mode = 'auto'
                    for widg in [self.xminLine, self.xmaxLine, self.yminLine, self.ymaxLine,
                                    self.refreshButton, self.defaultButton]:
                        widg.setEnabled(False)
                    try:
                        self.parent.parent.updateZoom_redraw()
                    except AttributeError:
                        print 'Caught AttributeError'
                elif self.manualButton.isChecked():
                    self.mode = 'manual'
                    for widg in [self.xminLine, self.xmaxLine, self.yminLine, self.ymaxLine,
                                    self.refreshButton, self.defaultButton]:
                        widg.setEnabled(True)

        def launchWaterfall(self):
            self.parent.launchWaterfall()

    def importData(self):
        f = h5py.File(self.filename)
        dset = f['wired-dataset']
        if self.sampleRange == -1:
            self.sampleRange = [0, len(dset)-1]
        self.nsamples = self.sampleRange[1] - self.sampleRange[0] + 1
        self.sampleNumbers = np.arange(self.sampleRange[0], self.sampleRange[1]+1)
        self.data = np.zeros((1024,self.nsamples), dtype='uint16')
        progressBarWindow = ProgressBarWindow(self.nsamples, 'Importing data...')
        progressBarWindow.show()
        for i in range(self.nsamples):
            self.data[:,i] = dset[i][3][:1024]
            progressBarWindow.update(i)
        self.data_uv = (np.array(self.data, dtype='float')-2**15)*0.2

    def initializeMPL(self):
        #self.fig = Figure((5.0, 4.0), dpi=100)
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)

    def updateChannels(self):
        channelsGroup = self.controlPanel.channelsGroup
        zoomGroup = self.controlPanel.zoomGroup
        nchannels = int(channelsGroup.nchannelsDropdown.currentText())
        nrows, ncols = channelsGroup.nchannelsLayoutDict[nchannels]
        bank = int(channelsGroup.bankSpinBox.value())
        self.channelList = range(bank*nchannels,(bank+1)*nchannels)
        self.fig.clear()
        self.axesList = []
        self.waveformList = []
        for i in range(nchannels):
            channel = self.channelList[i]
            axes = self.fig.add_subplot(nrows, ncols, i+1)
            axes.set_title('Channel %d' % channel, fontsize=10, fontweight='bold')
            axes.set_axis_bgcolor('k')
            waveform = axes.plot(self.sampleNumbers, self.data_uv[channel,:], color='#8fdb90')
            self.axesList.append(axes)
            self.waveformList.append(waveform)
        self.updateZoom()
        self.fig.subplots_adjust(left=0.05, bottom=0.08, right=0.98, top=0.92, wspace=0.08, hspace=0.4)
        self.canvas.draw()

    def updateZoom(self):
        zoomGroup = self.controlPanel.zoomGroup
        if zoomGroup.mode == 'manual':
            xmin = int(zoomGroup.xminLine.text())
            xmax = int(zoomGroup.xmaxLine.text())
            ymin = int(zoomGroup.yminLine.text())
            ymax = int(zoomGroup.ymaxLine.text())
        elif zoomGroup.mode == 'auto':
            xmin = self.sampleRange[0]
            xmax = self.sampleRange[1]
            ymin_hard = np.min(self.data_uv[self.channelList,:])
            ymax_hard = np.max(self.data_uv[self.channelList,:])
            deltay = ymax_hard - ymin_hard
            ymin = ymin_hard - deltay//2
            ymax = ymax_hard + deltay//2
            zoomGroup.xminLine.setText(str(xmin))
            zoomGroup.xmaxLine.setText(str(xmax))
            zoomGroup.yminLine.setText(str(ymin))
            zoomGroup.ymaxLine.setText(str(ymax))
        for axes in self.axesList:
            axes.axis([xmin, xmax, ymin, ymax], fontsize=10)

    def updateZoom_redraw(self):
        # this is stupid; trouble with default argument redraw 20140929
        zoomGroup = self.controlPanel.zoomGroup
        if zoomGroup.mode == 'manual':
            xmin = int(zoomGroup.xminLine.text())
            xmax = int(zoomGroup.xmaxLine.text())
            ymin = int(zoomGroup.yminLine.text())
            ymax = int(zoomGroup.ymaxLine.text())
        elif zoomGroup.mode == 'auto':
            xmin = self.sampleRange[0]
            xmax = self.sampleRange[1]
            ymin_hard = np.min(self.data_uv[self.channelList,:])
            ymax_hard = np.max(self.data_uv[self.channelList,:])
            deltay = ymax_hard - ymin_hard
            ymin = ymin_hard - deltay//2
            if ymin < 0: ymin = 0
            ymax = ymax_hard + deltay//2
            if ymax > 2**16-1: ymax = 2**16-1
            zoomGroup.xminLine.setText(str(xmin))
            zoomGroup.xmaxLine.setText(str(xmax))
            zoomGroup.yminLine.setText(str(ymin))
            zoomGroup.ymaxLine.setText(str(ymax))
        for axes in self.axesList:
            axes.axis([xmin, xmax, ymin, ymax], fontsize=10)
        self.canvas.draw()

    def calculateYTicks(self, ymin, ymax):
        if ((ymin < 2**15) and (ymax > 2**15)):
            if (2**15-ymin) < (ymax-2**15):
                ytick_locs = np.linspace(ymin, ymax, 5)
                ytick_lbls = ['%3.2f uv' % ((cnt-2**15)*0.2) for cnt in ytick_locs]

    def defaultZoom(self):
        zoomGroup = self.controlPanel.zoomGroup
        zoomGroup.xminLine.setText(str(self.sampleRange[0]))
        zoomGroup.xmaxLine.setText(str(self.sampleRange[1]))
        zoomGroup.yminLine.setText(str(0))
        zoomGroup.ymaxLine.setText(str(2**16-1))
        self.updateZoom()

    def launchWaterfall(self):
        self.waterfallPlotWindow = WaterfallPlotWindow(self)
        self.waterfallPlotWindow.show()

    def closeEvent(self, event):
        print 'closing'

if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    main = PlotWindow(None, '/home/chrono/sng/data/justin/neuralRecording_10sec.h5', [0,5000])
    main.show()
    app.exec_()
