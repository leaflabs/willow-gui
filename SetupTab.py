from PyQt4 import QtCore, QtGui
import subprocess

from parameters import DAEMON_DIR, DATA_DIR

class SetupTab(QtGui.QWidget):

    def __init__(self, parent):
        super(SetupTab, self).__init__(None)
        self.parent = parent

        self.daemonCheckbox = QtGui.QCheckBox('Daemon Running')
        self.daemonCheckbox.stateChanged.connect(self.toggleDaemon)

        self.ethConfigButton = QtGui.QPushButton('Expand Ethernet Buffers')
        self.ethConfigButton.clicked.connect(self.configureEthernet)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.ethConfigButton)
        self.layout.addWidget(self.daemonCheckbox)
        self.layout.addSpacing(100)
        self.setLayout(self.layout)

    def toggleDaemon(self):

        if self.daemonCheckbox.isChecked():
            subprocess.call([DAEMON_DIR+'build/leafysd', '-A', '192.168.1.2'])
            self.parent.isDaemonRunning = True
            self.parent.statusBox.append('Daemon started')
        else:
            subprocess.call(['killall', 'leafysd'])
            self.parent.isDaemonRunning = False
            self.parent.statusBox.append('Daemon stopped')
        pass

    def configureEthernet(self):
        """
        Probably this should just be run on init()
        """

        self.parent.statusBox.append('Please enter password in terminal..')
        subprocess.call(DAEMON_DIR+'util/expand_eth_buffers.sh')
        self.parent.statusBox.append('Ethernet buffers expanded!')

    def handleKeypress(self):
        if self.keypressCheckbox.isChecked():
            self.keypressCheckbox.setChecked(False)
        else:
            self.keypressCheckbox.setChecked(True)

