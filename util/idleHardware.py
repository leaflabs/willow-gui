#!/usr/bin/python

import subprocess, os, time
import hwif
import CustomExceptions as ex
from parameters import DAEMON_DIR, DATA_DIR

def startDaemon():
    subprocess.call(['killall', 'leafysd'])
    daemonProcess = subprocess.Popen([os.path.join(DAEMON_DIR, 'build/leafysd'),
                                            '-N', '-A', '192.168.1.2', '-I', 'eth0'])
    time.sleep(2)
    print 'Daemon started.'
    return daemonProcess

if __name__=='__main__':

    daemonProcess = startDaemon()
    time.sleep(1)
    hwif.init()
    try:
        hwif.stopStreaming()
        hwif.stopRecording()
    except ex.AlreadyError:
        pass
    daemonProcess.kill()
