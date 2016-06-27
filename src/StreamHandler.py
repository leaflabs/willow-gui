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
        self.eFile = open(os.path.join(self.script_dir, 'eFile'), 'w')

        self.streamProcess = QtCore.QProcess(self)
        self.streamProcess.readyReadStandardError.connect(self.routeStdErr)
        self.streamProcess.readyReadStandardOutput.connect(self.routeStdOut)

        # For parsing self.streamProcess's requests for hwif calls. Maps
        # from strings representing functions to the functions themselves,
        # and functions for converting other arguments from strings back into
        # real Python types (if applicable)
        self.hwif_calls = {
            'setSubsamples_byChip' : [hwif.setSubsamples_byChip, int],
            'startStreaming_subsamples' : [hwif.startStreaming_subsamples],
            'stopStreaming': [hwif.stopStreaming]
            }

    def run(self):
        proto2bytes_path = os.path.abspath(os.path.join( \
            config.daemonDir, 'build/proto2bytes'))
        self.streamProcess.start(self.exec_path, QtCore.QStringList(proto2bytes_path))
        self.msgPosted.emit('Subprocess %s spawned. Streaming widget running now...' %
                            self.script_name) 
        #self.returncode = self.analysisProcess.returncode
        #self.msgPosted.emit('Subprocess %s completed with return code %d. Output saved in %s and %s' %
        #                    (self.script_name, self.returncode,
        #                    os.path.relpath(self.oFile.name, config.streamAnalysisDir),
        #                    os.path.relpath(self.eFile.name, config.streamAnalysisDir)))
    def routeStdErr(self):
        err = str(self.streamProcess.readAllStandardError())
        self.eFile.write(err)
        # for debugging
        print 'from subprocess: ' + err
        request_prepend = 'hwif_req: '
        if err[:len(request_prepend)] == request_prepend:
            # translate requested function from a str into a Python function
            request = err[len(request_prepend):].split(', ')
            s_fun, s_args = request[0], request[1:]
            call, unstringifiers = self.hwif_calls[s_fun][0], self.hwif_calls[s_fun][1:]
            # call the function with any remaining arguments
            real_args = []
            for i in xrange(len(s_args)):
                real_args.append(unstringifiers[i](s_args[i]))
            call(*real_args)

    def routeStdOut(self):
        out = str(self.streamProcess.readAllStandardOutput())
        self.oFile.write(out)
