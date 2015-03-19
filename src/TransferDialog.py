from PyQt4 import QtCore, QtGui
import time, datetime, os, sys

import config

class TransferDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(TransferDialog, self).__init__(parent)

        self.allDataButton = QtGui.QRadioButton('Entire Experiment')
        self.allDataButton.setChecked(True)
        self.allDataButton.clicked.connect(self.disableSubsetLine)
        self.subsetButton = QtGui.QRadioButton('Subset, from')
        self.subsetButton.clicked.connect(self.enableSubsetLine)
        self.subsetFromLine = QtGui.QLineEdit('0')
        self.subsetToLine = QtGui.QLineEdit('1')
        self.subsetFromLine.setDisabled(True)
        self.subsetToLine.setDisabled(True)
        self.experimentGroupBox = QtGui.QGroupBox('Experiment')
        layout = QtGui.QGridLayout()
        layout.addWidget(self.allDataButton, 0, 0)
        layout.addWidget(self.subsetButton, 1, 0)
        layout.addWidget(self.subsetFromLine, 1, 1)
        layout.addWidget(QtGui.QLabel('to'), 1, 2)
        layout.addWidget(self.subsetToLine, 1, 3)
        layout.addWidget(QtGui.QLabel('seconds'), 1, 4)
        self.experimentGroupBox.setLayout(layout)

        self.autoNameButton = QtGui.QRadioButton('Name automatically')
        self.autoNameButton.setChecked(True)
        self.autoNameButton.clicked.connect(self.disableFilenameLine)
        self.filenameButton = QtGui.QRadioButton('Filename:')
        self.filenameButton.clicked.connect(self.enableFilenameLine)
        dt = datetime.datetime.fromtimestamp(time.time())
        strtime = '%04d%02d%02d-%02d%02d%02d' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        filename = os.path.join(config.dataDir, 'experiment_T%s.h5' % strtime)
        self.filenameLine = QtGui.QLineEdit(filename)
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
        self.subsetFromLine.setDisabled(True)
        self.subsetToLine.setDisabled(True)

    def enableSubsetLine(self):
        self.subsetFromLine.setDisabled(False)
        self.subsetToLine.setDisabled(False)

    def disableFilenameLine(self):
        self.filenameLine.setDisabled(True)
        self.browseButton.setDisabled(True)

    def enableFilenameLine(self):
        self.filenameLine.setDisabled(False)
        self.browseButton.setDisabled(False)

    def getParams(self):
        params = {}
        if self.subsetButton.isChecked():
            fromSamples = int(float(self.subsetFromLine.text())*30000)
            toSamples = int(float(self.subsetToLine.text())*30000)
            params['sampleRange'] = [fromSamples, toSamples]
        else:
            # return None to indicate "entire experiment"
            params['sampleRange'] = None
        if self.filenameButton.isChecked():
            filename = str(self.filenameLine.text())
            if not os.path.isabs(filename):
                filename = os.path.join(config.dataDir, filename)
            if os.path.splitext(filename)[1] != '.h5':
                filename = filename + '.h5'
            params['filename'] = filename
        else:
            params['filename'] = None
        return params

    def browse(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save To...', config.dataDir)
        if filename:
            self.filenameLine.setText(filename)
