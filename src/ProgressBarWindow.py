from PyQt4 import QtCore, QtGui


class ProgressBarWindow(QtGui.QWidget):

    def __init__(self, maximum, message):
        super(ProgressBarWindow, self).__init__(None)

        self.maximum = maximum
        self.message = message

        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(maximum)  # TODO what is this number exactly?
        self.progressBar.setValue(0)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel(self.message))
        self.layout.addWidget(self.progressBar)
        self.setLayout(self.layout)

        self.setWindowTitle('Progress Bar')
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        self.center()

    def update(self, val):
        self.progressBar.setValue(val)

    def center(self):
        windowCenter = self.frameGeometry().center()
        screenCenter = QtGui.QDesktopWidget().availableGeometry().center()
        self.move(screenCenter-windowCenter)

