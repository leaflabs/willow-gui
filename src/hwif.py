"""
hwif.py (hwif = HardWare InterFace)
created by Chris Chronopoulos on 20141109 
These functions interface with the Willow hardware, accounting for state,
and raising informative exceptions when things go wrong.
"""

import sys, os, socket
import time

from PyQt4 import QtCore

from parameters import *
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

import CustomExceptions as ex

def init():
    global DAEMON_SOCK, DAEMON_MUTEX
    DAEMON_SOCK = get_daemon_control_sock(retry=True, max_retries=100)
    DAEMON_MUTEX = QtCore.QMutex()
    print 'hwif initialized'

def isStreaming():
    mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
    resp = do_control_cmd(reg_read(MOD_DAQ, DAQ_UDP_ENABLE), control_socket=DAEMON_SOCK)
    if resp:
        if resp.type==ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]
    else:
        raise ex.NoResponseError
    return resp.reg_io.val == 1

def isRecording():
    mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
    resp = do_control_cmd(reg_read(MOD_DAQ, DAQ_SATA_ENABLE), control_socket=DAEMON_SOCK)
    if resp:
        if resp.type==ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]
    else:
        raise ex.NoResponseError
    return resp.reg_io.val == 3

def getSampleType():
    val = doRegRead(MOD_DAQ, DAQ_UDP_MODE)
    if val == 0:
        return 'subsample'
    elif val == 1:
        return 'boardsample'
    else:
        return -1

def setSubsamples_byChip(chip):
    """
    Right now proto2bytes only allows subsample channels to all be on one chip
    (or one channel across all chips).
    But you can configure the subsamples manually through the reg_writes.
    Eventually, if proto2bytes is modified (or we used a different method for streaming),
    one could imagine cherrypicking the subsamples one by one.
    """
    chipchanList = [(chip, chan) for chan in range(32)]
    cmds = []
    for i,chipchan in enumerate(chipchanList):
        chip = chipchan[0] & 0b00011111
        chan = chipchan[1] & 0b00011111
        cmds.append(reg_write(MOD_DAQ, DAQ_SUBSAMP_CHIP0+i,
                       (chip << 8) | chan))
    mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
    resps = do_control_cmds(cmds, control_socket=DAEMON_SOCK)
    for resp in resps:
        if resp:
            if resp.type==ControlResponse.ERR:
                raise ex.ERROR_DICT[resp.err.code]
        else:
            raise ex.NoResponseError

def startStreaming_subsamples():
    if isStreaming():
        raise ex.AlreadyError
    else:
        cmd = ControlCommand(type=ControlCommand.FORWARD)
        cmd.forward.sample_type = BOARD_SUBSAMPLE
        cmd.forward.force_daq_reset = not isRecording() # if recording, then DAQ is already running
        aton = socket.inet_aton(DEFAULT_FORWARD_ADDR)   # TODO should this have its own exception?
        cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
        cmd.forward.dest_udp_port = DEFAULT_FORWARD_PORT
        cmd.forward.enable = True
        mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
        resp = do_control_cmd(cmd, control_socket=DAEMON_SOCK)
        if resp:
            if resp.type==ControlResponse.ERR:
                raise ex.ERROR_DICT[resp.err.code]
        else:
            raise ex.NoResponseError

def startStreaming_boardsamples():
    if isStreaming():
        raise ex.AlreadyError
    else:
        cmd = ControlCommand(type=ControlCommand.FORWARD)
        cmd.forward.sample_type = BOARD_SAMPLE
        cmd.forward.force_daq_reset = not isRecording() # if recording, then DAQ is already running
        aton = socket.inet_aton(DEFAULT_FORWARD_ADDR)   # TODO should this have its own exception?
        cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
        cmd.forward.dest_udp_port = DEFAULT_FORWARD_PORT
        cmd.forward.enable = True
        mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
        resp = do_control_cmd(cmd, control_socket=DAEMON_SOCK)
        if resp:
            if resp.type==ControlResponse.ERR:
                raise ex.ERROR_DICT[resp.err.code]
        else:
            raise ex.NoResponseError

def stopStreaming():
    if not isStreaming():
        raise ex.AlreadyError
    else:
        cmds = []
        cmd = ControlCommand(type=ControlCommand.FORWARD)
        cmd.forward.enable = False
        cmds.append(cmd)
        if not isRecording():
            cmd = ControlCommand(type=ControlCommand.ACQUIRE)
            cmd.acquire.enable = False
            cmds.append(cmd)
        mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
        resps = do_control_cmds(cmds, control_socket=DAEMON_SOCK)
        for resp in resps:
            if resp:
                if resp.type==ControlResponse.ERR:
                    raise ex.ERROR_DICT[resp.err.code]
            else:
                raise ex.NoResponseError

