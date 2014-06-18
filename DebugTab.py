from PyQt4 import QtCore, QtGui

class DebugTab(QtGui.QWidget):

    def __init__(self, parent):
        super(DebugTab, self).__init__(None)
        self.parent = parent

        self.placeholder = QtGui.QLabel('This tab will provide facilities to\nparse and clear error messages.')
        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.placeholder)
        self.setLayout(self.layout)


