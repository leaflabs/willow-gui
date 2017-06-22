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

        self.script_dir = os.path.join(config.analysisDirStreaming, self.script_name)
        self.exec_path = os.path.join(self.script_dir, 'main')

        self.oFile = open(os.path.join(self.script_dir, 'oFile'), 'w')
        self.eFile = open(os.path.join(self.script_dir, 'eFile'), 'w')

        self.streamProcess = QtCore.QProcess(self)
        self.streamProcess.readyReadStandardError.connect(self.routeStdErr)
        self.streamProcess.readyReadStandardOutput.connect(self.routeStdOut)
        self.streamProcess.finished.connect(self.streamFinishedHandler)

        # For parsing self.streamProcess's requests for hwif calls. Maps
        # from strings representing functions to the functions themselves,
        # and functions for converting other arguments from strings back into
        # real Python types (if applicable)
        self.hwif_calls = {
            'setSubsamples_byChip' : [hwif.setSubsamples_byChip, int],
            'startStreaming_subsamples' : [hwif.startStreaming_subsamples],
            'startStreaming_boardsamples' : [hwif.startStreaming_boardsamples],
            'stopStreaming': [hwif.stopStreaming]
            }

    def run(self):
        proto2bytes_path = os.path.abspath(os.path.join( \
            config.daemonDir, 'build/proto2bytes'))
        self.streamProcess.start(self.exec_path, QtCore.QStringList(proto2bytes_path))
        self.msgPosted.emit('Subprocess %s spawned. Streaming widget running now...' %
                            self.script_name)
    def routeStdErr(self):
        err = str(self.streamProcess.readAllStandardError())
        commands = err.split("\n")
        self.eFile.write('\n'.join(commands))
        request_prepend = 'hwif_req: '
        for command in commands:
            if command[:len(request_prepend)] == request_prepend:
                # translate requested function from a str into a Python function
                request = command[len(request_prepend):].split(', ')
                s_fun, s_args = request[0], request[1:]
                call, unstringifiers = self.hwif_calls[s_fun][0], self.hwif_calls[s_fun][1:]
                # call the function with any remaining arguments
                real_args = []

                # TODO maybe handle potential hwif calls and errors more selectively
                for i in xrange(len(s_args)):
                    real_args.append(unstringifiers[i](s_args[i]))
                try:
                    call(*real_args)
                    if call == hwif.startStreaming_subsamples:
                        self.msgPosted.emit('Started streaming.')
                    elif call == hwif.stopStreaming:
                        self.msgPosted.emit('Stopped streaming.')
                    pass
                except hwif.AlreadyError:
                    already_message = 'Hardware was already '
                    if call == hwif.stopStreaming:
                        already_message = already_message + 'not streaming.'
                    elif (call == hwif.startStreaming_subsamples or
                          call == hwif.startStreaming_boardsamples):
                        already_message = already_message + \
                            'streaming. Try stopping and restarting stream.'
                    print already_message
                    pass
                except AttributeError:
                    # TODO what's up with this?
                    print 'AttributeError: Pipe object does not exist'
                    pass
                except hwif.hwifError as e:
                    print e.message
                    pass

    def routeStdOut(self):
        out = str(self.streamProcess.readAllStandardOutput())
        self.oFile.write(out)

    def streamFinishedHandler(self, exitCode, exitStatus):
        try:
            hwif.stopStreaming()
        except hwif.AlreadyError:
            pass
        except hwif.hwifError as e:
            self.msgPosted.emit("streamFinishedHandler: %s" % e.message)
            pass
        self.msgPosted.emit('Subprocess {0} completed with return code {1} \
            and status {2}. \n Output saved in {3} and {4}.'.format(
            self.script_name, exitCode, exitStatus,
            os.path.relpath(self.oFile.name, config.analysisDirStreaming),
            os.path.relpath(self.eFile.name, config.analysisDirStreaming)))
