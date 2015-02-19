from PyQt4 import QtCore, QtGui
import config

class SettingsWindow(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.cancelButton = QtGui.QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.cancel)

        self.saveButton = QtGui.QPushButton('Save')
        self.saveButton.clicked.connect(self.save)

        layout = QtGui.QGridLayout()
        self.lineEditMap = {}
        self.typeMap = {}
        for i,varName in enumerate(config.jsonDict.keys()):
            lineEdit = QtGui.QLineEdit(str(config.jsonDict[varName]['value']))
            self.lineEditMap[varName] = lineEdit
            self.typeMap[varName] = type(config.jsonDict[varName]['value'])
            layout.addWidget(QtGui.QLabel(config.jsonDict[varName]['description']), i,0)
            layout.addWidget(lineEdit, i,1)
        layout.addWidget(self.cancelButton, i+1,0)
        layout.addWidget(self.saveButton, i+1,1)

        self.setLayout(layout)

        self.setMinimumWidth(500)
        self.setWindowTitle('Configuration Parameters')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))

    def cancel(self):
        self.close()

    def save(self):
        for varName, lineEdit in self.lineEditMap.items():
            config.jsonDict[varName]['value'] = self.typeMap[varName](lineEdit.text())
        config.updateAttributes(config.jsonDict)
        config.saveJSON(config.jsonDict)
        self.close()

