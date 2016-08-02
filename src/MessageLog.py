from PyQt4 import QtCore, QtGui
import time, datetime

class MessageLog(QtGui.QWidget):

    def __init__(self, debugFlag):
        super(MessageLog, self).__init__()

        self.debugFlag = debugFlag

        # messages about Willow's state
        self.messageLog = QtGui.QTextEdit()
        self.messageLog.setReadOnly(True)
        self.messageLog.objectName = 'Messages'

        # descriptions of actions initiated by user
        self.actionLog = QtGui.QTextEdit()
        self.actionLog.setReadOnly(True)
        self.actionLog.objectName = 'Actions'

        # user-recorded notes
        self.noteLog = QtGui.QWidget()
        self.oldNotes = QtGui.QTextEdit()
        self.oldNotes.setReadOnly(True)
        self.oldNotes.objectName = 'Notes'
        self.newNote = QtGui.QPlainTextEdit()
        self.newNote.setReadOnly(False)
        self.recordNote = QtGui.QPushButton('Record note to log')
        self.recordNote.clicked.connect(self.takeNote)
        noteLayout = QtGui.QVBoxLayout()
        noteLayout.addWidget(self.oldNotes, stretch=2)
        noteLayout.addWidget(self.newNote, stretch=1)
        noteLayout.addWidget(self.recordNote)
        self.noteLog.setLayout(noteLayout)
        self.noteLog.objectName = 'Notes'

        # backlogs are QTextEdits with actual text we care about
        self.backlogs = [self.messageLog, self.oldNotes, self.actionLog]

        # visibleLogs are widgets the user looks at
        if self.debugFlag:
            self.visibleLogs = [self.messageLog, self.noteLog, self.actionLog]
        else:
            self.visibleLogs = [self.messageLog, self.noteLog]

        self.logPicker = QtGui.QTabWidget(parent=self)
        for log in self.visibleLogs:
            self.logPicker.addTab(log, '&'+log.objectName)
        self.logPicker.setFocusPolicy(QtCore.Qt.StrongFocus)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.logPicker)
        self.setLayout(mainLayout)

    def save(self):
        for log in self.backlogs:
            self.logWrite(log)

    def logWrite(self, log, filename=None):
        if filename:
            logText = log.toPlainText()
            with open(filename, 'w') as f:
                f.write(logText)
            self.post('Saved {} Log to {}'.format(log.objectName, filename), 
                    log=self.messageLog)
            print "saved"
        else:
            filename = str(QtGui.QFileDialog.getSaveFileName(self,
                'Save {} File'.format(log.objectName), '../log/{}'.format(log.objectName).lower()))
            self.logWrite(log, filename)

    def takeNote(self):
        message = self.newNote.toPlainText()
        self.post(message, log=self.oldNotes)
        self.newNote.clear()

    def post(self, message, **kwargs):
        log = kwargs.get('log', self.messageLog)
        dt = datetime.datetime.fromtimestamp(time.time())
        prefix = QtCore.QString('<b>[%02d:%02d:%02d]</b> ' % (dt.hour, dt.minute, dt.second))
        # make multi-line messages be printed prettily
        split_messages = str(message).splitlines()
        log.append(prefix + QtCore.QString(split_messages.pop(0)))
        while split_messages != []:
            log.append(QtCore.QString(split_messages.pop(0)))

    def keyPressEvent(self, e):
        # Allow Ctrl-Enter as a shortcut for note taking when that tab is open.
        if self.logPicker.currentWidget() == self.noteLog \
                              and e.key() == QtCore.Qt.Key_Return \
                        and e.modifiers() == QtCore.Qt.ControlModifier:
            self.takeNote()

