#!/usr/bin/env python2

import sys, time, os
from PyQt4 import QtGui
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
        self.fileObject = h5py.File(filename)
        self.data = self.fileObject['impedanceMeasurements'][:]

        self.plot(np.arange(NCHAN), self.data, pen=None, symbol='o')
        self.setLogMode(y=True)
        self.setLimits(xMin=0, xMax=NCHAN, yMin=0, yMax=np.log10(np.max(self.data))+1)
        self.setLabel('bottom', text='Willow Channel Number')
        self.setLabel('left', text='Impedance (Ohms)')
        self.setTitle(os.path.basename(self.filename))
        # iterate through all axesItems, and set their ticklength to the file-global value
        for axesDict in self.plotItem.axes.values():
            axesDict['item'].setStyle(tickLength=TICKLENGTH)

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


if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    import config
    config.updateAttributes(config.loadJSON())
    filename = str(QtGui.QFileDialog.getOpenFileName(None, 'Select Impedance File', config.dataDir))
    if filename:
        impedancePlotWindow = ImpedancePlotWindow(filename)
        impedancePlotWindow.show()
        app.exec_()
