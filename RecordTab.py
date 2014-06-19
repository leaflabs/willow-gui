from PyQt4 import QtCore, QtGui
import subprocess, h5py
import numpy as np
from progressbar import ProgressBar
import matplotlib.pyplot as plt

from parameters import *

class RecordTab(QtGui.QWidget):

    def __init__(self, parent):
        super(RecordTab, self).__init__(None)
        self.parent = parent

        self.nsampLine = QtGui.QLineEdit('30000')
        self.dirLine = QtGui.QLineEdit('/home/chrono/sng/data')
        self.filenameLine = QtGui.QLineEdit()
        self.recordButton = QtGui.QPushButton('Record Data')
        self.recordButton.clicked.connect(self.recordData)
        self.plotButton = QtGui.QPushButton('Plot Most Recent')
        self.plotButton.clicked.connect(self.plotRecent)
        self.mostRecentFilename = None

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel('Number of Samples:'))
        self.layout.addWidget(self.nsampLine)
        self.layout.addWidget(QtGui.QLabel('Directory:'))
        self.layout.addWidget(self.dirLine)
        self.layout.addWidget(QtGui.QLabel('Filename:'))
        self.layout.addWidget(self.filenameLine)
        self.layout.addWidget(self.recordButton)
        self.layout.addWidget(self.plotButton)
        self.layout.addStretch(1)

        self.setLayout(self.layout)

    def recordData(self):
        if self.parent.isDaemonRunning:
            DATA_DIR = self.dirLine.text()
            if DATA_DIR[-1] != '/':
                DATA_DIR = DATA_DIR + '/'
            filename = self.filenameLine.text()
            nsamp = self.nsampLine.text()
            status1 = subprocess.call([DAEMON_DIR+'util/acquire.py', 'start'])
            status2 = subprocess.call([DAEMON_DIR+'util/acquire.py', 'save_stream', DATA_DIR+filename, nsamp])
            status3 = subprocess.call([DAEMON_DIR+'util/acquire.py', 'stop'])
            if (status1==1 or status2==1 or status3==1):
                self.parent.statusBox.setText('Error')
            else:
                self.parent.statusBox.setText('Saved '+nsamp+' samples to: '+DATA_DIR+filename)
                self.mostRecentFilename = DATA_DIR+filename
        else:
            self.parent.statusBox.setText('Please start daemon first!')

    def plotRecent(self):
        if self.mostRecentFilename:
            f = h5py.File(self.mostRecentFilename)
            dset = f['wired-dataset'] # each element is this convoluted tuple
            ns = len(dset)  # number of samples
            data = np.zeros((1024,ns), dtype='uint16')      # 1024 channels at 30 kHz
            pbar = ProgressBar(maxval=ns-1).start()
            print 'reading in data...'
            for i in range(ns):
                pbar.update(i)
                data[:,i] = dset[i][3][:1024]
            pbar.finish()
            plt.figure(figsize=(12,16))
            for i in range(32):
                ax = plt.subplot(8,4,i+1)
                ax.set_axis_bgcolor('k')
                ax.plot(data[bank*32+i,:], color='y')
                ax.set_ylim([0,2**16-1])
            plt.show()
        else:
            self.parent.statusBox.setText('Nothing recorded yet.')


