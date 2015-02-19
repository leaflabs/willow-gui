from PyQt4 import QtCore, QtGui

class StreamDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(StreamDialog, self).__init__(parent)

        self.channelNumberLine = QtGui.QLineEdit('0')
        self.yminLine = QtGui.QLineEdit('-6000')
        self.ymaxLine = QtGui.QLineEdit('6000')
        self.refreshRateLine = QtGui.QLineEdit('20')

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
        layout.addWidget(QtGui.QLabel('Refresh Rate (Hz):'), 2,0, 1,1)
        layout.addWidget(self.refreshRateLine, 2,1, 1,2)
        layout.addWidget(self.dialogButtons, 3,2, 1,2)

        self.setLayout(layout)
        self.setWindowTitle('Stream Window Parameters')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.resize(500,100)


    def getParams(self):
        params = {}
        params['channel'] = int(self.channelNumberLine.text())
        params['ymin'] = int(self.yminLine.text())
        params['ymax'] = int(self.ymaxLine.text())
        params['refreshRate'] = int(self.refreshRateLine.text())
        return params

