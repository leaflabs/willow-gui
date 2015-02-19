from PyQt4 import QtCore, QtGui
import time, datetime, os, sys

import config

class SnapshotDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(SnapshotDialog, self).__init__(parent)

        self.lengthLine = QtGui.QLineEdit('1')
        dt = datetime.datetime.fromtimestamp(time.time())
        strtime = '%04d%02d%02d-%02d%02d%02d' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        filename = os.path.join(config.dataDir, 'snapshot_%s.h5' % strtime)
        self.filenameLine = QtGui.QLineEdit(filename)
        self.browseButton = QtGui.QPushButton('Browse')
        self.browseButton.clicked.connect(self.browse)
        self.plotCheckbox = QtGui.QCheckBox('Plot when finished')

        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        layout = QtGui.QGridLayout()
        layout.addWidget(QtGui.QLabel('Length (seconds):'), 0,0, 1,1)
        layout.addWidget(self.lengthLine, 0,1, 1,1)
        layout.addWidget(QtGui.QLabel('Filename:'), 1,0, 1,1)
        layout.addWidget(self.filenameLine, 1,1, 1,3)
        layout.addWidget(self.browseButton, 1,4, 1,1)
        layout.addWidget(self.plotCheckbox, 2,0, 1,1)

        layout.addWidget(self.dialogButtons, 2,1, 1,2)

        self.setLayout(layout)
        self.setWindowTitle('Snapshot Parameters')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.resize(800,100)

    def getParams(self):
        params = {}
        params['nsamples'] = int(float(self.lengthLine.text())*30000)
        filename = str(self.filenameLine.text())
        if not os.path.isabs(filename):
            filename = os.path.join(config.dataDir, filename)
        if os.path.splitext(filename)[1] != '.h5':
            filename = filename + '.h5'
        params['filename'] = filename
        params['plot'] = self.plotCheckbox.isChecked()
        return params

    def browse(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save To...', config.dataDir)
        if filename:
            self.filenameLine.setText(filename)
