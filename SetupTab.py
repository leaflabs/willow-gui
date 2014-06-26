from PyQt4 import QtCore, QtGui
import subprocess, os

from parameters import DAEMON_DIR, DATA_DIR

class SetupTab(QtGui.QWidget):

    def __init__(self, parent):
        super(SetupTab, self).__init__(None)
        self.parent = parent

        self.daemonCheckbox = QtGui.QCheckBox('Daemon Running')
        self.daemonCheckbox.stateChanged.connect(self.toggleDaemon)

        self.daqCheckbox = QtGui.QCheckBox('DAQ Running')
        self.daqCheckbox.stateChanged.connect(self.toggleDAQ)

        self.ethConfigButton = QtGui.QPushButton('Expand Ethernet Buffers')
        self.ethConfigButton.clicked.connect(self.configureEthernet)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.ethConfigButton)
        self.layout.addWidget(self.daemonCheckbox)
        self.layout.addWidget(self.daqCheckbox)
        self.layout.addSpacing(100)
        self.setLayout(self.layout)

        self.acquireDotPy = os.path.join(DAEMON_DIR, 'util/acquire.py')

    def configureEthernet(self):
        """
        Probably this should just be run on init()
        """

        self.parent.statusBox.append('Please enter password in terminal..')
        subprocess.call(os.path.join(DAEMON_DIR, 'util/expand_eth_buffers.sh'))
        self.parent.statusBox.append('Ethernet buffers expanded!')

    def toggleDaemon(self):
        if self.daemonCheckbox.isChecked():
            subprocess.call([os.path.join(DAEMON_DIR, 'build/leafysd'), '-A', '192.168.1.2'])
            self.parent.isDaemonRunning = True
            self.parent.statusBox.append('Daemon started.')
        else:
            subprocess.call(['killall', 'leafysd'])
            self.parent.isDaemonRunning = False
            self.parent.statusBox.append('Daemon stopped.')
        pass

    def toggleDAQ(self):
        if self.parent.isDaemonRunning:
            if self.daqCheckbox.isChecked():
                subprocess.call([self.acquireDotPy, 'start'])
                self.parent.isDaqRunning = True
                self.parent.statusBox.append('DAQ started.')
            else:
                subprocess.call([self.acquireDotPy, 'stop'])
                self.parent.isDaqRunning = False
                self.parent.statusBox.append('DAQ stopped.')
        else:
            self.parent.statusBox.append('Daemon is not running!')
            self.daqCheckbox.setChecked(False) #TODO: gray this out if daemon not running