def startRecording():
    if isRecording():
        raise ex.AlreadyError
    else:
        wasStreaming = isStreaming()
        cmds = []
        if wasStreaming:
            # temporarily turn off streaming (expect a blip in the stream)
            cmd = ControlCommand(type=ControlCommand.FORWARD)
            cmd.forward.enable = False
            cmds.append(cmd)
        cmd = ControlCommand(type=ControlCommand.ACQUIRE)
        cmd.acquire.exp_cookie = long(time.time())
        cmd.acquire.start_sample = 0
        cmd.acquire.enable = True
        cmds.append(cmd)
        if wasStreaming:
            # turn streaming back on again
            cmd = ControlCommand(type=ControlCommand.FORWARD)
            cmd.forward.sample_type = BOARD_SUBSAMPLE
            cmd.forward.force_daq_reset = False
            aton = socket.inet_aton(DEFAULT_FORWARD_ADDR)   # TODO should this have its own exception?
            cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
            cmd.forward.dest_udp_port = DEFAULT_FORWARD_PORT
            cmd.forward.enable = True
            cmds.append(cmd)
        mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
        resps = do_control_cmds(cmds, control_socket=DAEMON_SOCK)
        for resp in resps:
            if resp:
                if resp.type==ControlResponse.ERR:
                    raise ex.ERROR_DICT[resp.err.code]
            else:
                raise ex.NoResponseError

def stopRecording():
    if not isRecording():
        raise ex.AlreadyError
    else:
        wasStreaming = isStreaming()
        cmds = []
        cmd = ControlCommand(type=ControlCommand.ACQUIRE)
        cmd.acquire.enable = False
        cmds.append(cmd)
        if wasStreaming:
            # turn streaming back on again
            cmd = ControlCommand(type=ControlCommand.FORWARD)
            cmd.forward.sample_type = BOARD_SUBSAMPLE
            cmd.forward.force_daq_reset = True
            aton = socket.inet_aton(DEFAULT_FORWARD_ADDR) # TODO should this have its own exception?
            cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
            cmd.forward.dest_udp_port = DEFAULT_FORWARD_PORT
            cmd.forward.enable = True
            cmds.append(cmd)
        mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
        resps = do_control_cmds(cmds, control_socket=DAEMON_SOCK)
        for resp in resps:
            if resp:
                if resp.type==ControlResponse.ERR:
                    raise ex.ERROR_DICT[resp.err.code]
            else:
                raise ex.NoResponseError

def takeSnapshot(nsamples, filename):
    cmds = []
    if isStreaming():
        sampleType = getSampleType()
        if sampleType == 'boardsample':
            cmd = ControlCommand(type=ControlCommand.STORE)
            cmd.store.path = filename
            cmd.store.nsamples = nsamples
            cmds.append(cmd)
        elif sampleType == 'subsample':
            raise ex.StateChangeError   #TODO implement a work-around for this
        else:
            print 'unrecognized sample type received!'
    elif isRecording():
        # if not streaming, but recording...
        cmd = ControlCommand(type=ControlCommand.STORE)
        cmd.store.path = filename
        cmd.store.nsamples = nsamples
        cmds.append(cmd)
        ###
        # need this to turn off daq->udp, otherwise state gets broken
        cmd = ControlCommand(type=ControlCommand.FORWARD)
        cmd.forward.enable = False
        cmds.append(cmd)
    else:
        # if idle...
        cmd = ControlCommand(type=ControlCommand.FORWARD)
        cmd.forward.sample_type = BOARD_SAMPLE
        cmd.forward.force_daq_reset = True
        aton = socket.inet_aton(DEFAULT_FORWARD_ADDR) # TODO should this be its own exception?
        cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
        cmd.forward.dest_udp_port = DEFAULT_FORWARD_PORT
        cmd.forward.enable = True
        cmds.append(cmd)

        cmd = ControlCommand(type=ControlCommand.STORE)
        cmd.store.path = filename
        cmd.store.nsamples = nsamples
        cmds.append(cmd)

        cmd = ControlCommand(type=ControlCommand.ACQUIRE)
        cmd.acquire.enable = False
        cmds.append(cmd)
    mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
    resps = do_control_cmds(cmds, control_socket=DAEMON_SOCK)
    for resp in resps:
        if resp:
            if resp.type==ControlResponse.ERR:
                raise ex.ERROR_DICT[resp.err.code]
        else:
            raise ex.NoResponseError
    for resp in resps:
        if resp.type==ControlResponse.STORE_FINISHED:
            if resp.store.status==ControlResStore.DONE:
                return resp.store.nsamples
            elif resp.store.status==ControlResStore.PKTDROP:
                return resp.store.nsamples
            else:
                raise Exception('ControlResStore Status: %d' % resp.store.status)

