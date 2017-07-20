#!/usr/bin/env python2

import sys, time, os
from PyQt4 import QtCore, QtGui
import numpy as np
import h5py
import pyqtgraph as pg

from WillowDataset import NCHAN

TICKLENGTH = -10
INITWIDTH = 1200
INITHEIGHT = 600

class ImpedancePlotWindow(pg.PlotWidget):

    def __init__(self, filename):
        pg.PlotWidget.__init__(self)

        self.filename = filename
        self.fileObject = h5py.File(filename, 'r')
        self.data = self.fileObject['impedanceMeasurements'][:]

        pt_xs = np.arange(NCHAN)
        # plot points, setting 'data' attribute of each to channel, kOhm pairs
        self.points = self.plot(pt_xs, self.data, pen=None, symbol='o',
                                data=zip(pt_xs, self.data/1000.))
        self.points.sigPointsClicked.connect(self.pointClicked)

        self.info = pg.TextItem('', color=(255,255,255,255),
                                fill=(127,127,127,127))
        self.info.hide()
        self.addItem(self.info)

        self.setLogMode(y=True)
        self.setLimits(xMin=0, xMax=NCHAN, yMin=0, yMax=np.log10(np.max(self.data))+1)
        self.setLabel('bottom', text='Willow Channel Number')
        self.setLabel('left', text='Impedance (Ohms)')
        self.setTitle(os.path.basename(self.filename))
        # set axes tick lengths and install event filter on them for zooming
        for axesDict in self.plotItem.axes.values():
            axesDict['item'].setStyle(tickLength=TICKLENGTH)
            axesDict['item'].installEventFilter(self)
        # install event filter for zooming on viewbox also
        self.plotItem.vb.installEventFilter(self)

        self.resize(INITWIDTH,INITHEIGHT)
        self.setWindowTitle('Impedance Plot Window')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.center()

    def center(self):
        fmgeo = self.frameGeometry()
        currentScreen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
        centerPoint = QtGui.QApplication.desktop().screenGeometry(currentScreen).center()
        fmgeo.moveCenter(centerPoint)
        self.move(fmgeo.topLeft())

    def pointClicked(self, item, pts):
        pt_text = u'Channel {0}: Impedance = {1:.2f} k\N{OHM SIGN}'
        get_vals = pg.graphicsItems.ScatterPlotItem.SpotItem.data
        self.info.setText('\n'.join(pt_text.format(*i) for i in map(get_vals, pts)))
        self.info.setPos(pts[0].pos())
        self.info.show()

    def eventFilter(self, target, ev):
        if ev.type() == QtCore.QEvent.GraphicsSceneWheel:
            if ev.modifiers():
                if ev.modifiers() & QtCore.Qt.ControlModifier:
                    self.plotItem.axes['bottom']['item'].wheelEvent(ev)
                if ev.modifiers() & QtCore.Qt.ShiftModifier:
                    self.plotItem.axes['left']['item'].wheelEvent(ev)
            else:
                self.plotItem.axes['bottom']['item'].wheelEvent(ev)
                self.plotItem.axes['left']['item'].wheelEvent(ev)
            return True
        return False


if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    import config
    config.updateAttributes(config.loadJSON())
    filename = str(QtGui.QFileDialog.getOpenFileName(None, 'Select Impedance File', config.dataDir))
    if filename:
        impedancePlotWindow = ImpedancePlotWindow(filename)
        impedancePlotWindow.show()
        app.exec_()
