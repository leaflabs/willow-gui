from PyQt4 import QtCore, QtGui
import time, datetime, os, sys

import config

LAST_WHENFINISHED = None

class ImportDialog_experiment(QtGui.QDialog):

    def __init__(self):
        QtGui.QDialog.__init__(self)

        self.allDataButton = QtGui.QRadioButton('All data')
        self.allDataButton.setChecked(True)
        self.allDataButton.clicked.connect(self.disableSubsetLines)
        self.subsetButton = QtGui.QRadioButton('Subset (seconds):')
        self.subsetButton.clicked.connect(self.enableSubsetLines)
        self.fromLine = QtGui.QLineEdit('0')
        self.fromLine.setDisabled(True)
        self.toLine = QtGui.QLineEdit('1')
        self.toLine.setDisabled(True)

        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.allDataButton, 0,0)
        self.layout.addWidget(self.subsetButton, 1,0)
        self.layout.addWidget(self.fromLine, 1,1)
        self.layout.addWidget(self.toLine, 1,2)
        self.layout.addWidget(self.dialogButtons, 2,1, 1,2)

        self.setLayout(self.layout)
        self.setWindowTitle('Import Settings (experiment)')

    def disableSubsetLines(self):
        self.fromLine.setDisabled(True)
        self.toLine.setDisabled(True)

    def enableSubsetLines(self):
        self.fromLine.setEnabled(True)
        self.toLine.setEnabled(True)

    def getParams(self):
        params = {}
        if self.allDataButton.isChecked():
            params['sampleRange'] = -1
        else:
            params['sampleRange'] = [int(float(self.fromLine.text())*30000),
                int(float(self.toLine.text())*30000)-1]
        return params

class ImportDialog_snapshot(QtGui.QDialog):

    def __init__(self):
        QtGui.QDialog.__init__(self)

        # willow data explorer section
        self.dataExplorerButton = QtGui.QRadioButton('Open using WillowGUI Data Explorer')
        self.dataExplorerButton.setChecked(True)
        self.dataExplorerButton.toggled.connect(self.toggleDataExplorer)
        self.allDataButton = QtGui.QRadioButton('All data')
        self.allDataButton.setChecked(True)
        self.subsetButton = QtGui.QRadioButton('Subset (seconds):')
        self.subsetButton.toggled.connect(self.toggleSubset)
        self.fromLine = QtGui.QLineEdit('0')
        self.fromLine.setDisabled(True)
        self.toLine = QtGui.QLineEdit('1')
        self.toLine.setDisabled(True)

        # custom script section
        self.customButton = QtGui.QRadioButton('Open using custom analysis script:')
        self.customButton.setChecked(False)
        self.customButton.toggled.connect(self.toggleCustom)
        self.scriptDropdown = self.createScriptDropdown()
        self.scriptDropdown.setEnabled(False)

        """
        if LAST_WHENFINISHED:
            lastButton = self.finishedGroup.button(LAST_WHENFINISHED[0])
            lastButton.setChecked(True)
            lastIndex = self.scriptDropdown.findText(LAST_WHENFINISHED[1])
            if lastIndex >= 0:
                self.scriptDropdown.setCurrentIndex(lastIndex)
        """

        # dialog buttons
        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        # groupings
        self.plotMethodGroup = QtGui.QButtonGroup()
        for b in [self.dataExplorerButton, self.customButton]:
            self.plotMethodGroup.addButton(b)
        self.rangeGroup = QtGui.QButtonGroup()
        for b in [self.allDataButton, self.subsetButton]:
            self.rangeGroup.addButton(b)

        # main layout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.dataExplorerButton, 0, 0, 1,4)
        mainLayout.addWidget(self.allDataButton, 1, 1)
        mainLayout.addWidget(self.subsetButton, 2, 1)
        mainLayout.addWidget(self.fromLine, 2, 2)
        mainLayout.addWidget(self.toLine, 2, 3)
        mainLayout.addWidget(self.customButton, 3, 0, 1,2)
        mainLayout.addWidget(self.scriptDropdown, 3, 2, 1,2)
        mainLayout.addWidget(self.dialogButtons, 4, 2)
        self.setLayout(mainLayout)

        self.setWindowTitle('Import Settings (experiment)')

    def toggleDataExplorer(self, checked):
        self.allDataButton.setEnabled(checked)
        self.subsetButton.setEnabled(checked)

    def toggleSubset(self, checked):
        self.fromLine.setEnabled(checked)
        self.toLine.setEnabled(checked)

    def toggleCustom(self, checked):
        self.scriptDropdown.setEnabled(checked)

    def createScriptDropdown(self):
        dropdown = QtGui.QComboBox()
        analysisDirList = os.listdir(config.analysisDirSnapshot)
        for entry in analysisDirList:
            entrypath = os.path.join(config.analysisDirSnapshot, entry)
            if os.path.isdir(entrypath):
                mainpath = os.path.join(entrypath, 'main')
                if os.path.isfile(mainpath) and os.access(mainpath, os.X_OK):
                        dropdown.addItem(entry)
        return dropdown

    def getParams(self):
        params = {'sampleRange':None, 'customScript':None}
        if self.dataExplorerButton.isChecked():
            if self.allDataButton.isChecked():
                params['sampleRange'] = -1
            else:
                params['sampleRange'] = [int(float(self.fromLine.text())*30000),
                int(float(self.toLine.text())*30000)-1]
        else:
            params['customScript'] = str(self.scriptDropdown.currentText())
        return params

