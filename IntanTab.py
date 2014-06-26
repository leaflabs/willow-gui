from PyQt4 import QtCore, QtGui
import subprocess, os, sys

from parameters import DAEMON_DIR, DATA_DIR

sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

class IntanTab(QtGui.QWidget):

    def __init__(self, parent):
        super(IntanTab, self).__init__(None)
        self.parent = parent

        self.LEDCheckbox = QtGui.QCheckBox('LED')
        self.LEDCheckbox.stateChanged.connect(self.toggleLED)
        self.DSPCheckbox = QtGui.QCheckBox('DSP')
        self.DSPCheckbox.stateChanged.connect(self.toggleDSP)

        ###

        self.chipLine = QtGui.QLineEdit('11111111')
        self.chipRow = QtGui.QWidget()
        lo = QtGui.QHBoxLayout()
        lo.addWidget(QtGui.QLabel('Chip Select:'))
        lo.addWidget(self.chipLine)
        self.chipRow.setLayout(lo)

        self.registerLine = QtGui.QLineEdit()
        self.registerRow = QtGui.QWidget()
        lo = QtGui.QHBoxLayout()
        lo.addWidget(QtGui.QLabel('Register Address:'))
        lo.addWidget(self.registerLine)
        self.registerRow.setLayout(lo)

        self.dataLine = QtGui.QLineEdit()
        self.dataRow = QtGui.QWidget()
        lo = QtGui.QHBoxLayout()
        lo.addWidget(QtGui.QLabel('Data:'))
        lo.addWidget(self.dataLine)
        self.dataRow.setLayout(lo)

        self.writeButton = QtGui.QPushButton('Write')
        self.writeButton.clicked.connect(self.write)

        ###

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel('Common Usage:'))
        self.layout.addWidget(self.LEDCheckbox)
        self.layout.addWidget(self.DSPCheckbox)
        self.layout.addSpacing(100)
        self.layout.addWidget(QtGui.QLabel('Custom Control:'))
        self.layout.addWidget(self.chipRow)
        self.layout.addWidget(self.registerRow)
        self.layout.addWidget(self.dataRow)
        self.layout.addWidget(self.writeButton)
        self.setLayout(self.layout)

    def assembleWriteCommand(self, chips, address, data):
        chips &= 0xFF
        address &= 0b00111111
        data &= 0xFF
        return (1<<24) | (chips<<16) | ((0b10000000 | address) << 8) | data

    def toggleLED(self):
        if (self.parent.isDaemonRunning and self.parent.isDaqRunning):
            if self.LEDCheckbox.isChecked():
                intanCommand = self.assembleWriteCommand(0xFF, 3, 1)
            else:
                intanCommand = self.assembleWriteCommand(0xFF, 3, 0)
            do_control_cmd(reg_write(3, 5, intanCommand))
            do_control_cmd(reg_write(3, 5, 0)) # clear register when finished
        else:
            self.parent.statusBox.append('Make sure daemon is running, and DAQ enabled!')

    def toggleDSP(self):
        if (self.parent.isDaemonRunning and self.parent.isDaqRunning):
            if self.DSPCheckbox.isChecked():
                intanCommand = self.assembleWriteCommand(0xFF, 4, 0x1c)
            else:
                intanCommand = self.assembleWriteCommand(0xFF, 4, 0)
            do_control_cmd(reg_write(3, 5, intanCommand))
            do_control_cmd(reg_write(3, 5, 0)) # clear register when finished
        else:
            self.parent.statusBox.append('Make sure daemon is running, and DAQ enabled!')

    def write(self):
        if (self.parent.isDaemonRunning and self.parent.isDaqRunning):
            chips = int(str(self.chipLine.text()), base=2)
            address = int(str(self.registerLine.text()))
            data = int(str(self.dataLine.text()))
            intanCommand = self.assembleWriteCommand(chips, address, data)
            do_control_cmd(reg_write(3, 5, intanCommand))
        else:
            self.parent.statusBox.append('Make sure daemon is running, and DAQ enabled!')

