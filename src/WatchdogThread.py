from PyQt4 import QtCore, QtGui
import sys, os, h5py, time
import numpy as np
import hwif

import config
sys.path.append(os.path.join(config.daemonDir, 'util'))
from daemon_control import *

class WatchdogThread(QtCore.QThread):

    vitalsChecked = QtCore.pyqtSignal(dict)

    def __init__(self):
        super(WatchdogThread, self).__init__()

    """
    def start(self):
        # for debugging
        super(WatchdogThread, self).start()
        print 'watchdog thread started!'
        raise Exception('wtf')
    """

    def run(self):
        time.sleep(1)
        # doesn't need try/except because it's the watchdog
        vitals = hwif.checkVitals()
        self.vitalsChecked.emit(vitals)
