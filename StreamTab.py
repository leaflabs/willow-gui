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
                                        'open a viewing window.')

        self.chipChanWidget = self.ChipChanWidget(self)

        self.launchButton = QtGui.QPushButton('Launch')
        self.launchButton.clicked.connect(self.launch)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addSpacing(20)
        self.layout.addWidget(self.description)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.chipChanWidget)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.launchButton)
        self.setLayout(self.layout)

    class ChipChanWidget(QtGui.QWidget):

        def __init__(self, parent):
            super(parent.ChipChanWidget, self).__init__()
            self.chipLine = QtGui.QLineEdit('3')
            self.chanLine = QtGui.QLineEdit('3')
            self.layout = QtGui.QGridLayout()
            self.layout.addWidget(QtGui.QLabel('Chip Number:'), 0,0)
            self.layout.addWidget(self.chipLine, 0,1)
            self.layout.addWidget(QtGui.QLabel('Channel Number:'), 1,0)
            self.layout.addWidget(self.chanLine, 1,1)
            self.setLayout(self.layout)

    def launch(self):
        """
        How does this handle multiple instances of StreamWindow?
        Is it robust?
        """
        chip = int(self.chipChanWidget.chipLine.text())
        chan = int(self.chipChanWidget.chanLine.text())
        self.streamWindow = StreamWindow(self, chip, chan)
        self.streamWindow.show()

