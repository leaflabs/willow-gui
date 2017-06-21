import os, subprocess, socket 

from git import Repo

import config, hwif
from StatusBar import StatusBar
from ButtonPanel import ButtonPanel
from MessageLog import MessageLog

from PyQt4 import QtCore, QtGui

import datetime, time, zipfile
if not os.path.isdir('../log'):
    os.mkdir('../log')
oFile = open('../log/oFile', 'w')
eFile = open('../log/eFile', 'w')


class DaemonMissingError(Exception):

    def __init__(self, path):
        self.path = path


class MainWindow(QtGui.QWidget):

    def __init__(self, debugFlag, parent=None):
        QtGui.QWidget.__init__(self)

        self.debugFlag = debugFlag

        self.msgLog = MessageLog(debugFlag)
        self.statusBar = StatusBar(self.msgLog)
        self.buttonPanel = ButtonPanel(self.msgLog)
        self.buttonPanel.logPackageRequested.connect(self.packageLogs)

        self.statusBar.diskFillupDetected.connect(self.buttonPanel.handleDiskFillup)


        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.statusBar)
        mainLayout.addWidget(self.buttonPanel)
        mainLayout.addWidget(self.msgLog)
        self.setLayout(mainLayout)

        versionFile = open('../VERSION', 'r')
        versionNumber = versionFile.readline().rstrip('\n')
        if not Repo('..').head.is_detached:
            branchName = Repo('..').active_branch.name
        else:
            branchName = Repo('..').head.commit.hexsha
        versionText = versionNumber if (branchName == 'master') else branchName

        self.setWindowTitle('WillowGUI (%s)' % versionText)
        self.setWindowIcon(QtGui.QIcon('../img/round_logo_60x60.png'))
        #self.resize(400,200)
        self.center()

        ###
        try:
            self.startDaemon()
            self.msgLog.post('Daemon started.')
        except DaemonMissingError as e:
            self.msgLog.post('Path to daemon does not exist: %s' % e.path)

        try:
            hwif.init()
            self.msgLog.post('HWIF initialized.')
        except (ImportError, socket.error) as e:
            self.msgLog.post('Could not initialize HWIF.')

        self.statusBar.initializeWatchdog()

    def startDaemon(self):
        daemonPath = os.path.join(config.daemonDir, 'build/leafysd')
        if os.path.exists(daemonPath):
            self.daemonProcess = subprocess.Popen([daemonPath, '-N', '-A', '192.168.1.2',
                                                    '-I', config.networkInterface],
                                                    stdout=oFile, stderr=eFile)
        else:
            raise DaemonMissingError(daemonPath)

    def exit(self):
        print 'Cleaning up, then exiting..'
        if self.debugFlag:
            self.packageLogs()
        self.statusBar.watchdogThread.terminate()

    def center(self):
        windowCenter = self.frameGeometry().center()
        screenCenter = QtGui.QDesktopWidget().availableGeometry().center()
        self.move(screenCenter-windowCenter)

    def packageLogs(self):
        log_dir = '../log/'
        for log in self.msgLog.backlogs:
            self.msgLog.logWrite(log, log_dir+log.objectName.lower())
        vitalsLogFilename = log_dir+'/vitals'
        self.statusBar.writeVitalsLog(vitalsLogFilename)
        dt = datetime.datetime.fromtimestamp(time.time())
        zipFilename = str(QtGui.QFileDialog.getSaveFileName(self, 'Save Zipped logs', '../log/logs_from_%02d-%02d-%04d_%02d:%02d:%02d.zip' % (dt.month, dt.day, dt.year, dt.hour, dt.minute, dt.second)))
        if zipFilename:
            with zipfile.ZipFile(zipFilename, 'w') as f:
                for log in self.msgLog.backlogs:
                    f.write(log_dir+log.objectName.lower())
                f.write('../log/oFile')
                f.write('../log/eFile')
        self.msgLog.post('Saved debugging logs to {0}'.format(zipFilename))
