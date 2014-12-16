from PyQt4 import QtCore, QtGui
import time, datetime, os, sys

from parameters import *

class SnapshotDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(SnapshotDialog, self).__init__(parent)

        self.nsamplesLine = QtGui.QLineEdit('30000')
        dt = datetime.datetime.fromtimestamp(time.time())
        strtime = '%04d%02d%02d-%02d%02d%02d' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        filename = os.path.join(DATA_DIR, 'snapshot_%s.h5' % strtime)
        self.filenameLine = QtGui.QLineEdit(filename)
        self.browseButton = QtGui.QPushButton('Browse')
        self.browseButton.clicked.connect(self.browse)
        self.plotCheckbox = QtGui.QCheckBox('Plot when finished')

        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        layout = QtGui.QGridLayout()
        layout.addWidget(QtGui.QLabel('Number of Samples:'), 0,0, 1,1)
        layout.addWidget(self.nsamplesLine, 0,1, 1,1)
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
        params['nsamples'] = int(self.nsamplesLine.text())
        params['filename'] = str(self.filenameLine.text())
        params['plot'] = self.plotCheckbox.isChecked()
        return params

    def browse(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save To...', DATA_DIR)
        if filename:
            self.filenameLine.setText(filename)

class SnapshotProgressDialog(QtGui.QDialog):

    def __init__(self, nsamples, filename, parent=None):
        super(SnapshotProgressDialog, self).__init__(parent)

        self.plotButton = QtGui.QPushButton('Plot')
        self.plotButton.setEnabled(False)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel('hello'))
        self.layout.addWidget(QtGui.QLabel('world'))
        self.layout.addWidget(self.plotButton)
        self.setLayout(self.layout)


    def doSnapshot(self, nsamples, filename):
        changeState('take snapshot', nsamples=nsamples, filename=filename)
        self.plotButton.setEnabled(True)

    @staticmethod
    def getPlotChoice(nsamples, filename, parent=None):
        dialog = SnapshotProgressDialog(nsamples, filename, parent)
        #result = dialog.exec_()
        result = dialog.show()
        dialog.doSnapshot(nsamples, filename)
        return result
