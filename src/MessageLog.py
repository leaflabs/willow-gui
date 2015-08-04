from PyQt4 import QtCore, QtGui
import time, datetime

class MessageLog(QtGui.QWidget):

    def __init__(self, debugFlag):
        super(MessageLog, self).__init__()

        self.debugFlag = debugFlag

        self.textEdit = QtGui.QTextEdit()
        self.textEdit.setReadOnly(True)

        self.actionsEdit = QtGui.QTextEdit()
        self.actionsEdit.setReadOnly(True)

        layout = QtGui.QGridLayout()
        layout.addWidget(QtGui.QLabel('<b>Message Log</b>'), 0,0)

        layout.addWidget(self.textEdit, 1,0, 1,3)

        if self.debugFlag:
            layout.addWidget(QtGui.QLabel('<b>Actions Log</b>'), 2,0)
            layout.addWidget(self.actionsEdit, 3,0, 1,3)

        self.setLayout(layout)

    def save(self):
        filename = str(QtGui.QFileDialog.getSaveFileName(self, 'Save Message Log File', '../log/messages'))
        if filename:
            self.messageWrite(filename)
        if self.debugFlag:
            filename = str(QtGui.QFileDialog.getSaveFileName(self, 'Save Actions Log File', '../log/actions'))
        else:
            filename = str(QtGui.QFileDialog.getSaveFileName(self, 'Save Actions Log File (not visible)', '../log/actions'))
        if filename:
            self.actionWrite(filename)

    def messageWrite(self, filename):
        logText = self.textEdit.toPlainText()
        with open(filename, 'w') as f:
            f.write(logText)
        self.post('Saved Message Log to %s' % filename)

    def actionWrite(self, filename):
        actionsText = self.actionsEdit.toPlainText()
        with open(filename, 'w') as f:
            f.write(actionsText)
        self.post('Saved Actions Log to %s' % filename)

    def post(self, msg):
        dt = datetime.datetime.fromtimestamp(time.time())
        prefix = '<b>[%02d:%02d:%02d]</b> ' % (dt.hour, dt.minute, dt.second)
        self.textEdit.append(prefix+msg)

    def actionPost(self, msg):
        dt = datetime.datetime.fromtimestamp(time.time())
        prefix = '<b>[%02d:%02d:%02d]</b> ' % (dt.hour, dt.minute, dt.second)
        self.actionsEdit.append(prefix+msg)

    def append(self, msg):
        self.textEdit.append(msg)
