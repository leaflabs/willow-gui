from PyQt4 import QtCore, QtGui
import subprocess, h5py, os, sys, socket
import numpy as np
from progressbar import ProgressBar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from binarySearch import getExperimentCookie, findExperimentBoundary_pbar
from ProgressBarWindow import ProgressBarWindow

from parameters import DAEMON_DIR, DATA_DIR

sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

import CustomExceptions as ex
import hwif

def isBlank(string):
    if len(string)==0:
        return True
    elif string[0]==' ':
        return isBlank(string[1:])
    else:
        return False

class TransferTab(QtGui.QWidget):

    def __init__(self, parent):
        super(TransferTab, self).__init__(None)
        self.parent = parent

        self.description = QtGui.QLabel(
            "<i>Transfer an experiment from the datanode's disk to your filesystem.</i>")

        self.binarySearchButton = QtGui.QPushButton('Determine Length of Experiment on Disk')
        self.binarySearchButton.clicked.connect(self.binarySearch)

        self.bsResultLabel = QtGui.QLabel('(click above for experiment length)')

        self.nsampLine = QtGui.QLineEdit()

        self.filenameBrowseWidget = self.FilenameBrowseWidget(self)

        self.transferButton = QtGui.QPushButton('Transfer Data')
        self.transferButton.clicked.connect(self.transferData)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addSpacing(20)
        self.layout.addWidget(self.description)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.binarySearchButton)
        self.layout.addWidget(self.bsResultLabel)
        self.layout.addSpacing(20)
        self.layout.addWidget(QtGui.QLabel('Number of Samples (blank indicates entire experiment):'))
        self.layout.addWidget(self.nsampLine)
        self.layout.addWidget(QtGui.QLabel('Filename:'))
        self.layout.addWidget(self.filenameBrowseWidget)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.transferButton)
        self.layout.addWidget(QtGui.QLabel('Note: GUI will be unvailable until transfer is complete'))
        self.setLayout(self.layout)

    def binarySearch(self):
        try:
            progressBarWindow = ProgressBarWindow(26, 'Analyzing disk for experiment length...')
            progressBarWindow.show()
            cookie = getExperimentCookie(0)
            boundary = findExperimentBoundary_pbar(cookie, 0, int(125e6), progressBarWindow.progressBar, 0)
            if boundary>0:
                self.bsResultLabel.setText('Experiment on disk is %d samples, '
                                            'or %5.2f minutes worth of data.\n'
                                            'Experiment cookie is %d' % (boundary, boundary/1.8e6, cookie))
        except socket.error:
            self.parent.statusBox.append('Socket error: Could not connect to daemon')
        except DaemonControlError:
            self.parent.statusBox.append('Daemon control error.')

    class FilenameBrowseWidget(QtGui.QWidget):

        def __init__(self, parent):
            super(parent.FilenameBrowseWidget, self).__init__()
            self.filenameLine = QtGui.QLineEdit()
            self.browseButton = QtGui.QPushButton('Browse')
            self.browseButton.clicked.connect(self.browse)
            self.layout = QtGui.QHBoxLayout()
            self.layout.addWidget(self.filenameLine)
            self.layout.addWidget(self.browseButton)
            self.setLayout(self.layout)

        def browse(self):
            filename = QtGui.QFileDialog.getSaveFileName(self, 'Save To...', DATA_DIR)
            self.filenameLine.setText(filename)

    def transferData(self):
        filename = str(self.filenameBrowseWidget.filenameLine.text())
        nsamples_text = str(self.nsampLine.text())
        if isBlank(nsamples_text):
            nsamples = None
        else:
            nsamples = int(nsamples_text)
        try:
            hwif.doTransfer(nsamples, filename)
            self.parent.statusBox.append('Transfer Complete: %s' % filename)
        except ex.StateChangeError:
            self.parent.statusBox.append('Cannot do transfer while recording or streaming (temporary).')
        except socket.error:
            self.parent.statusBox.append('Socket error: Could not connect to daemon.')
        except tuple(ex.ERROR_DICT.values()) as e:
            self.parent.statusBox.append('Error: %s' % e)

