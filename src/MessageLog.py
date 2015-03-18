from PyQt4 import QtCore, QtGui
import time, datetime

class MessageLog(QtGui.QWidget):

    def __init__(self):
        super(MessageLog, self).__init__()

        self.textEdit = QtGui.QTextEdit()
        self.textEdit.setReadOnly(True)

        self.clearButton = QtGui.QPushButton('Clear')
        self.clearButton.clicked.connect(self.clear)
        self.saveButton = QtGui.QPushButton('Save')
        self.saveButton.clicked.connect(self.save)

        layout = QtGui.QGridLayout()
        layout.addWidget(QtGui.QLabel('<b>Message Log</b>'), 0,0)
        layout.addWidget(self.clearButton, 0,1)
        layout.addWidget(self.saveButton, 0,2)
        layout.addWidget(self.textEdit, 1,0, 3,3)

        self.setLayout(layout)

    def clear(self):
        self.textEdit.clear()

    def save(self):
        filename = str(QtGui.QFileDialog.getSaveFileName(self, 'Save Log File', '../log/'))
        if filename:
            logText = self.textEdit.toPlainText()
            with open(filename, 'w') as f:
                f.write(logText)
            self.post('Saved Message Log to %s' % filename)

    def post(self, msg):
        dt = datetime.datetime.fromtimestamp(time.time())
        prefix = '<b>[%02d:%02d:%02d]</b> ' % (dt.hour, dt.minute, dt.second)
        self.textEdit.append(prefix+msg)

    def append(self, msg):
        self.textEdit.append(msg)
