from PyQt4 import QtCore, QtGui
import subprocess

from parameters import *

class DebugTab(QtGui.QWidget):

    def __init__(self, parent):
        super(DebugTab, self).__init__(None)
        self.parent = parent

        self.debugButton = QtGui.QPushButton('Parse Error State')
        self.debugButton.clicked.connect(self.parseErrors)

        self.resetButton = QtGui.QPushButton('Manually clear error registers (not recommended!)')
        self.resetButton.clicked.connect(self.clearErrorRegisters)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.debugButton)
        self.layout.addWidget(self.resetButton)
        self.setLayout(self.layout)

        self.moduleMap = {1:'central', 2:'sata', 3:'daq', 4:'udp', 5:'gpio'}
        self.errorMap = {
            'central' : {0:'Module Configuration Error'},
            'sata' : {0:'Module Configuration Error', 1:'Disk Not Ready', 2:'SATA-UDP FIFO Underflow', 3:'SATA-UDP FIFO Overflow', 4:'SATA Read FIFO Overflow', 5:'SATA Read FIFO Overflow', 6:'Disk Removed', 7:'Other Error', 8:'Low-Level SATA Error (see bits 23:16)'},
            'daq' : {0:'Module Configuration Error', 1:'DAQ-UDP FIFO Underflow', 2:'DAQ-UDP FIFO Overflow', 3:'DAQ-SATA FIFO Underflow', 4:'DAQ-SATA FIFO Overflow'},
            'udp' : {0:'Module Configuration Error', 7:'Other error'},
            'gpio' : {0:'Module Configuration Error'}
        }

    def parseErrors(self):
        if self.parent.isDaemonRunning:
            debugtool_po = subprocess.Popen([DAEMON_DIR+'util/debug_tool.py', 'read', 'error', '0'], stdout=subprocess.PIPE)
            result = debugtool_po.stdout.readline()
            start, stop = result.index('\t'), result.index('|')
            errmod_bitfield = int(result[start:stop])
            if errmod_bitfield==0:
                self.parent.statusBox.append('No error conditions present on FPGA')
            else:
                errmod_bitfield_str = bin(errmod_bitfield)[2:].zfill(8)
                # lots of one-off confusion here, but i think this works now
                for i in range(1,8):
                    if errmod_bitfield_str[-(i+1)]=='1':
                        module = self.moduleMap[i]
                        debugtool_po = subprocess.Popen([DAEMON_DIR+'util/debug_tool.py', 'read', module, '0'], stdout=subprocess.PIPE)
                        result = debugtool_po.stdout.readline()
                        start, stop = result.index('\t'), result.index('|')
                        mod_bitfield = int(result[start:stop])
                        #self.parent.statusBox.append(module+' has an error bitfield of: '+str(bitfield))
                        mod_bitfield_str = bin(mod_bitfield)[2:].zfill(10)
                        nerrs = mod_bitfield_str.count('1')
                        self.parent.statusBox.append(str(nerrs)+' error(s) in '+module.upper()+' module:')
                        for j in range(10):
                            if mod_bitfield_str[-(j+1)]=='1':
                                try:
                                    errmsg = self.errorMap[module][j]
                                    self.parent.statusBox.append('\t'+errmsg)
                                except KeyError:
                                    self.parent.statusBox.append('Unknown error!')
        else:
            self.parent.statusBox.append('Daemon is not running!')

    def clearErrorRegisters(self):
        subprocess.call([DAEMON_DIR+'util/debug_tool.py', 'write', 'central', '0', '0'])
        subprocess.call([DAEMON_DIR+'util/debug_tool.py', 'write', 'sata', '0', '0'])
        subprocess.call([DAEMON_DIR+'util/debug_tool.py', 'write', 'daq', '0', '0'])
        subprocess.call([DAEMON_DIR+'util/debug_tool.py', 'write', 'udp', '0', '0'])
        subprocess.call([DAEMON_DIR+'util/debug_tool.py', 'write', 'gpio', '0', '0'])
        subprocess.call([DAEMON_DIR+'util/debug_tool.py', 'write', 'error', '0', '0'])
        self.parent.statusBox.append('Error registers cleared. Note, WiredLeaf may be in a funky state. Recommend soft hardware reset.')


