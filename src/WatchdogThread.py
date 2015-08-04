from PyQt4 import QtCore, QtGui
import sys, os, h5py, time
import numpy as np
import hwif

import time

class WatchdogThread(QtCore.QThread):

    vitalsChecked = QtCore.pyqtSignal(dict)
    vitalsDifferent = QtCore.pyqtSignal(dict)

    def __init__(self):
        super(WatchdogThread, self).__init__()

        self.old_vitals = None
        self.vitals = None

    def run(self):
        time.sleep(1)
        # doesn't need try/except because it's the watchdog
        if self.vitals is not None:
            self.old_vitals = self.vitals.copy()
        self.vitals = hwif.checkVitals()
        self.vitalsChecked.emit(self.vitals)
        if self.vitals != self.old_vitals:
            self.vitalsDifferent.emit(self.vitals)
