from PyQt4 import QtCore, QtGui
import subprocess, os, sys

from parameters import DAEMON_DIR, DATA_DIR

sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

class DiskTab(QtGui.QWidget):

    def __init__(self, parent):
        super(DiskTab, self).__init__(None)
        self.parent = parent

        self.startLine = QtGui.QLineEdit('0')
        self.lengthLine = QtGui.QLineEdit('1')

        self.SATAReadButton = QtGui.QPushButton('Read From SATA Disk')
        self.SATAReadButton.clicked.connect(self.readFromSATA)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel('Start Index'))
        self.layout.addWidget(self.startLine)
        self.layout.addWidget(QtGui.QLabel('Read Length'))
        self.layout.addWidget(self.lengthLine)
        self.layout.addWidget(self.SATAReadButton)
        self.layout.addSpacing(200)
        self.setLayout(self.layout)

    def readFromSATA(self):
        if self.parent.isDaemonRunning:
            start = int(str(self.startLine.text()))
            length = int(str(self.lengthLine.text()))
            cmds = []
            cmds.append(reg_write(3, 11, 0))
            cmds.append(reg_write(2,  1, 0))
            cmds.append(reg_write(3,  9, 0))
            cmds.append(reg_write(4,  1, 0))
            cmds.append(reg_write(4, 13, 1))
            cmds.append(reg_write(2, 11, 1))
            cmds.append(reg_write(2, 11, 0))
            cmds.append(reg_write(2,  8, 1))
            cmds.append(reg_write(2,  8, 0))
            cmds.append(reg_write(2,  5, start))
            cmds.append(reg_write(2,  6, length))
            cmds.append(reg_write(4,  1, 1))
            cmds.append(reg_write(2,  1, 1))
            replies = do_control_cmds(cmds)
            for i,reply in enumerate(replies):
                if reply.type == ControlResponse.ERR:
                    print 'error: ', cmds[i].type
            self.parent.statusBox.append('Executed API Recipe 6.3.8')

            cmds = []
            cmds.append(reg_write(2,  1, 0))
            cmds.append(reg_write(4,  1, 0))
            cmds.append(reg_write(2, 11, 1))
            cmds.append(reg_write(2, 11, 0))
            cmds.append(reg_write(2,  8, 1))
            cmds.append(reg_write(2,  8, 0))
            replies = do_control_cmds(cmds)
            for i,reply in enumerate(replies):
                if reply.type == ControlResponse.ERR:
                    print 'error: ', cmds[i].type
            self.parent.statusBox.append('Executed API Recipe 6.3.9')
        else:
            self.parent.statusBox.append('Daemon is not running!')
