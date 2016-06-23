from PyQt4 import QtCore, QtGui
import time, datetime, os, sys

import config

LAST_SCRIPT = None

class StreamPickDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(StreamPickDialog, self).__init__(parent)

        self.streamPickGroup = QtGui.QButtonGroup()
        self.button1 = QtGui.QRadioButton('WillowGUI single-channel streaming')
        self.button2 = QtGui.QRadioButton('Custom streaming data script:')
        self.streamPickGroup.addButton(self.button1)
        self.streamPickGroup.addButton(self.button2)
        self.button2.toggled.connect(self.toggleDisabled)
        self.scriptDropdown = self.createScriptDropdown()
        self.button1.setChecked(True)
        self.scriptDropdown.setEnabled(False)
        if LAST_SCRIPT and LAST_SCRIPT != 'default':
            self.button2.setChecked(True)
            lastIndex = self.scriptDropdown.findText(LAST_SCRIPT)
            if lastIndex >= 0:
                self.scriptDropdown.setCurrentIndex(lastIndex)

        # 'cancel' and 'ok'
        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.button1, 0,0, 1,2)
        layout.addWidget(self.button2, 1,0, 1,1)
        layout.addWidget(self.scriptDropdown, 1, 1, 1,1)
        layout.addWidget(self.dialogButtons, 2,1, 1,2)
        self.setLayout(layout)

        self.setWindowTitle('Streaming Script Selection')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.resize(800, 100)
            
    def createScriptDropdown(self):
        dropdown = QtGui.QComboBox()
        streamDirList = os.listdir(config.streamAnalysisDir)
        for entry in streamDirList:
            entry_path = os.path.join(config.streamAnalysisDir, entry)
            if os.path.isdir(entry_path):
                mainpath = os.path.join(entry_path, 'main')
                if os.path.isfile(mainpath) and os.access(mainpath, os.X_OK):
                        dropdown.addItem(entry)
        return dropdown

    def toggleDisabled(self, checked):
        self.scriptDropdown.setEnabled(checked)

    def getChoice(self):
        global LAST_SCRIPT
        if self.scriptDropdown.isEnabled():
            entry = str(self.scriptDropdown.currentText())
            entry_path = os.path.join(config.streamAnalysisDir, entry)
            # check that last choice is still there
            if os.path.isdir(entry_path):
                mainpath = os.path.join(entry_path, 'main')
                if os.path.isfile(mainpath) and os.access(mainpath, os.X_OK):
                    LAST_SCRIPT = str(self.scriptDropdown.currentText()) 
                else:
                    LAST_SCRIPT = 'default'
            else:
                LAST_SCRIPT = 'default'
        else:
            LAST_SCRIPT = 'default'

        return LAST_SCRIPT

