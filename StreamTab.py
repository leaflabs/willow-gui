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
        self.chanLine = QtGui.QLineEdit('3')

        self.launchButton = QtGui.QPushButton('Launch')
        self.launchButton.clicked.connect(self.launch)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addSpacing(20)
        self.layout.addWidget(self.description)
        self.layout.addSpacing(20)
        self.layout.addWidget(QtGui.QLabel('Chip Number:'))
        self.layout.addWidget(self.chipLine)
        self.layout.addWidget(QtGui.QLabel('Channel Number:'))
        self.layout.addWidget(self.chanListLine)
        self.layout.addSpacing(40)
        self.layout.addWidget(self.launchButton)
        self.setLayout(self.layout)

    def launch(self):
        chip = int(self.chipLine.text())
        chan = int(self.chanLine.text())
        self.streamWindow = StreamWindow(chip, chan)
        self.streamWindow.show()

