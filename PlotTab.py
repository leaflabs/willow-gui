from PyQt4 import QtCore, QtGui
from PlotWindow import PlotWindow 
from parameters import DAEMON_DIR, DATA_DIR
import os

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

        self.description = QtGui.QLabel('Description goes here')

        self.dirLine = QtGui.QLineEdit(DATA_DIR)
        self.filenameLine = QtGui.QLineEdit()
        self.nsamplesLine = QtGui.QLineEdit('30000')

        self.launchButton = QtGui.QPushButton('Launch')
        self.launchButton.clicked.connect(self.launch)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addSpacing(20)
        self.layout.addWidget(self.description)
        self.layout.addSpacing(20)
        self.layout.addWidget(QtGui.QLabel('Directory:'))
        self.layout.addWidget(self.dirLine)
        self.layout.addWidget(QtGui.QLabel('Filename:'))
        self.layout.addWidget(self.filenameLine)
        self.layout.addWidget(QtGui.QLabel('Number of samples (blank indicates entire file):'))
        self.layout.addWidget(self.nsamplesLine)
        self.layout.addSpacing(40)
        self.layout.addWidget(self.launchButton)
        self.setLayout(self.layout)

    def launch(self):
        directory = str(self.dirLine.text())
        filename = str(self.filenameLine.text())
        nsamples_str = str(self.nsamplesLine.text())
        if isBlank(nsamples_str):
            nsamples = -1
        else:
            nsamples = int(nsamples_str)
            if nsamples <= 0:
                nsamples = -1
        absFilename = os.path.join(directory, filename)
        self.plotWindow = PlotWindow(self, absFilename, nsamples)
        self.plotWindow.show()

