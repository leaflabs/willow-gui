from PyQt4 import QtCore, QtGui
import time, datetime, os, sys

from parameters import *

class TransferDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(TransferDialog, self).__init__(parent)

        self.allDataButton = QtGui.QRadioButton('Entire Experiment')
        self.allDataButton.setChecked(True)
        self.allDataButton.clicked.connect(self.disableSubsetLine)
        self.subsetButton = QtGui.QRadioButton('Subset (seconds):')
        self.subsetButton.clicked.connect(self.enableSubsetLine)
        self.subsetLine = QtGui.QLineEdit('10')
        self.subsetLine.setDisabled(True)
        self.experimentGroupBox = QtGui.QGroupBox('Experiment')
        layout = QtGui.QGridLayout()
        layout.addWidget(self.allDataButton, 0, 0)
        layout.addWidget(self.subsetButton, 1, 0)
        layout.addWidget(self.subsetLine, 1, 1)
        self.experimentGroupBox.setLayout(layout)

        self.autoNameButton = QtGui.QRadioButton('Name automatically')
        self.autoNameButton.setChecked(True)
        self.autoNameButton.clicked.connect(self.disableFilenameLine)
        self.filenameButton = QtGui.QRadioButton('Filename:')
        self.filenameButton.clicked.connect(self.enableFilenameLine)
        self.filenameLine = QtGui.QLineEdit()
        self.filenameLine.setDisabled(True)
        self.browseButton = QtGui.QPushButton('Browse')
        self.browseButton.clicked.connect(self.browse)
        self.browseButton.setDisabled(True)
        self.filenameGroupBox = QtGui.QGroupBox('Filename')
        layout = QtGui.QGridLayout()
        layout.addWidget(self.autoNameButton, 0,0)
        layout.addWidget(self.filenameButton, 1,0)
        layout.addWidget(self.filenameLine, 2,0)
        layout.addWidget(self.browseButton, 2,1)
        self.filenameGroupBox.setLayout(layout)

        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.experimentGroupBox)
        layout.addWidget(self.filenameGroupBox)
        layout.addWidget(self.dialogButtons)
        self.setLayout(layout)
        self.setWindowTitle('Transfer Parameters')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))

    def disableSubsetLine(self):
        self.subsetLine.setDisabled(True)

    def enableSubsetLine(self):
        self.subsetLine.setDisabled(False)

    def disableFilenameLine(self):
        self.filenameLine.setDisabled(True)
        self.browseButton.setDisabled(True)

    def enableFilenameLine(self):
        self.filenameLine.setDisabled(False)
        self.browseButton.setDisabled(False)

    def getParams(self):
        params = {}
        if self.subsetButton.isChecked():
            params['nsamples'] = int(float(self.subsetLine.text())*30000)
        else:
            params['nsamples'] = None
        if self.filenameButton.isChecked():
            filename = str(self.filenameLine.text())
            if not os.path.isabs(filename):
                filename = os.path.join(DATA_DIR, filename)
            params['filename'] = filename
        else:
            params['filename'] = False
        return params

    def browse(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save To...', DATA_DIR)
        if filename:
            self.filenameLine.setText(filename)
