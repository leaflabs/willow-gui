from PyQt4 import QtCore, QtGui
import os, sys, h5py
import numpy as np

from progressbar import ProgressBar

from parameters import DAEMON_DIR, DATA_DIR
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

import numpy as np
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from collections import OrderedDict

def createLabelLine(labelText, lineWidget):
    widget = QtGui.QWidget()
    layout = QtGui.QHBoxLayout()
    layout.addWidget(QtGui.QLabel(labelText))
    layout.addWidget(lineWidget)
    widget.setLayout(layout)
    return widget

class PlotWindow(QtGui.QWidget):

    def __init__(self, parent, filename, nsamples):
        super(PlotWindow, self).__init__(None)

        self.parent = parent
        self.filename = filename
        self.nsamples = nsamples

        self.state = self.ChangeState()

        ###################
        # Control Panel
        ###################

        # Number of Channels
        self.nchannelsGroupBox = QtGui.QGroupBox('Number of Channels')
        nchannelsLayout = QtGui.QVBoxLayout()

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
        self.nchannelsDropdown.currentIndexChanged.connect(self.flagNchannels)

        nchannelsLayout.addWidget(self.nchannelsDropdown)
        self.nchannelsGroupBox.setLayout(nchannelsLayout)

        # Channel List
        self.channelListGroupBox = QtGui.QGroupBox('Channel List')
        self.channelListLine = QtGui.QLineEdit('96, 97, 98, 99, 100, 101, 102, 103')
        self.channelListLine.editingFinished.connect(self.flagChannelList)
        # -> is this the signal you want? consider also textChanged and textEdited
        channelListLayout = QtGui.QVBoxLayout()
        channelListLayout.addWidget(self.channelListLine)
        self.channelListGroupBox.setLayout(channelListLayout)
        self.channelListGroupBox.setMaximumWidth(300)

        # Zoom Control
        self.zoomGroupBox = QtGui.QGroupBox('Zoom Control')
        zoomLayout = QtGui.QGridLayout()

        self.xRangeMin= QtGui.QLineEdit('0')
        self.xRangeMax = QtGui.QLineEdit(str(self.nsamples))
        zoomLayout.addWidget(QtGui.QLabel('X-Range:'), 0, 0)
        zoomLayout.addWidget(self.xRangeMin, 0, 1)
        zoomLayout.addWidget(self.xRangeMax, 0, 2)

        self.yRangeMin = QtGui.QLineEdit('0')
        self.yRangeMax = QtGui.QLineEdit('65535')
        zoomLayout.addWidget(QtGui.QLabel('Y-Range:'),1,0)
        zoomLayout.addWidget(self.yRangeMin, 1, 1)
        zoomLayout.addWidget(self.yRangeMax, 1, 2)

        for widg in [self.xRangeMin, self.xRangeMax, self.yRangeMin, self.yRangeMax]:
            widg.editingFinished.connect(self.flagZoom)

        self.zoomGroupBox.setLayout(zoomLayout)
        self.zoomGroupBox.setMaximumWidth(200)

        # Buttons
        self.refreshButton = QtGui.QPushButton('Refresh')
        self.refreshButton.clicked.connect(self.refresh)
        self.defaultButton = QtGui.QPushButton('Default Settings')
        self.defaultButton.clicked.connect(self.setDefaults)
        self.buttons = QtGui.QWidget()
        tmp = QtGui.QVBoxLayout()
        tmp.addWidget(self.refreshButton)
        tmp.addWidget(self.defaultButton)
        self.buttons.setLayout(tmp)

        self.controlPanel = QtGui.QWidget()
        controlPanelLayout = QtGui.QHBoxLayout()
        controlPanelLayout.addWidget(self.nchannelsGroupBox)
        controlPanelLayout.addWidget(self.channelListGroupBox)
        controlPanelLayout.addWidget(self.zoomGroupBox)
        controlPanelLayout.addWidget(self.buttons)
        self.controlPanel.setLayout(controlPanelLayout)
        self.controlPanel.setMaximumHeight(100)

        ###################
        # Matplotlib Setup
        ###################

        self.importData()
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

        self.setWindowTitle('WiredLeaf Plotting Window')
        self.setWindowIcon(QtGui.QIcon('round_logo_60x60.png'))
        self.resize(1600,800)


    def importData(self):
        f = h5py.File(self.filename)
        dset = f['wired-dataset']
        self.data = np.zeros((1024,self.nsamples), dtype='uint16')
        pbar = ProgressBar(maxval=self.nsamples-1).start()
        for i in range(self.nsamples):
            pbar.update(i)
            self.data[:,i] = dset[i][3][:1024]
        pbar.finish()

    def initializeMPL(self):
        #self.fig = Figure((5.0, 4.0), dpi=100)
        self.fig = Figure()
        #self.fig.subplots_adjust(left=0.,bottom=0.,right=1.,top=1., wspace=0.04, hspace=0.1)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.xvalues = np.arange(self.nsamples)

    def updateChannels(self):
        nchannels = int(self.nchannelsDropdown.currentText())
        nrows, ncols = self.nchannelsLayoutDict[nchannels]
        channelList = [int(s) for s in str(self.channelListLine.text()).split(',')]
        xmin = int(self.xRangeMin.text())
        xmax = int(self.xRangeMax.text())
        ymin = int(self.yRangeMin.text())
        ymax = int(self.yRangeMax.text())
        if len(channelList) > nchannels:
            self.parent.parent.statusBox.append('Warning: Truncating channel list to %d channels' % nchannels)
        self.fig.clear()
        self.axesList = []
        self.waveformList = []
        for i in range(nchannels):
            channel = channelList[i]
            axes = self.fig.add_subplot(nrows, ncols, i+1)
            axes.set_title('Channel %d' % channel, fontsize=10, fontweight='bold')
            #axes.yaxis.set_ticklabels([])
            #xtickLabels = axes.xaxis.get_ticklabels()
            #axes.xaxis.set_ticklabels([0,self.maxXvalue/2, self.maxXvalue], fontsize=10)
            axes.tick_params(labelsize=10)
            axes.set_axis_bgcolor('k')
            axes.axis([xmin, xmax, ymin, ymax], fontsize=10)
            waveform = axes.plot(self.xvalues, self.data[channel,:], color='#8fdb90')
            #waveform = axes.plot(self.xvalues, np.array([2**15-1]*self.nsamples, dtype='uint16'), color='#8fdb90')
            self.axesList.append(axes)
            self.waveformList.append(waveform)
        self.fig.subplots_adjust(left=0.05, bottom=0.08, right=0.98, top=0.92, wspace=0.08, hspace=0.4)
        self.canvas.draw()
        self.state.channelsChanged = False

    def updateZoom(self):
        xmin = int(self.xRangeMin.text())
        xmax = int(self.xRangeMax.text())
        ymin = int(self.yRangeMin.text())
        ymax = int(self.yRangeMax.text())
        for axes in self.axesList:
            axes.axis([xmin, xmax, ymin, ymax], fontsize=10)
        self.canvas.draw()
        self.state.zoomChanged = False

    def flagNchannels(self):
        self.state.channelsChanged = True

    def flagChannelList(self):
        self.state.channelsChanged = True

    def flagZoom(self):
        self.state.zoomChanged = True

    def refresh(self):
        if self.state.channelsChanged:
            self.updateChannels()
        elif self.state.zoomChanged:
            self.updateZoom()

    def setDefaults(self):
        self.nchannelsDropdown.setCurrentIndex(6)
        self.channelListLine.setText('96, 97, 98, 99, 100, 101, 102, 103')
        self.xRangeMin.setText('0')
        self.xRangeMax.setText(str(self.nsamples))
        self.yRangeMin.setText('0')
        self.yRangeMax.setText(str(2**16-1))
        self.state.channelsChanged = True
        self.updateChannels()

    class ChangeState():

        def __init__(self):
            self.channelsChanged = False
            self.zoomChanged = False

    def closeEvent(self, event):
        print 'closing'

