#!/usr/bin/env python2

import sys
from PyQt4 import QtGui, QtCore
import numpy as np

from viridis import viridis as cmap


class HeatMap(QtGui.QLabel):

    dragAndDropAccepted = QtCore.pyqtSignal(int, int, str)

    def __init__(self, nrows, ncols, tileSize_init=10):
        """
        nrows: number of rows
        ncols: number of columns
        tileSize_init: initial side length of the square tiles (subject to
            resize events in future versions, but locked to a square shape
            for now)
        """
        QtGui.QLabel.__init__(self)

        self.nrows = nrows
        self.ncols = ncols

        self.activity = np.zeros((self.nrows, self.ncols))

        self.setMinimumSize(tileSize_init*self.ncols,tileSize_init*self.nrows)
        self.setMaximumSize(tileSize_init*self.ncols, tileSize_init*self.nrows)

        self.hold = False
        self.setMouseTracking(True)

    def setActivity(self, activity):
        """
        activity should be a (nrows,ncols) ndarray with values from 0 to 1
        values outside this range will saturate the colormap
        """
        self.activity = activity
        self.repaint()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        pen = painter.pen()
        pen.setStyle(QtCore.Qt.NoPen)
        painter.setPen(pen)

        for i in range(self.nrows):
            for j in range(self.ncols):
                x = j*self.rectw
                y = i*self.recth
                brush = QtGui.QBrush(QtGui.QColor(*tuple(cmap(self.activity[i,j]))))
                painter.setBrush(brush)
                pen = QtGui.QPen(QtGui.QColor(0,0,0), 1)
                painter.setPen(pen)
                painter.drawRect(x,y, self.rectw,self.recth)

    def resizeEvent(self, event):
        self.rectw = event.size().width() // self.ncols
        self.recth = event.size().height() // self.nrows

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.hold = True
            self.iselected = event.pos().x() // self.rectw
            self.jselected = event.pos().y() // self.recth

    def mouseMoveEvent(self, event):
        chip = event.pos().x() // self.rectw
        chan = event.pos().y() // self.recth
        pt = self.mapToGlobal(QtCore.QPoint(event.pos().x(), event.pos().y()))
        QtGui.QToolTip.showText(pt, 'chip: %d, chan: %d' % (chip, chan))
        if self.hold:
            mimeData = QtCore.QMimeData()
            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            dropAction = drag.exec_()
            if dropAction == QtCore.Qt.MoveAction:
                dropText = str(drag.mimeData().text())
                self.dragAndDropAccepted.emit(self.iselected, self.jselected, dropText)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.hold = False

if __name__ == '__main__':
    # demo with random activity values
    nrows, ncols = 16, 32
    tileSize_init = 20
    import random
    app = QtGui.QApplication(sys.argv)
    heatMap = HeatMap(nrows, ncols, tileSize_init)
    activity = np.array([random.random() for i in range(nrows*ncols)]).reshape(nrows,ncols)
    heatMap.setActivity(activity)
    heatMap.show()
    sys.exit(app.exec_())
