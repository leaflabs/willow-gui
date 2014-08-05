from PyQt4 import QtCore, QtGui
import subprocess, h5py, os, sys
import numpy as np
from progressbar import ProgressBar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from parameters import DAEMON_DIR, DATA_DIR

sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

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

        self.nsampLine = QtGui.QLineEdit()
        self.dirLine = QtGui.QLineEdit(DATA_DIR)
        self.filenameLine = QtGui.QLineEdit()
        self.transferButton = QtGui.QPushButton('Transfer Data')
        self.transferButton.clicked.connect(self.transferData)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel('Number of Samples (blank indicates entire experiment):'))
        self.layout.addWidget(self.nsampLine)
        self.layout.addWidget(QtGui.QLabel('Directory:'))
        self.layout.addWidget(self.dirLine)
        self.layout.addWidget(QtGui.QLabel('Filename:'))
        self.layout.addWidget(self.filenameLine)
        self.layout.addWidget(self.transferButton)
        self.setLayout(self.layout)

    def transferData(self):
        if self.parent.isDaemonRunning:
            filename = os.path.join(str(self.dirLine.text()), str(self.filenameLine.text()))
            nsamples_text = self.nsampLine.text()
            if isBlank(nsamples_text):
                nsamples = None
            else:
                nsamples = int(nsamples_text)
            self.parent.statusBox.append('Transferring...')
            # old
            """
            status1 = subprocess.call([self.acquireDotPy, 'start'])
            status2 = subprocess.call([self.acquireDotPy, 'save_stream', filename, nsamp])
            status3 = subprocess.call([self.acquireDotPy, 'stop'])
            if (status1==1 or status2==1 or status3==1):
                self.parent.statusBox.append('Error')
            else:
                self.parent.statusBox.append('Saved '+nsamp+' samples to: '+filename)
                self.mostRecentFilename = filename
            """
            # new
            cmd = ControlCommand(type=ControlCommand.STORE)
            cmd.store.start_sample = 0
            if nsamples:
                cmd.store.nsamples = nsamples
            # (else leave missing which indicates whole experiment)
            cmd.store.path = filename
            resp = do_control_cmd(cmd)
            self.parent.statusBox.append('Transfer Complete')
        else:
            self.parent.statusBox.append('Daemon is not running.')

    def plotFromFile(self, filename):
        f = h5py.File(filename)
        dset = f['wired-dataset'] # each element is this convoluted tuple
        ns = len(dset)  # number of samples
        data = np.zeros((1024,ns), dtype='uint16')      # 1024 channels at 30 kHz
        pbar = ProgressBar(maxval=ns-1).start()
        self.parent.statusBox.append('Reading in data from '+filename)
        print 'Reading in data from '+filename
        for i in range(ns):
            pbar.update(i)
            data[:,i] = dset[i][3][:1024]
        pbar.finish()
        self.parent.statusBox.append('Done.')
        bank = 3
        self.parent.statusBox.append('Plotting multi-channel data...')
        newFig = Figure((5.,4.), dpi=100)
        self.parent.fig.clear()
        for i in range(32):
            ax = self.parent.fig.add_subplot(8,4,i+1)
            ax.set_axis_bgcolor('k')
            ax.plot(data[bank*32+i,:], color='y')
            ax.set_ylim([0,2**16-1])
            ax.xaxis.set_ticklabels([]) # this makes the axes text invisible (but not the ticks themselves)
            ax.yaxis.set_ticklabels([]) # this makes the axes text invisible (but not the ticks themselves)
        self.parent.fig.subplots_adjust(left=0.,bottom=0.,right=1.,top=1., wspace=0.04, hspace=0.1)
        self.parent.canvas.draw()
        self.parent.statusBox.append('Done.')

    def plotRecent(self):
        if self.mostRecentFilename:
            self.plotFromFile(self.mostRecentFilename)
        else:
            self.parent.statusBox.append('Nothing recorded yet.')

    def plotSpecific(self):
        datadir = str(self.dirLine.text())
        specificFilename = str(self.specificLine.text())
        filename = os.path.join(datadir, specificFilename)
        if specificFilename:
            if os.path.exists(filename):
                self.plotFromFile(filename)
            else:
                self.parent.statusBox.append('File does not exist: '+filename)
        else:
            self.parent.statusBox.append('Please enter filename to plot.')
