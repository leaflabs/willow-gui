from PyQt4 import QtCore, QtGui
import subprocess

from parameters import *

class DebugTab(QtGui.QWidget):

    def __init__(self, parent):
        super(DebugTab, self).__init__(None)
        self.parent = parent

        self.debugButton = QtGui.QPushButton('Parse Error State')
        self.debugButton.clicked.connect(self.parseErrors)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.debugButton)
        self.setLayout(self.layout)

        self.moduleMap = {1:'central', 2:'sata', 3:'daq', 4:'udp', 5:'gpio'}

    def parseErrors(self):
        if self.parent.isDaemonRunning:
            debugtool_po = subprocess.Popen([DAEMON_DIR+'util/debug_tool.py', 'read', 'error', '0'], stdout=subprocess.PIPE)
            result = debugtool_po.stdout.readline()
            start, stop = result.index('\t'), result.index('|')
            bitfield = int(result[start:stop])
            if bitfield==0:
                self.parent.statusBox.append('No error conditions present on FPGA')
            else:
                bitfield_str = bin(bitfield)[2:].zfill(8)
                badModuleList = []
                # lots of one-off confusion here, but i think this works now
                for i in range(1,8):
                    if bitfield_str[-(i+1)]=='1':
                        badModuleList.append(self.moduleMap[i])
                error_msg = ''
                for module in badModuleList:
                    debugtool_po = subprocess.Popen([DAEMON_DIR+'util/debug_tool.py', 'read', module, '0'], stdout=subprocess.PIPE)
                    result = debugtool_po.stdout.readline()
                    start, stop = result.index('\t'), result.index('|')
                    bitfield = int(result[start:stop])
                    self.parent.statusBox.append(module+' has an error bitfield of: '+str(bitfield))
                    """
                    bitfield_str = bin(bitfield)[2:].zfill(32)
                    for i in range(32):
                        if bitfield_str[-(i+1)]=='1':
                            pass # TODO append to error_msg here
                    self.parent.statusBox.append('Bad Modules: '+badModuleList)
                    """
        else:
            self.parent.statusBox.append('Daemon is not running!')
