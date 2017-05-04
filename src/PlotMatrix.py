#!/usr/bin/env python

from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
pg.setConfigOptions(antialias=True)

import numpy as np

class DragPlotItem(pg.PlotItem):

    def __init__(self, subplotIndex, *args, **kwargs):
        pg.PlotItem.__init__(self, *args, **kwargs)

        self.subplotIndex = subplotIndex

        # install event filter for viewbox and axes items
        self.vb.installEventFilter(self)
        for axesDict in self.axes.values():
            axesDict['item'].installEventFilter(self)

        self.setAcceptDrops(True)

    def setData(self, x, y):
        if self.curves:
            self.curves[0].setData(x=x, y=y)
        else:
            self.plot(x=x, y=y)

    def eventFilter(self, target, ev):
        if ev.type() == QtCore.QEvent.GraphicsSceneWheel:
            if ev.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                self.axes['left']['item'].wheelEvent(ev)
            else:
                self.axes['bottom']['item'].wheelEvent(ev)
            return True
        return False

    def dragEnterEvent(self, event):
        for axesDict in self.axes.values():
            axesDict['item'].setPen(255,0,255) # leaflabs green

    def dragLeaveEvent(self, event):
        for axesDict in self.axes.values():
            axesDict['item'].setPen('w')

    def dropEvent(self, event):
        event.mimeData().setText(str(self.subplotIndex))
        for axesDict in self.axes.values():
            axesDict['item'].setPen('w')
        event.accept()

class PlotMatrix(pg.GraphicsLayoutWidget):

    def __init__(self, nrows, ncols):
        pg.GraphicsLayoutWidget.__init__(self)

        self.nrows = nrows
        self.ncols = ncols

        self.createPlotItems()

    def createPlotItems(self):
        self.plotItems = []
        for subplotIndex in range(self.nrows * self.ncols):
            plotItem = DragPlotItem(subplotIndex)
            plotItem.hideButtons()
            plotItem.showGrid(x=True, y=True, alpha=.25)
            if subplotIndex > 0: # link them in a daisy-chain topology
                plotItem.setXLink(self.plotItems[subplotIndex-1])
                plotItem.setYLink(self.plotItems[subplotIndex-1])
            self.addItem(plotItem)
            self.plotItems.append(plotItem)
            if subplotIndex % 2 == 1:
                self.nextRow()

    def setPlotData(self, subplotIndex, x, y):
        plotItem = self.plotItems[subplotIndex]
        plotItem.setData(x, y)

    def setPlotTitle(self, subplotIndex, title):
        plotItem = self.plotItems[subplotIndex]
        plotItem.setTitle(title=title)

    def setAllTitles(self, title):
        for plotItem in self.plotItems:
            plotItem.setTitle(title=title)

    def setXRange(self, xmin, xmax):
        for plotItem in self.plotItems:
            plotItem.setLimits(xMin=xmin, xMax=xmax)
            plotItem.setXRange(xmin, xmax, update=True)

    def setYRange(self, ymin, ymax):
        for plotItem in self.plotItems:
            plotItem.setLimits(yMin=ymin, yMax=ymax)
            plotItem.setYRange(ymin, ymax, update=True)

    def home(self):
        for plotItem in self.plotItems:
            plotItem.autoRange()

    def dragEnterEvent(self, event):
        event.accept()


if __name__ =="__main__":
    nrows = 4
    ncols = 2
    nsamples = 30000
    import sys
    from random import random
    app = QtGui.QApplication(sys.argv)
    plotMatrix = PlotMatrix(nrows,ncols)
    x = np.arange(nsamples)
    for i in range(nrows*ncols):
        plotMatrix.setPlotData(i, x, [random() for j in range(nsamples)])
    plotMatrix.show()
    sys.exit(app.exec_())