def doTransfer(filename, sampleRange=-1):
    if isStreaming() or isRecording():
        raise ex.StateChangeError
    else:
        cmd = ControlCommand(type=ControlCommand.STORE)
        if (len(sampleRange) == 2) and (sampleRange[1] > sampleRange[0]):
            startSample = sampleRange[0]
            nsamples = sampleRange[1] - sampleRange[0] + 1
            cmd.store.start_sample = startSample
            cmd.store.nsamples = nsamples
        elif sampleRange == -1:
            cmd.store.start_sample = 0
            # leave nsamples missing, which indicates whole experiment
        cmd.store.path = filename
        mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
        resp = do_control_cmd(cmd, control_socket=DAEMON_SOCK)
        if resp:
            if resp.type==ControlResponse.ERR:
                raise ex.ERROR_DICT[resp.err.code]
        else:
            raise ex.NoResponseError


def pingDatanode():
    cmd = ControlCommand(type=ControlCommand.PING_DNODE)
    mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
    resp = do_control_cmd(cmd, control_socket=DAEMON_SOCK)
    if resp:
        if resp.type==ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]
    else:
        raise ex.NoResponseError

def doRegRead(module, address):
    mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
    resp = do_control_cmd(reg_read(module, address), control_socket=DAEMON_SOCK)
    if resp:
        if resp.type == ControlResponse.REG_IO:
            return resp.reg_io.val
        elif resp.type==ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]
    else:
        raise ex.NoResponseError

def doRegWrite(module, address, data):
    resp = do_control_cmd(reg_write(module, address, data), control_socket=DAEMON_SOCK)
    if resp:
        if resp.type==ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]
    else:
        raise ex.NoResponseError

def doIntanRegWrite(address, data):
    """
    Can only write to all chips simultaneously, due to hardware limitations.
    (Can actually write at "headstage resolution", but this isn't particularly useful.)
    """
    address = address & 0b11111
    cmds = []
    cmdData = ((0x1 << 24) |                    # aux command write enable
               (0xFF << 16) |                   # all chips
               ((0b10000000 | address) << 8) | # intan register address
               data)                            # data
    clear = 0
    cmds.append(reg_write(MOD_DAQ, DAQ_CHIP_CMD, cmdData))
    cmds.append(reg_write(MOD_DAQ, DAQ_CHIP_CMD, clear))
    resps = do_control_cmds(cmds, control_socket=DAEMON_SOCK)
    for resp in resps:
        if resp:
            if resp.type==ControlResponse.ERR:
                raise ex.ERROR_DICT[resp.err.code]
        else:
            raise ex.NoResponseError


def checkVitals():
    #TODO catch NoResponseError as well?
    vitals = {} # True means up, False means down, None means unknown
    try:
        pingDatanode()
        vitals['daemon'] = True
        vitals['datanode'] = True
        vitals['firmware'] = doRegRead(MOD_CENTRAL, CENTRAL_GIT_SHA_PIECE)
        vitals['errors'] = doRegRead(MOD_ERR, ERR_ERR0)
        vitals['stream'] = isStreaming()
        vitals['record'] = isRecording()
        return vitals
    except socket.error:
        # cannot connect to daemon
        vitals['daemon'] = False
        vitals['datanode'] = None
        vitals['firmware'] = None
        vitals['errors'] = None
        vitals['stream'] = None
        vitals['record'] = None
        return vitals
    except (ex.NO_DNODE_error, ex.DNODE_DIED_error) as e:
        # datanode is not connected
        vitals['daemon'] = True
        vitals['datanode'] = False
        vitals['firmware'] = None
        vitals['errors'] = None
        vitals['stream'] = None
        vitals['record'] = None
        return vitals
    except ex.DNODE_error:
        # error condition present
        vitals['daemon'] = True
        vitals['datanode'] = True
        vitals['firmware'] = doRegRead(MOD_CENTRAL, CENTRAL_GIT_SHA_PIECE)
        vitals['errors'] = doRegRead(MOD_ERR, ERR_ERR0)
        vitals['stream'] = isStreaming()
        vitals['record'] = isRecording()
        return vitals


