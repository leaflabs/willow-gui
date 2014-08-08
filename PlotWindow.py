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

        ###################
        # Control Panel
        ###################

        # Number of Channels
        self.nchannelsGroupBox = QtGui.QGroupBox('Number of Channels')
        nchannelsLayout = QtGui.QVBoxLayout()
        radButton1 = QtGui.QRadioButton('1')
        nchannelsLayout.addWidget(radButton1)
        radButton2 = QtGui.QRadioButton('2')
        nchannelsLayout.addWidget(radButton2)
        radButton4 = QtGui.QRadioButton('4')
        nchannelsLayout.addWidget(radButton4)
        radButton6 = QtGui.QRadioButton('6')
        nchannelsLayout.addWidget(radButton6)
        radButton8 = QtGui.QRadioButton('8')
        radButton8.setChecked(True)
        nchannelsLayout.addWidget(radButton8)
        radButton12 = QtGui.QRadioButton('12')
        nchannelsLayout.addWidget(radButton12)
        radButton16 = QtGui.QRadioButton('16')
        nchannelsLayout.addWidget(radButton16)
        self.nchannelsGroupBox.setLayout(nchannelsLayout)

        # Channel List
        self.channelListGroupBox = QtGui.QGroupBox('Channel List')
        self.channelListEdit = QtGui.QTextEdit('0,1,2,3,4,5,6,7')
        channelListLayout = QtGui.QVBoxLayout()
        channelListLayout.addWidget(self.channelListEdit)
        self.channelListGroupBox.setLayout(channelListLayout)
        self.channelListGroupBox.setMaximumWidth(200)

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

        self.zoomGroupBox.setLayout(zoomLayout)
        self.zoomGroupBox.setMaximumWidth(200)

        # Refresh Button
        self.refreshButton = QtGui.QPushButton('Refresh')
        self.refreshButton.clicked.connect(self.refresh)

        self.controlPanel = QtGui.QWidget()
        controlPanelLayout = QtGui.QHBoxLayout()
        controlPanelLayout.addWidget(self.nchannelsGroupBox)
        controlPanelLayout.addWidget(self.channelListGroupBox)
        controlPanelLayout.addWidget(self.zoomGroupBox)
        controlPanelLayout.addWidget(self.refreshButton)
        self.controlPanel.setLayout(controlPanelLayout)

        ###################
        # Matplotlib Setup
        ###################

        #self.fig = Figure((5.0, 4.0), dpi=100)
        self.fig = Figure()
        #self.fig.subplots_adjust(left=0.,bottom=0.,right=1.,top=1., wspace=0.04, hspace=0.1)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.xvalues = np.arange(self.nsamples)
        self.maxXvalue = max(self.xvalues)
        self.axesList = []
        self.waveformList = []
        for i in range(8):
            axes = self.fig.add_subplot(4, 2, i+1)
            axes.set_title('Channel %d' % i, fontsize=10, fontweight='bold')
            #axes.yaxis.set_ticklabels([])
            #xtickLabels = axes.xaxis.get_ticklabels()
            #axes.xaxis.set_ticklabels([0,self.maxXvalue/2, self.maxXvalue], fontsize=10)
            axes.tick_params(labelsize=10)
            axes.set_axis_bgcolor('k')
            axes.axis([0,self.nsamples,0,2**16-1], fontsize=10)
            waveform = axes.plot(np.arange(self.nsamples), np.array([2**15]*self.nsamples), color='#8fdb90')
            self.axesList.append(axes)
            self.waveformList.append(waveform)
        self.fig.subplots_adjust(left=0.05, bottom=0.08, right=0.98, top=0.92, wspace=0.08, hspace=0.4)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)

        self.mplLayout = QtGui.QVBoxLayout()
        self.mplLayout.addWidget(self.canvas)
        self.mplLayout.addWidget(self.mpl_toolbar)
        self.mplWindow = QtGui.QWidget()
        self.mplWindow.setLayout(self.mplLayout)

        self.canvas.draw()

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

        self.importData()

    def importData(self):
        f = h5py.File(self.filename)
        dset = f['wired-dataset']
        self.data = np.zeros((1024,self.nsamples), dtype='uint16')
        pbar = ProgressBar(maxval=self.nsamples-1).start()
        for i in range(self.nsamples):
            pbar.update(i)
            self.data[:,i] = dset[i][3][:1024]
        pbar.finish()

        for i in range(8):
            self.waveformList[i][0].set_data(self.xvalues, self.data[96+i,:])
        self.canvas.draw()

    def refresh(self):
        xmin = int(self.xRangeMin.text())
        xmax = int(self.xRangeMax.text())
        ymin = int(self.yRangeMin.text())
        ymax = int(self.yRangeMax.text())
        for axes in self.axesList:
            axes.axis([xmin, xmax, ymin, ymax], fontsize=10)
        self.canvas.draw()

    def returnState(self):
        pass

    def closeEvent(self, event):
        print 'closing'

