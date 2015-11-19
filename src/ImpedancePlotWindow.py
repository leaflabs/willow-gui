#!/usr/bin/python

import sys, time
from PyQt4 import QtGui
import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import h5py

class ImpedancePlotWindow(QtGui.QWidget):

    def __init__(self, data):
        QtGui.QWidget.__init__(self)
        self.data = data

        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.createPlot()

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)
        self.resize(1200,600)
        self.setWindowTitle('Impedance Plot Window')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.center()

    def createPlot(self):
        self.axes = self.fig.add_subplot(111)
        self.axes.set_axis_bgcolor('k')
        self.axes.semilogy(self.data, color='#8fdb90', linestyle='', marker='D')
        self.axes.set_title('Impedance at 1 kHz')
        self.axes.set_xlabel('Channel Number')
        self.axes.set_ylabel('Z (ohms)')
        self.axes.set_xlim([0,1023])
        self.axes.tick_params(axis='both', which='both', direction='out', width=1.5)
        self.axes.tick_params(axis='both', which='major', length=8) 
        self.axes.tick_params(axis='both', which='minor', length=4) 

    def center(self):
        fmgeo = self.frameGeometry()
        currentScreen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
        centerPoint = QtGui.QApplication.desktop().screenGeometry(currentScreen).center()
        fmgeo.moveCenter(centerPoint)
        self.move(fmgeo.topLeft())

if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    filename = str(QtGui.QFileDialog.getOpenFileName(None, 'Select Impedance File', '../cal'))
    if filename:
        f = h5py.File(filename)
        dset = f['impedanceMeasurements']
        impedanceMeasurements = dset[:]
        impedancePlotWindow = ImpedancePlotWindow(impedanceMeasurements)
        impedancePlotWindow.show()
    app.exec_()
