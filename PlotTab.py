from PyQt4 import QtCore, QtGui
from PlotWindow import PlotWindow 
from parameters import DAEMON_DIR, DATA_DIR
import os

from parameters import DAEMON_DIR, DATA_DIR

def isBlank(string):
    if len(string)==0:
        return True
    elif string[0]==' ':
        return isBlank(string[1:])
    else:
        return False

class PlotTab(QtGui.QWidget):

    def __init__(self, parent):
        super(PlotTab, self).__init__(None)
        self.parent = parent

        self.description = QtGui.QLabel('Import a data file, and view the data in an interactive plotting window.')

        self.filenameBrowseWidget = self.FilenameBrowseWidget(self)
        self.nsamplesWidget = self.NSamplesWidget(self)

        self.launchButton = QtGui.QPushButton('Launch')
        self.launchButton.clicked.connect(self.launch)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addSpacing(20)
        self.layout.addWidget(self.description)
        self.layout.addSpacing(20)
        self.layout.addWidget(QtGui.QLabel('Filename:'))
        self.layout.addWidget(self.filenameBrowseWidget)
        self.layout.addWidget(self.nsamplesWidget)
        self.layout.addSpacing(40)
        self.layout.addWidget(self.launchButton)
        self.setLayout(self.layout)

        self.plotWindows = []

    def launch(self):
        filename = str(self.filenameBrowseWidget.filenameLine.text())
        if filename:
            if self.nsamplesWidget.allDataButton.isChecked():
                sampleRange = -1
            elif self.nsamplesWidget.subsetButton.isChecked():
                fromSample = int(self.nsamplesWidget.fromLine.text())
                toSample = int(self.nsamplesWidget.toLine.text())
                sampleRange = [fromSample, toSample]

            plotWindow = PlotWindow(self, filename, sampleRange)
            self.plotWindows.append(plotWindow)
            plotWindow.show()
        else:
            self.parent.statusBox.append('Please enter filename to import.')

    class FilenameBrowseWidget(QtGui.QWidget):

        def __init__(self, parent):
            super(parent.FilenameBrowseWidget, self).__init__()
            self.filenameLine = QtGui.QLineEdit()
            self.browseButton = QtGui.QPushButton('Browse')
            self.browseButton.clicked.connect(self.browse)
            self.layout = QtGui.QHBoxLayout()
            self.layout.addWidget(self.filenameLine)
            self.layout.addWidget(self.browseButton)
            self.setLayout(self.layout)

        def browse(self):
            filename = QtGui.QFileDialog.getOpenFileName(self, 'Import Data File', DATA_DIR)
            self.filenameLine.setText(filename)

    class NSamplesWidget(QtGui.QWidget):

        def __init__(self, parent):
            super(parent.NSamplesWidget, self).__init__()
            self.allDataButton = QtGui.QRadioButton('All data')
            self.allDataButton.setChecked(True)
            self.allDataButton.clicked.connect(self.disableSubsetLines)
            self.subsetButton = QtGui.QRadioButton('Subset:')
            self.subsetButton.clicked.connect(self.enableSubsetLines)
            self.fromLine = QtGui.QLineEdit('0')
            self.fromLine.setDisabled(True)
            self.toLine = QtGui.QLineEdit('30000')
            self.toLine.setDisabled(True)
            self.layout = QtGui.QGridLayout()
            self.layout.addWidget(self.allDataButton, 0,0)
            self.layout.addWidget(self.subsetButton, 1,0)
            self.layout.addWidget(self.fromLine, 1,1)
            self.layout.addWidget(self.toLine, 1,2)
            self.setLayout(self.layout)

        def disableSubsetLines(self):
            self.fromLine.setDisabled(True)
            self.toLine.setDisabled(True)

        def enableSubsetLines(self):
            self.fromLine.setEnabled(True)
            self.toLine.setEnabled(True)
