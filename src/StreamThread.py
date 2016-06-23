from PyQt4 import QtCore, QtGui
import sys, os, h5py, subprocess
import numpy as np
import hwif
from WillowDataset import WillowDataset
import config

class StreamThread(QtCore.QThread):

    msgPosted = QtCore.pyqtSignal(str)
    
    def __init__(self, script_name):
        QtCore.QThread.__init__(self)

        self.script_name = script_name

        self.script_dir = os.path.join(config.streamAnalysisDir, self.script_name)
        self.exec_path = os.path.join(self.script_dir, 'main')

        self.oFile = open(os.path.join(self.script_dir, 'oFile'), 'w')
        self.eFile = open(os.path.join(self.script_dir, 'eFile'), 'w')

    def run(self):
        self.proto2bytes_path = os.path.join(config.daemonDir, 'build/proto2bytes')
        self.streamProcess = subprocess.Popen([self.exec_path, self.proto2bytes_path],
                cwd=self.script_dir, stdout=self.oFile, stderr=self.eFile)
        self.msgPosted.emit('Subprocess %s spawned. Streaming widget running now...' %
                            self.script_name) 
        self.streamProcess.wait() 
        self.returncode = self.analysisProcess.returncode
        self.msgPosted.emit('Subprocess %s completed with return code %d. Output saved in %s and %s' %
                            (self.script_name, self.returncode,
                            os.path.relpath(self.oFile.name, config.streamAnalysisDir),
                            os.path.relpath(self.eFile.name, config.streamAnalysisDir)))
