from PyQt4 import QtCore
import os, subprocess
import config

class SnapshotAnalysisThread(QtCore.QThread):

    msgPosted = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(object)

    def __init__(self, params):
        QtCore.QThread.__init__(self)
        self.params = params

        self.filename = params['filename']
        self.scriptName = params['whenFinished'][1]

        self.cwd = os.path.join(config.analysisDir, self.scriptName)
        self.execPath = os.path.join(self.cwd, 'main')

        self.oFile = open(os.path.join(self.cwd, 'oFile'), 'w')
        self.eFile = open(os.path.join(self.cwd, 'eFile'), 'w')

    def run(self):
        self.analysisProcess = subprocess.Popen([self.execPath, self.filename], cwd=self.cwd,
                                    stdout=self.oFile, stderr=self.eFile)
        self.analysisProcess.wait()
        self.returncode = self.analysisProcess.returncode
        self.msgPosted.emit('Subprocess %s completed with return code %d. Output saved in %s and %s' %
                            (self.scriptName, self.returncode,
                            os.path.relpath(self.oFile.name, config.analysisDir),
                            os.path.relpath(self.eFile.name, config.analysisDir)))
