#!/usr/bin/env python

"""
Willow Control Panel GUI

Chris Chronopoulos (chrono@leaflabs.com) - 20140522
"""

import sys, os, subprocess

from PyQt4 import QtCore, QtGui

# change workdir to src/
os.chdir(os.path.dirname(os.path.realpath(__file__)))


if not os.path.isdir('../log'):
    os.mkdir('../log')
oFile = open('../log/oFile', 'w')
eFile = open('../log/eFile', 'w')

class StdOutLogger(object):
    def __init__(self, filename = '../log/stdoutAndStderrCopy'):
        self.terminal = sys.stdout
        if os.path.isfile(filename):
            os.remove(filename)
        self.log = open(filename, 'a')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

if __name__=='__main__':
    subprocess.call(['killall', 'leafysd'])
    subprocess.call(['killall', 'proto2bytes'])
    import argparse
    parser = argparse.ArgumentParser(description='Run the GUI for the Willow.')
    parser.add_argument('-d', '--debug', action='store_true',
    help='display sometimes-gratuitously verbose output about actions taken in GUI to make clearer debugging reports')
    args = parser.parse_args()
    print 'PID = %d' % os.getpid()
    # save standard out to '../log/stdoutCopy' as well as printing to terminal
    sys.stdout = StdOutLogger()
    sys.stderr = sys.stdout
    app = QtGui.QApplication(sys.argv)
    if os.path.exists('config.json'):
        import config
        config.updateAttributes(config.loadJSON())
        from MainWindow import MainWindow
        main = MainWindow(args.debug)
        main.show()
        app.exec_()
        main.exit()
    else:
        print 'config.json does not exist; launching wizard..'
        from ConfigWizard import ConfigWizard
        wizard = ConfigWizard(args.debug)
        wizard.show()
        app.exec_()
        if wizard.mainWindow:
            wizard.mainWindow.exit()

