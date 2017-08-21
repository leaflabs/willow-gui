#!/usr/bin/env python2

from PyQt4 import QtCore, QtGui

import numpy as np

from PlotMatrix import PlotMatrix
from HeatMap import HeatMap
from TimeScrubber import TimeScrubber

from WillowDataset import WillowDataset, SAMPLE_RATE

DEFAULT_TIME_SPAN = 3       # seconds

class HelpWindow(QtGui.QDialog):
    def __init__(self, *args, **kwargs):
        QtGui.QDialog.__init__(self, *args, **kwargs)

        self.setWindowTitle('DataExplorer Help')

        help_texts = []

        help_texts.append(QtGui.QLabel('The WillowGUI Data Explorer allows inspection of snapshot or experiment\n'
            'data recorded with a Willow. The colorful heat map in the upper-left corner is\n'
            'filled with squares which represent the 32 different ADC chips connected to the\n'
            'Willow during the recording, and each of their 32 individual recording channels.\n'
            'To inspect one of these channels more closely, click on a colored square and drag\n'
            'into one of the eight graphs in the bottom part of the GUI. You can adjust the\n'
            'length of time inspected with the time scrubber on the top left.\n\n'))
        help_texts.append(QtGui.QLabel('Keyboard shortcuts:\n'))
        font = QtGui.QFont()
        font.setBold(True)
        help_texts[-1].setFont(font)
        help_texts.append(QtGui.QLabel('F1 - launch this help menu\n'
            'F - toggles filtering of displayed data\n'
            'F11 - toggle fullscreen viewing of the Data Explorer\n'
            'Home - reset viewing range of the eight plots on the bottom\n'
            'Scrollwheel - zoom x and y dimensions of plots\n'
            'Ctrl+Scrollwheel - zoom only x dimension of plots\n'
            'Shift+Scrollwheel - zoom only y dimension of plots\n'))
        layout = QtGui.QVBoxLayout()
        for help_text in help_texts:
            layout.addWidget(help_text)
        self.setLayout(layout)


class DataExplorerWindow(QtGui.QWidget):

    def __init__(self, filename):
        QtGui.QWidget.__init__(self)

        self.dataset = WillowDataset(filename)

        # widgets
        self.heatMap = HeatMap(32, 32)
        if self.dataset.nsamples < DEFAULT_TIME_SPAN * SAMPLE_RATE:
            self.initRange = [0,self.dataset.nsamples]
        else:
            initRange = [0,DEFAULT_TIME_SPAN * SAMPLE_RATE]
        self.timeScrubber = TimeScrubber(self.dataset.nsamples, initRange=initRange)
        self.plotMatrix = PlotMatrix(4, 2)
        self.plotMatrix.setAllTitles('willowChan = xxxx')
        self.plotMatrix.setAllLabels(b_text='time', b_units='s',
                                     l_text='voltage', l_units='V')
        # time units in milliseconds; voltage units in microvolts:
        self.plotMatrix.setAllScales(b_scale=1/1000., l_scale=1/1000000.)

        # layout
        topLayout = QtGui.QHBoxLayout()
        topLayout.addWidget(self.heatMap)
        topLayout.addWidget(self.timeScrubber)
        layout = QtGui.QVBoxLayout()
        layout.addLayout(topLayout)
        layout.addWidget(self.plotMatrix)
        self.setLayout(layout)

        # window and margin settings
        self.setWindowTitle('Willow Data Explorer (%s)' % filename)
        self.resize(1400,800)

        self.timeScrubber.timeRangeSelected.connect(self.handleTimeSelection)
        self.heatMap.dragAndDropAccepted.connect(self.handleChanSelection)

        # this is used to keep track of which channels (if any) are on which subplots
        self.chanLedger = {}
        for i in range(8):
            self.chanLedger[i] = None

        self.filtered = False

        self.helpWindow = HelpWindow(parent=self)

        self.timeScrubber.bang()

    def handleTimeSelection(self, start, stop):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.dataset.importSlice(start,stop)
        self.dataset.filterAndCalculateActivitySlice()
        self.heatMap.setActivity(self.dataset.slice_activity.reshape((32,32), order='F'))
        self.plotMatrix.setXRange(0, self.dataset.slice_nsamples/30.)
        self.plotMatrix.setYRange(self.dataset.slice_min, self.dataset.slice_max)
        self.updateAllPlots()
        QtGui.QApplication.restoreOverrideCursor()

    def handleChanSelection(self, chip, chan, text):
        if text:
            subplotIndex = int(text)
            willowChan = chip*32 + chan
            self.setPlotChan(subplotIndex, willowChan)
            self.chanLedger[subplotIndex] = willowChan

    def setPlotChan(self, subplotIndex, willowChan):
        x = np.arange(self.dataset.slice_nsamples)/30.
        if self.filtered:
            y = self.dataset.slice_filtered[willowChan,:]
        else:
            y = self.dataset.slice_uv[willowChan,:]
        self.plotMatrix.setPlotData(subplotIndex, x, y)
        self.plotMatrix.setPlotTitle(subplotIndex, 'willowChan = %.4d' % willowChan)

    def updateAllPlots(self):
        """
        call this after updating the time slice, or filtered state.
        to set a single plot's channel use setPlotChan instead
        """
        for subplotIndex, willowChan in self.chanLedger.items():
            if willowChan:
                self.setPlotChan(subplotIndex, willowChan)

    def showHelp(self):
        if self.helpWindow.isHidden():
            self.helpWindow.setGeometry(QtCore.QRect(100,100,500,250))
            self.helpWindow.show()
        else:
            # focus window which is already somewhere on desktop
            self.helpWindow.setWindowState(self.helpWindow.windowState() &
                ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        self.helpWindow.activateWindow()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F11:
            if self.windowState() & QtCore.Qt.WindowFullScreen:
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.key() == QtCore.Qt.Key_Escape:
                self.showNormal()
        elif event.key() == QtCore.Qt.Key_F:
            self.filtered = not self.filtered
            self.updateAllPlots()
        elif event.key() == QtCore.Qt.Key_Home:
            self.plotMatrix.home()
        elif event.key() == QtCore.Qt.Key_F1:
            self.showHelp()

if __name__=='__main__':
    import sys
    if len(sys.argv)>1:
        filename = sys.argv[1]
    else:
        print 'Usage: $ ./main <filename.h5>'
        sys.exit(1)
    app = QtGui.QApplication(sys.argv)
    dataExplorerWindow = DataExplorerWindow(filename)
    dataExplorerWindow.show()
    sys.exit(app.exec_())
