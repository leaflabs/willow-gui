"""
This feels like a weird implementation; I basically followed this:
http://stackoverflow.com/questions/18196799/how-can-i-show-a-pyqt-modal-dialog-and-get-data-out-of-its-controls-once-its-clo
"""

from PyQt4 import QtCore, QtGui
import time, datetime, os, sys

from parameters import *
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

from StateManagement import checkState, changeState, DaemonControlError

class StreamDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(StreamDialog, self).__init__(parent)

        self.channelNumberLine = QtGui.QLineEdit('99')
        self.yminLine = QtGui.QLineEdit('-6000')
        self.ymaxLine = QtGui.QLineEdit('6000')
        self.refreshRateLine = QtGui.QLineEdit('30')

        self.dialogButtons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)

        layout = QtGui.QGridLayout()
        layout.addWidget(QtGui.QLabel('Channel Number:'), 0,0, 1,1)
        layout.addWidget(self.channelNumberLine, 0,1, 1,2)
        layout.addWidget(QtGui.QLabel('Y-Range (uV):'), 1,0, 1,1)
        layout.addWidget(self.yminLine, 1,1, 1,1)
        layout.addWidget(self.ymaxLine, 1,2, 1,1)
        layout.addWidget(QtGui.QLabel('Refresh Rate:'), 2,0, 1,1)
        layout.addWidget(self.refreshRateLine, 2,1, 1,2)
        layout.addWidget(self.dialogButtons, 3,2, 1,2)

        self.setLayout(layout)
        self.setWindowTitle('Stream Window Parameters')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.resize(500,100)


    def getStreamParams(self):
        channel = int(self.channelNumberLine.text())
        ymin = int(self.yminLine.text())
        ymax = int(self.ymaxLine.text())
        refreshRate = int(self.refreshRateLine.text())
        return channel, ymin, ymax, refreshRate

    @staticmethod
    def getParams(parent=None):
        dialog = StreamDialog(parent)
        result = dialog.exec_()
        params = dialog.getStreamParams()
        return params + (result==QtGui.QDialog.Accepted,)

