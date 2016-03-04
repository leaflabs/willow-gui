from PyQt4 import QtCore, QtGui
import config

class DirectoryButton(QtGui.QPushButton):

    def __init__(self, description, value):
        QtGui.QPushButton.__init__(self, value)

        self.value = value
        self.description = description
        self.clicked.connect(self.browseForDirectory)

    def browseForDirectory(self):
        filename = QtGui.QFileDialog.getExistingDirectory(self, ('Select %s' % self.description),
                                                          self.value)
        if filename:
            self.setText(filename)


class SettingsWindow(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.cancelButton = QtGui.QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.cancel)

        self.saveButton = QtGui.QPushButton('Save')
        self.saveButton.clicked.connect(self.save)

        layout = QtGui.QGridLayout()

        self.valFieldMap = {}
        self.typeMap = {}
        for i,varName in enumerate(config.jsonDict.keys()):
            description = str(config.jsonDict[varName]['description'])
            value = str(config.jsonDict[varName]['value'])
            self.typeMap[varName] = type(config.jsonDict[varName]['value']) # shouldn't this be 'type'?
            if (varName[-3:] == 'Dir'): # special treatment for directory parameters
                layout.addWidget(QtGui.QLabel(description), i,0)
                dirButton = DirectoryButton(description, value)
                layout.addWidget(dirButton, i,1)
                self.valFieldMap[varName] = dirButton
            else:
                layout.addWidget(QtGui.QLabel(description), i,0)
                lineEdit = QtGui.QLineEdit(value)
                layout.addWidget(lineEdit, i,1)
                self.valFieldMap[varName] = lineEdit
        layout.addWidget(self.cancelButton, i+1,0)
        layout.addWidget(self.saveButton, i+1,1)

        self.setLayout(layout)

        self.setMinimumWidth(500)
        self.center()
        self.setWindowTitle('Configuration Parameters')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))

    def cancel(self):
        self.close()

    def save(self):
        for varName, valField in self.valFieldMap.items():
            config.jsonDict[varName]['value'] = self.typeMap[varName](valField.text())
        config.updateAttributes(config.jsonDict)
        config.saveJSON(config.jsonDict)
        self.close()

    def center(self):
        fmgeo = self.frameGeometry()
        currentScreen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
        centerPoint = QtGui.QApplication.desktop().screenGeometry(currentScreen).center()
        fmgeo.moveCenter(centerPoint)
        self.move(fmgeo.topLeft())
