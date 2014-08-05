from PyQt4 import QtCore, QtGui
import subprocess, os, sys
import numpy as np

from StreamWindow import StreamWindow


class StreamTab(QtGui.QWidget):

    def __init__(self, parent):
        super(StreamTab, self).__init__(None)
        self.parent = parent

        self.description = QtGui.QLabel('Configure your live streaming '
                                        'parameters, then click Launch to '
                                        'launch the viewing window.')

        self.chipLine = QtGui.QLineEdit('3')
        self.chanListLine = QtGui.QLineEdit('0,1,2,3')

        self.launchButton = QtGui.QPushButton('Launch')
        self.launchButton.clicked.connect(self.launch)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addSpacing(20)
        self.layout.addWidget(self.description)
        self.layout.addSpacing(20)
        self.layout.addWidget(QtGui.QLabel('Chip Number:'))
        self.layout.addWidget(self.chipLine)
        self.layout.addWidget(QtGui.QLabel('Channels (comma-separated):'))
        self.layout.addWidget(self.chanListLine)
        self.layout.addSpacing(40)
        self.layout.addWidget(self.launchButton)
        self.setLayout(self.layout)

    def launch(self):
        chip = int(self.chipLine.text())
        chanList = [int(chan) for chan in str(self.chanListLine.text()).split(',')]
        self.streamWindow = StreamWindow(chip, chanList)
        self.streamWindow.show()

