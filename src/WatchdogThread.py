from PyQt4 import QtCore, QtGui
import sys, os, h5py, time
import numpy as np
import hwif

class WatchdogThread(QtCore.QThread):

    vitalsChecked = QtCore.pyqtSignal(dict)

    def __init__(self):
        super(WatchdogThread, self).__init__()

        self.old_vitals = None
        self.vitals = None

    def run(self):
        time.sleep(1)
        # doesn't need try/except because it's the watchdog
        self.vitals = hwif.checkVitals()
        self.vitalsChecked.emit(self.vitals)
