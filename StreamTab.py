from PyQt4 import QtCore, QtGui
import subprocess
import numpy as np

from parameters import DAEMON_DIR, DATA_DIR

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
        self.layout.addSpacing(200)
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

        self.standingBy = False

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
                self.parent.statusBox.append('Standby mode activated')
                self.standingBy = True
            else:
                subprocess.call([DAEMON_DIR+'util/acquire.py', 'stop'])
                self.parent.statusBox.append('Standby mode de-activated')
                self.standingBy = False
        else:
            #TODO gray-out the checkbox when the daemon is not running
            self.parent.statusBox.append('Please start daemon first!')
            self.standbyCheckbox.setChecked(False)
                

    def toggleStream(self):
        if (self.parent.isDaemonRunning and self.standingBy):
            if self.streamCheckbox.isChecked():
                # matplotlib stuff
                self.parent.fig.clear()
                self.parent.axes = self.parent.fig.add_subplot(111)
                self.parent.fig.subplots_adjust() # return to default
                self.parent.axes.set_title('Data Window')
                self.parent.axes.set_xlabel('Samples')
                self.parent.axes.set_ylabel('Counts')
                self.parent.axes.set_axis_bgcolor('k')
                self.parent.axes.axis([0,30000,0,2**16-1])
                self.parent.waveform = self.parent.axes.plot(np.arange(30000), np.array([2**15]*30000), color='y')
                self.parent.canvas.draw()
                # other stuff
                self.proto2bytes_po = subprocess.Popen([DAEMON_DIR+'build/proto2bytes', '-s', '-c', self.channelNumLine.text()], stdout=subprocess.PIPE)
                self.timer.start(self.fp)
                self.parent.statusBox.append('Started streaming')
            else:
                self.timer.stop()
                self.proto2bytes_po.kill()
                self.parent.statusBox.append('Stopped streaming')
        else:
            #TODO gray-out the checkbox when the daemon is not running
            self.parent.statusBox.append('Make sure daemon is started,  and standby is on!')
            self.streamCheckbox.setChecked(False) #TODO bug: this still gets checked 1 in 3 times (??)



    def updatePlot(self):
        for i in range(self.nrefresh):
            self.newBuff[i] = self.proto2bytes_po.stdout.readline()
        self.plotBuff = np.concatenate((self.plotBuff[self.nrefresh:],self.newBuff))
        self.parent.waveform[0].set_data(self.xvalues, self.plotBuff)
        self.parent.canvas.draw()

