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
        self.streamProcess.setReadChannel(self.streamProcess.StandardError)
        self.readMoreTimer = QtCore.QTimer()
        self.readMoreTimer.setSingleShot(True)
        self.readMoreTimer.timeout.connect(self.routeStdErr)
        self.streamProcess.readyReadStandardError.connect(self.armReadMoreTimer)
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

    def armReadMoreTimer(self):
        self.readMoreTimer.start(0)

    def routeStdErr(self):
        if not self.streamProcess.canReadLine():
            return

        err = str(self.streamProcess.readLine())
        self.eFile.write(err)
        err = err.rstrip()
        request_prepend = 'hwif_req: '
        if err.startswith(request_prepend):
            # translate requested function from a str into a Python function
            request = err[len(request_prepend):].split(', ')
            s_fun, s_args = request[0], request[1:]
            call, unstringifiers = self.hwif_calls[s_fun][0], self.hwif_calls[s_fun][1:]
            # call the function with any remaining arguments
            real_args = [unstringifiers[i](arg) for i, arg in enumerate(s_args)]
            try:
                call(*real_args)
            except hwif.AlreadyError:
                already_message = 'Hardware was already '
                if call == hwif.stopStreaming:
                    already_message = already_message + 'not streaming.'
                elif (call == hwif.startStreaming_subsamples or
                      call == hwif.startStreaming_boardsamples):
                    already_message = already_message + \
                        'streaming. Try stopping and restarting stream.'
                self.msgPosted.emit(already_message)
            except AttributeError:
                # TODO what's up with this?
                self.msgPosted.emit('AttributeError: Pipe object does not exist')
            except hwif.hwifError as e:
                self.msgPosted.emit(e.message)
            else:
                if (call == hwif.startStreaming_subsamples or
                    call == hwif.startStreaming_boardsamples):
                    self.msgPosted.emit('Started streaming.')
                elif call == hwif.stopStreaming:
                    self.msgPosted.emit('Stopped streaming.')
        # in case we didn't get all lines of stream, re-arm timer to call again
        self.armReadMoreTimer()

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
        self.readMoreTimer.stop()
        self.oFile.close()
        self.eFile.close()
        self.msgPosted.emit('Subprocess {0} completed with return code {1} \
            and status {2}. \n Output saved in {3} and {4}.'.format(
            self.script_name, exitCode, exitStatus,
            os.path.relpath(self.oFile.name, config.analysisDirStreaming),
            os.path.relpath(self.eFile.name, config.analysisDirStreaming)))
