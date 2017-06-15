from PyQt4 import QtCore, QtGui
import sys, os, h5py, time
import numpy as np
import hwif

class WatchdogThread(QtCore.QThread):

    vitalsChecked = QtCore.pyqtSignal(dict)
    statusUpdated = QtCore.pyqtSignal(str)

    def __init__(self):
        super(WatchdogThread, self).__init__()

        self.old_vitals = None
        self.vitals = None

        self.running = False

    def run(self):
        self.running = True
        while self.running:
            try:
                self.vitals = hwif.checkVitals()
                self.vitalsChecked.emit(self.vitals)
                time.sleep(1)
            except hwif.hwifError as e:
                self.statusUpdated.emit(e.message)
                self.running = False
