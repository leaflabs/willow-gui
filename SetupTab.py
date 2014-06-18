from PyQt4 import QtCore, QtGui
import subprocess

from parameters import *

class SetupTab(QtGui.QWidget):

    def __init__(self, parent):
        super(SetupTab, self).__init__(None)
        self.parent = parent

        self.daemonCheckbox = QtGui.QCheckBox('Daemon Running')
        self.daemonCheckbox.stateChanged.connect(self.toggleDaemon)

        # Test keypress
        self.keypressCheckbox = QtGui.QCheckBox('Test Keypress')
        self.shcut = QtGui.QShortcut(self)
        self.shcut.setKey("space")
        self.shcut.activated.connect(self.handleKeypress)

        self.ethConfigButton = QtGui.QPushButton('Expand Ethernet Buffers')
        self.ethConfigButton.clicked.connect(self.configureEthernet)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.daemonCheckbox)
        self.layout.addWidget(self.keypressCheckbox)
        self.layout.addWidget(self.ethConfigButton)
        self.setLayout(self.layout)

    def toggleDaemon(self):

        if self.daemonCheckbox.isChecked():
            subprocess.call([DAEMON_DIR+'build/leafysd', '-A', '192.168.1.2'])
            self.parent.statusBox.setText('Daemon started')
        else:
            subprocess.call(['killall', 'leafysd'])
            self.parent.statusBox.setText('Daemon stopped')
        pass

    def configureEthernet(self):
        """
        Probably this should just be run on init()
        """

        self.parent.statusBox.setText('Please enter password in terminal..')
        subprocess.call(DAEMON_DIR+'util/expand_eth_buffers.sh')
        self.parent.statusBox.setText('Ethernet buffers expanded!')

    def handleKeypress(self):
        if self.keypressCheckbox.isChecked():
            self.keypressCheckbox.setChecked(False)
        else:
            self.keypressCheckbox.setChecked(True)

