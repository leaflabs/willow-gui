from PyQt4 import QtCore, QtGui

class PlotDialog(QtGui.QDialog):

    def __init__(self):
        super(PlotDialog, self).__init__()

        self.allDataButton = QtGui.QRadioButton('All data')
        self.allDataButton.setChecked(True)
        self.allDataButton.clicked.connect(self.disableSubsetLines)
        self.subsetButton = QtGui.QRadioButton('Subset:')
        self.subsetButton.clicked.connect(self.enableSubsetLines)
        self.fromLine = QtGui.QLineEdit('0')
        self.fromLine.setDisabled(True)
        self.toLine = QtGui.QLineEdit('30000')
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
        self.layout.addWidget(self.dialogButtons, 2,0)

        self.setLayout(self.layout)

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
            params['sampleRange'] = [int(self.fromLine.text()), int(self.toLine.text())]
        return params
