from PyQt4 import QtCore, QtGui
import time, datetime, os, sys

import config

class ImpedanceDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(ImpedanceDialog, self).__init__(parent)

        self.allChipsButton = QtGui.QRadioButton('All Chips')
        self.allChipsButton.setChecked(True)
        self.allChipsButton.clicked.connect(self.disableOneChipLine)
        self.oneChipButton = QtGui.QRadioButton('Chip #:')
        self.oneChipButton.clicked.connect(self.enableOneChipLine)
        self.oneChipLine = QtGui.QLineEdit('0')
        self.oneChipLine.setDisabled(True)
        self.chipGroupBox = QtGui.QGroupBox('Chip')
        layout = QtGui.QGridLayout()
        layout.addWidget(self.allChipsButton, 0, 0)
        layout.addWidget(self.oneChipButton, 1, 0)
        layout.addWidget(self.oneChipLine, 1, 1)
        self.chipGroupBox.setLayout(layout)

        self.chanLine = QtGui.QLineEdit('0')
        self.chanGroupBox = QtGui.QGroupBox('Channel')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.chanLine)
        self.chanGroupBox.setLayout(layout)

        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.chipGroupBox)
        layout.addWidget(self.chanGroupBox)
        layout.addWidget(self.dialogButtons)
        self.setLayout(layout)
        self.setWindowTitle('Impedance Check Parameters')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))

    def disableOneChipLine(self):
        self.oneChipLine.setDisabled(True)

    def enableOneChipLine(self):
        self.oneChipLine.setDisabled(False)

    def getParams(self):
        params = {}
        if self.oneChipButton.isChecked():
            params['chip'] = int(self.oneChipLine.text())
        else:
            params['chip'] = -1
        params['chan'] = int(self.chanLine.text())
        return params

    def browse(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save To...', config.dataDir)
        if filename:
            self.filenameLine.setText(filename)
