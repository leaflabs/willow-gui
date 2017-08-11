#!/usr/bin/env python2

from PyQt4 import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from willowephys import SAMPLE_RATE

class TimeScrubber(QtGui.QLabel):

    timeRangeSelected= QtCore.pyqtSignal(int, int)

    def __init__(self, nsamples, initRange=[0,30000], maxNSamples=90000):
        QtGui.QLabel.__init__(self)

        self.nsamples = nsamples
        self.time_total = nsamples/SAMPLE_RATE  # in seconds

        # some drawing parameters
        self.margin = 40
        self.tickLength = 30
        self.pen_timeline = QtGui.QPen(QtGui.QColor('gray'))
        self.brush_scrubber = QtGui.QBrush(QtGui.QColor(200, 200, 200, 64))
        self.pen_scrubber = QtGui.QPen()
        self.pen_scrubber.setStyle(QtCore.Qt.NoPen)

        # widget properties
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.setStyleSheet('background-color: #0F0F0F')
        self.setMouseTracking(True)

        # mouse state variables
        self.edgeDetect = 0
        self.edgeDetectMargin = 3
        self.centerHold = 0
        self.leftHold = 0
        self.rightHold = 0

        # scrubber state variables: to preserve state across resizings, it makes
        #   sense to track state as sample indices rather than pixels. however,
        #   we can set them from pixel values using setStateLeft(), setStateRight(),
        #   and setStateCenter(). these functions also implement limit-checking.
        self.totalsamp = maxNSamples
        if (initRange[1] - initRange[0]) > maxNSamples:
            raise ValueError("Exceeding maximum number of samples to represent! initRange must be less than maxSamples!!")
        self.minsamp = initRange[0]
        self.maxsamp = initRange[1]

        [timespan, suffix] = pg.siFormat(self.time_total, suffix='s').split(' ')

        self.leftLabel = QtGui.QLabel('sample 0 \n (0 %s)' % suffix)
        self.rightLabel = QtGui.QLabel('sample %d' % self.nsamples + \
                                       '\n (%s %s)' % (timespan, suffix))
        for label in [self.leftLabel, self.rightLabel]:
            label.setStyleSheet('color:gray; background:transparent')
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setParent(self)
            label.show()

    def setStateLeft(self, pix):
        samp = self._pix2samp(pix)
        upperbound = self.maxsamp - self._dpix2dsamp(2*self.edgeDetectMargin)
        if (samp >= 0) and (samp < upperbound) and (samp > (self.maxsamp - self.totalsamp)):
            self.minsamp = self._pix2samp(pix)
        else:
            self.minsamp = self._pix2samp(self._samp2pix(0))

    def setStateRight(self, pix):
        samp = self._pix2samp(pix)
        lowerbound = self.minsamp + self._dpix2dsamp(2*self.edgeDetectMargin)
        if (samp >= lowerbound) and (samp < self.nsamples) and (samp < (self.minsamp + self.totalsamp)):
            self.maxsamp = self._pix2samp(pix)
        else:
            self.maxsamp = self._pix2samp(self._samp2pix(self.nsamples))

    def setStateCenter(self, pix):
        delta = self.maxsamp - self.minsamp
        mid = self._pix2samp(pix)
        minsamp = int(mid - delta/2.)
        maxsamp = int(mid + delta/2.)
        if (minsamp < 0):
            minsamp = 0
            maxsamp = minsamp + delta
        elif (maxsamp >= self.nsamples):
            maxsamp = self.nsamples
            minsamp = maxsamp - delta
        self.minsamp = minsamp
        self.maxsamp = maxsamp

    def bang(self):
        """
        send the current state via signal, like 'bang' in Pd/Max
        """
        self.timeRangeSelected.emit(self.minsamp, self.maxsamp)

    def _samp2pix(self, samp):
        w = self.size().width()
        pix = self.margin + samp * (w-2.*self.margin) / self.nsamples
        return int(pix)

    def _pix2samp(self, pix):
        w = self.size().width()
        samp = (pix - self.margin) * self.nsamples / (w - 2.*self.margin)
        return int(samp)

    def _dsamp2dpix(self, dsamp):
        w = self.size().width()
        return dsamp * (w - 2.*self.margin) / self.nsamples

    def _dpix2dsamp(self, dpix):
        w = self.size().width()
        return dpix * self.nsamples / (w - 2.*self.margin)

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)

        x1 = self.margin
        x2 = self.size().width() - self.margin
        y = self.size().height() / 2

        # draw time line and tick labels
        painter.setPen(self.pen_timeline)
        painter.drawLine(x1,y, x2,y)
        painter.drawLine(x1, y-self.tickLength/2, x1, y+self.tickLength/2)
        painter.drawLine(x2, y-self.tickLength/2, x2, y+self.tickLength/2)
        self.leftLabel.move(x1-self.leftLabel.width()/2, y+self.tickLength)
        self.rightLabel.move(x2-self.rightLabel.width()/2, y+self.tickLength)

        # draw the scrubber itself
        painter.setBrush(self.brush_scrubber)
        painter.setPen(self.pen_scrubber)
        self.scrubberLeft = self._samp2pix(self.minsamp)
        self.scrubberRight = self._samp2pix(self.maxsamp)
        self.scrubberTop = self.size().height() * 1./4
        self.scrubberBottom = self.size().height() * 3./4
        w = self.scrubberRight - self.scrubberLeft
        h = self.scrubberBottom - self.scrubberTop
        painter.drawRect(self.scrubberLeft, self.scrubberTop, w, h)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.edgeDetect == 0:
                self.centerHold = True
                self.setStateCenter(event.pos().x())
                self.repaint()
            elif self.edgeDetect == 1: # left
                self.leftHold = True
            elif self.edgeDetect == 2: # right
                self.rightHold = True

    def mouseMoveEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        if x < 0: x = 0
        if x > self.size().width() - 1: x = self.size().width() - 1
        if self.centerHold:
            self.setStateCenter(x)
            self.repaint()
        elif self.leftHold:
            self.setStateLeft(x)
            self.repaint()
        elif self.rightHold:
            self.setStateRight(x)
            self.repaint()
        else:
            if abs(x - self.scrubberLeft) < self.edgeDetectMargin:
                if (y > self.scrubberTop) and (y < self.scrubberBottom):
                    QtGui.QApplication.setOverrideCursor(QtCore.Qt.SizeHorCursor)
                    self.edgeDetect = 1 # left
            elif abs(x - self.scrubberRight) < self.edgeDetectMargin:
                if (y > self.scrubberTop) and (y < self.scrubberBottom):
                    QtGui.QApplication.setOverrideCursor(QtCore.Qt.SizeHorCursor)
                    self.edgeDetect = 2 # right
            else:
                QtGui.QApplication.restoreOverrideCursor()
                self.edgeDetect = 0 # none

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.timeRangeSelected.emit(self.minsamp, self.maxsamp)
            self.centerHold = False
            self.leftHold = False
            self.rightHold = False


if __name__ =="__main__":
    NSAMPLES = 300000   # 10 seconds
    INITRANGE = [0,30000] # first second
    WIDTH = 600
    HEIGHT = 200
    def callback(start, stop): print 'start = %d, stop = %d' % (start, stop)
    import sys
    app = QtGui.QApplication(sys.argv)
    nsamples = INITRANGE[1] - INITRANGE[0]
    widget = TimeScrubber(NSAMPLES, initRange=INITRANGE)
    widget.timeRangeSelected.connect(callback)
    widget.resize(600,200)
    widget.show()
    sys.exit(app.exec_())
