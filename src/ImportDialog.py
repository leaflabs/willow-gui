from PyQt4 import QtCore, QtGui
import time, datetime, os, sys

import config

LAST_WHENFINISHED = None

class SnapshotImportDialog(QtGui.QDialog):

    def __init__(self):
        QtGui.QDialog.__init__(self)

        # willow data explorer section
        self.dataExplorerButton = QtGui.QRadioButton('Open using WillowGUI Data Explorer')
        self.dataExplorerButton.setChecked(True)
        self.customButton = QtGui.QRadioButton('Open using custom analysis script:')
        self.customButton.setChecked(False)
        self.customButton.toggled.connect(self.toggleCustom)
        self.scriptDropdown = self.createScriptDropdown()
        self.scriptDropdown.setEnabled(False)

        # dialog buttons
        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        # main layout
        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(self.dataExplorerButton, 0, 0, 1,4)
        mainLayout.addWidget(self.customButton, 3, 0, 1,2)
        mainLayout.addWidget(self.scriptDropdown, 3, 2, 1,2)
        mainLayout.addWidget(self.dialogButtons, 4, 2)
        self.setLayout(mainLayout)

        self.setWindowTitle('Snapshot Import Settings')

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
        params = {'customScript':None}
        if self.customButton.isChecked():
            params['customScript'] = str(self.scriptDropdown.currentText())
        return params

