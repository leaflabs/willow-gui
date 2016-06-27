from PyQt4 import QtCore, QtGui
import sys, os, h5py, subprocess
import numpy as np
import hwif
from WillowDataset import WillowDataset
import config

class StreamHandler(QtCore.QObject):

    msgPosted = QtCore.pyqtSignal(str)
    
    def __init__(self, script_name):
        super(StreamHandler, self).__init__()

        self.script_name = script_name

        self.script_dir = os.path.join(config.streamAnalysisDir, self.script_name)
        self.exec_path = os.path.join(self.script_dir, 'main')

        self.oFile = open(os.path.join(self.script_dir, 'oFile'), 'w')
        #self.oFile.close()
        #self.oFile = open(os.path.join(self.script_dir, 'oFile'), 'a')
        self.eFile = open(os.path.join(self.script_dir, 'eFile'), 'w')
        #self.eFile.close()
        #self.eFile = open(os.path.join(self.script_dir, 'eFile'), 'a')

        self.streamProcess = QtCore.QProcess(self)
        self.streamProcess.readyReadStandardError.connect(self.routeStdErr)
        self.streamProcess.readyReadStandardOutput.connect(self.routeStdOut)

    def run(self):
        self.killDaemon()
        self.proto2bytes_path = os.path.join(config.daemonDir, 'build/proto2bytes')
        #self.streamProcess = subprocess.Popen([self.exec_path, self.proto2bytes_path],
        #        cwd=self.script_dir, stdout=self.oFile, stderr=self.eFile)
        self.streamProcess.start(self.exec_path, [os.getcwd()])
        self.msgPosted.emit('Subprocess %s spawned. Streaming widget running now...' %
                            self.script_name) 
        #self.streamProcess.wait() 
        #self.returncode = self.analysisProcess.returncode
        #self.msgPosted.emit('Subprocess %s completed with return code %d. Output saved in %s and %s' %
        #                    (self.script_name, self.returncode,
        #                    os.path.relpath(self.oFile.name, config.streamAnalysisDir),
        #                    os.path.relpath(self.eFile.name, config.streamAnalysisDir)))
    def killDaemon(self):
        subprocess.call(['killall', 'leafysd'])
        self.msgPosted.emit('Daemon killed.')
        print 'daemon killed'

    def routeStdErr(self):
        self.oFile.write(str(self.streamProcess.readAllStandardError()))

    def routeStdOut(self):
        out = str(self.streamProcess.readAllStandardOutput())
        self.oFile.write(out)
        self.msgPosted.emit('From subprocess {0}: {1}'.format(self.script_name, out))
