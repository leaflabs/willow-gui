#!/usr/bin/env python

"""
Willow Control Panel GUI

Chris Chronopoulos (chrono@leaflabs.com) - 20140522
"""

import sys, os, signal
from PyQt4 import QtCore, QtGui

# change workdir to src/
os.chdir(os.path.dirname(os.path.realpath(__file__)))

if __name__=='__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtGui.QApplication(sys.argv)
    if os.path.exists('config.json'):
        import config
        config.updateAttributes(config.loadJSON())
        from MainWindow import MainWindow
        main = MainWindow()
        main.show()
    else:
        print 'config.json does not exist, launching wizard..'
        from ConfigWizard import ConfigWizard
        wizard = ConfigWizard()
        wizard.show()
    app.exec_()
