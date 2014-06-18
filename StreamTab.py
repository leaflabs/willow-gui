from PyQt4 import QtCore, QtGui
import subprocess
import numpy as np

from parameters import *

class StreamTab(QtGui.QWidget):

    def __init__(self, parent):
        super(StreamTab, self).__init__(None)
        self.parent = parent

        self.chipNumLine = QtGui.QLineEdit('3')
        self.channelNumLine = QtGui.QLineEdit('3')

        self.standbyCheckbox = QtGui.QCheckBox('Standby')
        self.standbyCheckbox.clicked.connect(self.toggleStandby)

        self.streamCheckbox = QtGui.QCheckBox('Stream')
        self.streamCheckbox.stateChanged.connect(self.toggleStream)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel('Chip Number:'))
        self.layout.addWidget(self.chipNumLine)
        self.layout.addWidget(QtGui.QLabel('Channel Number:'))
        self.layout.addWidget(self.channelNumLine)
        self.layout.addSpacing(100)
        self.layout.addWidget(self.standbyCheckbox)
        self.layout.addWidget(self.streamCheckbox)
        self.setLayout(self.layout)

        # stream buffers, etc.
        sr = 30000  # sample rate
        fr = 30      # frame rate
        self.fp = 1000//fr  # frame period
        n = 30000   # number of samples to display
        self.nrefresh = sr//fr   # new samples collected before refresh
        self.xvalues = np.arange(n, dtype='int')
        self.plotBuff = np.zeros(n, dtype='uint16')
        self.newBuff = np.zeros(self.nrefresh, dtype='uint16')

        # timer stuff
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updatePlot)

    def toggleStandby(self):
        """
        Decided to separate out standby mode because the setup is kind of slow (~5 seconds)
        and you probably only want to do this occasionally, while starting/stopping the stream
        you would do more frequently, without having to wait.
        """
        if self.parent.isDaemonRunning:
            if self.standbyCheckbox.isChecked():
                subprocess.call([DAEMON_DIR+'util/acquire.py', 'subsamples', '--constant', 'chip', self.chipNumLine.text()])
                subprocess.call([DAEMON_DIR+'util/acquire.py', 'start'])
                subprocess.call([DAEMON_DIR+'util/acquire.py', 'forward', 'start', '-f', '-t', 'subsample'])
                self.parent.statusBox.setText('Standby mode activated')
            else:
                subprocess.call([DAEMON_DIR+'util/acquire.py', 'stop'])
                self.parent.statusBox.setText('Standby mode de-activated')
        else:
            #TODO gray-out the checkbox when the daemon is not running
            self.parent.statusBox.setText('Please start daemon first!')
            self.standbyCheckbox.setChecked(False)
                

    def toggleStream(self):
        """
        This works as long as the daemon was started externally,
        and the GUI was started with data piped in from proto2bytes:

        $ ~/sng/sng-daemon/build/proto2bytes -s -c 3 | ./wiredLeaf.py

        otherwise, this will crash the GUI.
        """
        if self.parent.isDaemonRunning:
            if self.streamCheckbox.isChecked():
                self.proto2bytes_po = subprocess.Popen([DAEMON_DIR+'build/proto2bytes', '-s', '-c', self.channelNumLine.text()], stdout=subprocess.PIPE)
                self.timer.start(self.fp)
                self.parent.statusBox.setText('Started streaming')
            else:
                self.timer.stop()
                self.proto2bytes_po.kill()
                self.parent.statusBox.setText('Stopped streaming')
        else:
            #TODO gray-out the checkbox when the daemon is not running
            self.parent.statusBox.setText('Please start daemon first!')
            self.streamCheckbox.setChecked(False)



    def updatePlot(self):
        for i in range(self.nrefresh):
            self.newBuff[i] = self.proto2bytes_po.stdout.readline()
        self.plotBuff = np.concatenate((self.plotBuff[self.nrefresh:],self.newBuff))
        self.parent.waveform[0].set_data(self.xvalues, self.plotBuff)
        self.parent.canvas.draw()

