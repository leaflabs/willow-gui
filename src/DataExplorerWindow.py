#!/usr/bin/python

from PyQt4 import QtCore, QtGui

import numpy as np

from PlotMatrix import PlotMatrix
from HeatMap import HeatMap
from TimeScrubber import TimeScrubber

from WillowDataset import WillowDataset

class DataExplorerWindow(QtGui.QWidget):

    def __init__(self, filename):
        QtGui.QWidget.__init__(self)

        self.dataset = WillowDataset(filename, -1)

        # widgets
        self.heatMap = HeatMap(32, 32)
        if self.dataset.nsamples > 300000:
            initRange = [0,30000]
        else:
            initRange = [0,self.dataset.nsamples/10]
        self.timeScrubber = TimeScrubber(self.dataset.nsamples, initRange=initRange)
        self.plotMatrix = PlotMatrix(4, 2)
        self.plotMatrix.setAllTitles('willowChan = xxxx')

        # layout
        topLayout = QtGui.QHBoxLayout()
        topLayout.addWidget(self.heatMap)
        topLayout.addWidget(self.timeScrubber)
        layout = QtGui.QVBoxLayout()
        layout.addLayout(topLayout)
        layout.addWidget(self.plotMatrix)
        self.setLayout(layout)

        # window and margin settings
        self.setWindowTitle('Willow Data Explorer')
        self.resize(1400,800)

        self.timeScrubber.timeRangeSelected.connect(self.handleTimeSelection)
        self.heatMap.dragAndDropAccepted.connect(self.handleChanSelection)

        # this is used to keep track of which channels (if any) are on which subplots
        self.chanLedger = {}
        for i in range(8):
            self.chanLedger[i] = None

        self.filtered = False

        self.timeScrubber.bang()

    def handleTimeSelection(self, start, stop):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.dataset.importSlice(start,stop)
        self.dataset.filterAndCalculateActivitySlice()
        self.heatMap.setActivity(self.dataset.slice_activity.reshape((32,32), order='C'))
        self.plotMatrix.setXRange(0, self.dataset.slice_nsamples/30.)
        if self.filtered:
            self.plotMatrix.setYRange(self.dataset.slice_min, self.dataset.slice_max)
        else:
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
