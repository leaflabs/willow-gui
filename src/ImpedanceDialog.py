from PyQt4 import QtCore, QtGui
import time, datetime, os, sys

import config

class ImpedanceDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(ImpedanceDialog, self).__init__(parent)

        self.allChipsButton = QtGui.QRadioButton('All Channels')
        self.allChipsButton.setChecked(True)
        self.allChipsButton.clicked.connect(self.setDisabledAllChips)

        self.plotCheckbox = QtGui.QCheckBox('Plot when finished')

        self.oneChannelButton = QtGui.QRadioButton('Single Channel:')
        self.oneChannelButton.clicked.connect(self.setDisabledOneChannel)
        self.oneChannelLine = QtGui.QLineEdit('0')
        self.oneChannelLine.setDisabled(True)

        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.allChipsButton, 0,0)
        layout.addWidget(self.plotCheckbox, 0,1)
        layout.addWidget(self.oneChannelButton, 1,0)
        layout.addWidget(self.oneChannelLine, 1,1)
        layout.addWidget(self.dialogButtons, 2,0, 1,2)
        self.setLayout(layout)
        self.setWindowTitle('Impedance Check Parameters')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))

    def setDisabledAllChips(self):
        self.oneChannelLine.setDisabled(True)
        self.plotCheckbox.setDisabled(False)

    def setDisabledOneChannel(self):
        self.oneChannelLine.setDisabled(False)
        self.plotCheckbox.setDisabled(True)

    def getParams(self):
        params = {}
        if self.allChipsButton.isChecked():
            params['routine'] = 0
            params['plot'] = self.plotCheckbox.isChecked()
        elif self.oneChannelButton.isChecked():
            params['routine'] = 1
            params['channel'] = int(str(self.oneChannelLine.text()))
        return params

    def browse(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save To...', config.dataDir)
        if filename:
            self.filenameLine.setText(filename)
