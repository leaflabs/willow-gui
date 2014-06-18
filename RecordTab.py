from PyQt4 import QtCore, QtGui
import subprocess

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
        self.parent.statusBox.setText('This does nothing yet')


