from PyQt4 import QtCore, QtGui
import time, datetime, os, sys

import config

LAST_WHENFINISHED = None

class SnapshotDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(SnapshotDialog, self).__init__(parent)

        # length and filename
        self.lengthLine = QtGui.QLineEdit('1')
        dt = datetime.datetime.fromtimestamp(time.time())
        strtime = '%04d%02d%02d-%02d%02d%02d' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        filename = os.path.join(config.dataDir, 'snapshot_%s.h5' % strtime)
        self.filenameLine = QtGui.QLineEdit(filename)
        self.browseButton = QtGui.QPushButton('Browse')
        self.browseButton.clicked.connect(self.browse)

        # "when finished" widget
        self.finishedWidget = QtGui.QWidget()
        self.finishedGroup = QtGui.QButtonGroup()
        self.button1 = QtGui.QRadioButton('Do Nothing (just save)')
        self.button2 = QtGui.QRadioButton('Open using WillowGUI Data Explorer')
        self.button3 = QtGui.QRadioButton('Open using custom analysis script:')
        for b in [self.button1, self.button2, self.button3]:
            self.finishedGroup.addButton(b)
        self.button3.toggled.connect(self.toggleDisabled)
        self.scriptDropdown = self.createScriptDropdown()
        self.button1.setChecked(True)
        self.scriptDropdown.setEnabled(False)
        layout = QtGui.QGridLayout()
        layout.addWidget(self.button1, 0,0, 1,2)
        layout.addWidget(self.button2, 1,0, 1,2)
        layout.addWidget(self.button3, 2,0, 1,1)
        layout.addWidget(self.scriptDropdown, 2,1, 1,1)
        self.finishedWidget.setLayout(layout)
        if LAST_WHENFINISHED:
            lastButton = self.finishedGroup.button(LAST_WHENFINISHED[0])
            lastButton.setChecked(True)
            lastIndex = self.scriptDropdown.findText(LAST_WHENFINISHED[1])
            if lastIndex >= 0:
                self.scriptDropdown.setCurrentIndex(lastIndex)

        # 'cancel' and 'ok'
        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(QtGui.QLabel('Length (seconds):'), 0,0, 1,1)
        self.layout.addWidget(self.lengthLine, 0,1, 1,1)
        self.layout.addWidget(QtGui.QLabel('Filename:'), 1,0, 1,1)
        self.layout.addWidget(self.filenameLine, 1,1, 1,3)
        self.layout.addWidget(self.browseButton, 1,4, 1,1)
        self.layout.addWidget(QtGui.QLabel('When finished:'), 2,0, 1,1)
        self.layout.addWidget(self.finishedWidget, 2,1, 1,1)

        self.layout.addWidget(self.dialogButtons, 3,1, 1,2)

        self.setLayout(self.layout)
        self.setWindowTitle('Snapshot Parameters')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.resize(800,100)

    def createScriptDropdown(self):
        dropdown = QtGui.QComboBox()
        analysisDirList = os.listdir(config.analysisDir)
        for entry in analysisDirList:
            entrypath = os.path.join(config.analysisDir, entry)
            if os.path.isdir(entrypath):
                mainpath = os.path.join(entrypath, 'main')
                if os.path.isfile(mainpath) and os.access(mainpath, os.X_OK):
                        dropdown.addItem(entry)
        return dropdown

    def toggleDisabled(self, checked):
        self.scriptDropdown.setEnabled(checked)

    def getParams(self):
        global LAST_WHENFINISHED
        params = {}
        params['nsamples'] = int(float(self.lengthLine.text())*30000)
        filename = str(self.filenameLine.text())
        if not os.path.isabs(filename):
            filename = os.path.join(config.dataDir, filename)
        if os.path.splitext(filename)[1] != '.h5':
            filename = filename + '.h5'
        params['filename'] = filename
        params['whenFinished'] = (self.finishedGroup.checkedId(), str(self.scriptDropdown.currentText()))
        LAST_WHENFINISHED = params['whenFinished']
        return params

    def browse(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save To...', config.dataDir)
        if filename:
            self.filenameLine.setText(filename)
