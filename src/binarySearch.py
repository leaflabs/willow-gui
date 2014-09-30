#!/usr/bin/python

import os, h5py, time, sys
from parameters import DAEMON_DIR, DATA_DIR


sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

ERRORS = {0:'NO_DNODE', 1:'DAEMON', 6:'DAEMON_IO', 8:'C_VALUE', 2:'C_PROTO',
            3:'D_PROTO', 4:'DNODE', 5:'DNODE_ASYNC', 7:'DNODE_DIED'}
STATUS = {1:'DONE', 2:'ERROR', 3:'PKTDROP', 4:'TIMEOUT'}

def getExperimentCookie(bsi):
    cmd = ControlCommand(type=ControlCommand.STORE)
    cmd.store.start_sample = bsi
    cmd.store.nsamples = 1
    cmd.store.backend = STORE_HDF5
    cmd.store.path = os.path.join(os.getcwd(), 'tmp.h5')
    ###
    resp = do_control_cmd(cmd)
    if resp.type==1:
        print 'ControlCommand failed with Error Code %d: %s' % (resp.err.code, ERRORS[resp.err.code])
        return -1
    elif resp.type==3:
        if resp.store.status==1:
            f = h5py.File('tmp.h5')
            dset = f['wired-dataset']
            ck = dset.attrs.get('experiment_cookie')[0]
            f.close()
            return ck
        else:
            print 'ControlCommand failed with Status Code %d: %s' % (resp.store.status, STATUS[resp.store.status])
            return -1
    else:
        print 'Something weird happened'
        return -1


def queryDisk(bsi, verbose=False):
    """
    A generalization of getExperimentCookie():
    Query the disk at board sample index bsi
    If there's a board sample there, return the experiment cookie
    If there's not, return 0
    If something else goes wrong, return -1
    """
    cmd = ControlCommand(type=ControlCommand.STORE)
    cmd.store.start_sample = bsi
    cmd.store.nsamples = 1
    cmd.store.backend = STORE_HDF5
    cmd.store.path = os.path.join(os.getcwd(), 'tmp.h5')
    ###
    resp = do_control_cmd(cmd)
    if resp.type==1:
        if verbose: print 'ControlCommand failed with Error Code %d: %s' % (resp.err.code, ERRORS[resp.err.code])
        return -1
    elif resp.type==3:
        if resp.store.status==1:
            # board sample found
            f = h5py.File('tmp.h5')
            dset = f['wired-dataset']
            ck = dset.attrs.get('experiment_cookie')[0]
            f.close()
            return ck
        else:
            # board sample NOT found
            if verbose: print 'ControlCommand failed with Status Code %d: %s' % (resp.store.status, STATUS[resp.store.status])
            return 0
    else:
        print 'Something weird happened'
        return -1


def findExperimentBoundary(cookie, leftBracket, rightBracket):
    print leftBracket, rightBracket
    if (rightBracket-leftBracket)==1:
        return leftBracket
    else:
        newBracket = (leftBracket+rightBracket)//2
        result = queryDisk(newBracket)
        if result==cookie:
            leftBracket = newBracket
        else:
            rightBracket = newBracket
        return findExperimentBoundary(cookie, leftBracket, rightBracket)

def findExperimentBoundary_pbar(cookie, leftBracket, rightBracket, pbar, step):
    """
    pbar is the progressbar object
    step gets incremented with each recursion
    """
    if (rightBracket-leftBracket)==1:
        return leftBracket
    else:
        newBracket = (leftBracket+rightBracket)//2
        result = queryDisk(newBracket)
        if result==cookie:
            leftBracket = newBracket
        else:
            rightBracket = newBracket
        pbar.setValue(step)
        return findExperimentBoundary_pbar(cookie, leftBracket, rightBracket, pbar, step+1)

if __name__=='__main__':
    cookie = getExperimentCookie(0)
    boundary = findExperimentBoundary(cookie, 0, int(125e6))
    #boundary = findExperimentBoundary(cookie, 0, 60000)
    if boundary>0:
        print 'Boundary for experiment %d occurs at BSI = %d' % (cookie, boundary)
