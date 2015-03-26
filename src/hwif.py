"""
hwif.py (hwif = HardWare InterFace)

These functions interface with the Willow hardware, accounting for state,
synchronizing between threads, and raising informative exceptions when things
go wrong.

This module represents an abstraction boundary between the GUI callbacks and the
protobuf interface: hwif functions are high-level in the sense that their caller
should be thinking about actions being taken, not reg_reads and reg_writes.

Before using, first start the daemon, then do:

import hwif
hwif.init()

Functions in this module perform socket communication with the daemon (ControlCmd's),
so they can fail in predictable ways. These are encapsulated in _controlCmdWrapper(),
which recognizes these failures and raises hwifError with an informative message.
So basic usage of these functions looks like:

try:
    hwif.startRecording()
except hwif.hwifError as e:
    msgLog.post(e.message)

Some hwif functions can raise other custom Exceptions, which are explained in
their docstrings.

Chris Chronopoulos (chrono@leaflabs.com) - 20150306
"""

import sys, os, socket
import time, struct

from PyQt4 import QtCore

import config

sys.path.append(os.path.join(config.daemonDir, 'util'))
import daemon_control as dc

def init():
    global DAEMON_SOCK, DAEMON_MUTEX
    DAEMON_SOCK = dc.get_daemon_control_sock(retry=True, max_retries=200)
    DAEMON_MUTEX = QtCore.QMutex()
    print 'hwif initialized'



ERR_MSG = {  dc.ControlResErr.NO_DNODE : 'NO_DNODE: No datanode connected',
                dc.ControlResErr.DAEMON : 'DAEMON: Internal daemon error',
                dc.ControlResErr.DAEMON_IO : 'DAEMON_IO: Daemon I/O error',
                dc.ControlResErr.C_VALUE : 'C_VALUE: Invalid arguments on client control socket',
                dc.ControlResErr.C_PROTO : 'C_PROTO: Protocol error on client control socket',
                dc.ControlResErr.D_PROTO : 'D_Proto: Protocol error on datanode control socket',
                dc.ControlResErr.DNODE : 'DNODE: Datanode transaction failed',
                dc.ControlResErr.DNODE_ASYNC : 'DNODE_ASYNC: Asynchronous datanode error',
                dc.ControlResErr.DNODE_DIED : 'DNODE_DIED: Datanode connection died while processing request'
                }


#
##
###
#### custom exceptions

class StateChangeError(Exception):
    """
    This error indicates that the user has requested a state change that is
    disallowed, given the current state.
    """
    pass

class NoResponseError(Exception):
    """
    This error means that do_control_cmd(cmd) returned None
    This happens when, e.g. trying to do a ControlCommand.STORE with nsamples missing,
    but the DAQ's BSI register is empty (because e.g. the hardware was recently booted).
    (This is a bug in the daemon which needs to be fixed.)
    (It can also happen as a result of the daemon refusing new client connection because
    'another is ongoing')
    """
    pass

class AlreadyError(Exception):
    """
    This error indicates that the user requested a transition into some state,
    but the hardware was already in that state.
    """
    pass

class hwifError(Exception):
    """
    This error can be thrown by any hwif function, it is an umbrella case for I/O exceptions.
    type = 0 means socket.error
    type = 1 means daemon transaction error, and should be accomapnied by an error code
    type = 2 means resp = None, which happens, eg:
        when trying to do a ControlCommand.STORE with nsamples missing,
            but the DAQ's BSI register is empty (because e.g. the hardware was recently booted).
            (This is a bug in the daemon which needs to be fixed.)
        as a result of the daemon refusing new client connection because 'another is ongoing'.
    type = 3 means "miscellaneous", and should be accompanied by a custom message argument
    """
    def __init__(self, type, errcode=None, message=None):
        Exception.__init__(self)
        self.type = type
        if self.type==0:
            self.message = 'Socket Error: could not connect to daemon'
        elif self.type==1:
            self.errcode = errcode
            self.message = ERR_MSG[self.errcode]
        elif self.type==2:
            self.message = 'Control Command got No Response'
        elif self.type==3:
            self.message = message


#
##
###
#### internal (helper) functions

def _controlCmdWrapper(cmd):
    """
    cmd can either be a single dc.ControlCommand, or a list of them
    with return resp or resps, according to the multiplicity of cmd
    may raise hwifError, with type and message attributes
    """
    multiple = isinstance(cmd, list)
    try:
        if multiple:
            with QtCore.QMutexLocker(DAEMON_MUTEX):
                resps = dc.do_control_cmds(cmd, control_socket=DAEMON_SOCK)
            for resp in resps:
                if resp:
                    if resp.type == dc.ControlResponse.ERR:
                        raise hwifError(1, resp.err.code)
                else:
                    raise hwifError(2)
            return resps
        else:
            with QtCore.QMutexLocker(DAEMON_MUTEX):
                resp = dc.do_control_cmd(cmd, control_socket=DAEMON_SOCK)
            if resp:
                if resp.type == dc.ControlResponse.ERR:
                    raise hwifError(1, resp.err.code)
            else:
                raise hwifError(2)
            return resp
    except socket.error:
        raise hwifError(0)


def _isValidSampleRange(sampleRange):
    if isinstance(sampleRange, list) and (len(sampleRange)==2):
        if (sampleRange[1]>sampleRange[0]) and (sampleRange[0]>=0):
            return True
        else:
            return False
    else:
        return False

def _intanRegWrite(clear=False, address=None, data=None):
    """
    Use this to generate a control command for writing to the intan chips.
    Can only write to all chips simultaneously, due to hardware limitations.
    (Can actually write at "headstage resolution", but this isn't particularly useful.)
    Use cmd_clear = _intanRegWrite(clear=True) to generate a clear command.
    """
    if clear:
        cmdData = 0
    else:
        cmdData = ((0x1 << 24) |                    # aux command write enable
                   (0xFF << 16) |                   # all chips
                   ((0b10000000 | address) << 8) | # intan register address
                   data)                            # data
    cmd = dc.reg_write(dc.MOD_DAQ, dc.DAQ_CHIP_CMD, cmdData)
    return cmd

def _doRegRead(module, address):
    mutexLocker = QtCore.QMutexLocker(DAEMON_MUTEX)
    resp = dc.do_control_cmd(dc.reg_read(module, address), control_socket=DAEMON_SOCK)
    if resp:
        if resp.type == dc.ControlResponse.REG_IO:
            return resp.reg_io.val
        elif resp.type==dc.ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]
    else:
        raise ex.NoResponseError


#
##
###
#### public functions

def isStreaming():
    """
    Returns True if hardware is streaming, False otherwise.
    """
    cmd = dc.reg_read(dc.MOD_DAQ, dc.DAQ_UDP_ENABLE)
    resp = _controlCmdWrapper(cmd)
    return resp.reg_io.val == 1

def isRecording():
    """
    Returns True if hardware is recording, False otherwise.
    """
    cmd = dc.reg_read(dc.MOD_DAQ, dc.DAQ_SATA_ENABLE)
    resp = _controlCmdWrapper(cmd)
    return resp.reg_io.val == 3

def getSataBSI():
    """
    Returns BSI of last SATA write.
    """
    cmd = dc.reg_read(dc.MOD_SATA, dc.SATA_W_IDX)
    resp = _controlCmdWrapper(cmd)
    return resp.reg_io.val

def getDaqBSI():
    """
    Returns BSI of last DAQ transaction.
    """
    cmd = dc.reg_read(dc.MOD_DAQ, dc.DAQ_BSMP_CURR)
    resp = _controlCmdWrapper(cmd)
    return resp.reg_io.val

def getSampleType():
    """
    Returns streaming type: 'boardsample' or 'subsample'
    """
    cmd = dc.reg_read(dc.MOD_DAQ, dc.DAQ_UDP_MODE)
    resp = _controlCmdWrapper(cmd)
    val = resp.reg_io.val
    if val == 0:
        return 'subsample'
    elif val == 1:
        return 'boardsample'
    else:
        return 'unknown'

def getChipsAlive():
    """
    Returns a list of indices of live Intan chips, by reading the bitmask in
        hardware register (3,4)
    WARNING: This bitmask will be inaccurate upon startup, until the DAQ is run.
        This is an HDL bug, see ticket Willow-94.
    """
    cmd = dc.reg_read(dc.MOD_DAQ, dc.DAQ_CHIP_ALIVE)
    resp = _controlCmdWrapper(cmd)
    mask = resp.reg_io.val
    return [i for i in range(32) if (mask & (0x1 << i))]

def setSubsamples_byChip(chip):
    """
    Set the subsample channels by chip. 
    Right now proto2bytes only allows subsample channels to all be on one chip
    (or one channel across all chips).
    Eventually, if proto2bytes is modified (or we used a different method for streaming),
    then potentially you could cherrypick the subsamples one by one.
    """
    chipchanList = [(chip, chan) for chan in range(32)]
    cmds = []
    for i,chipchan in enumerate(chipchanList):
        chip = chipchan[0] & 0b00011111
        chan = chipchan[1] & 0b00011111
        cmds.append(dc.reg_write(dc.MOD_DAQ, dc.DAQ_SUBSAMP_CHIP0 + i, (chip << 8) | chan))
    resps = _controlCmdWrapper(cmds)

def startStreaming_subsamples():
    """
    Start streaming subsamples.
    Appropriate for streaming via proto2bytes.
    Make sure to call setSubsamples_byChip() before starting streaming.
    """
    if isStreaming():
        raise AlreadyError
    else:
        cmd = dc.ControlCommand(type=dc.ControlCommand.FORWARD)
        cmd.forward.sample_type = dc.BOARD_SUBSAMPLE
        cmd.forward.force_daq_reset = not isRecording() # if recording, then DAQ is already running
        aton = socket.inet_aton(config.defaultForwardAddr)
        cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
        cmd.forward.dest_udp_port = config.defaultForwardPort
        cmd.forward.enable = True
        resp = _controlCmdWrapper(cmd)

def startStreaming_boardsamples():
    """
    Start streaming boardsamples.
    Useful for running the DAQ during impedance testing while setting zcheck params.
    Although, there may be a more direct way to accomplish this (new recipe?)
    """
    if isStreaming():
        raise AlreadyError
    else:
        cmd = dc.ControlCommand(type=dc.ControlCommand.FORWARD)
        cmd.forward.sample_type = dc.BOARD_SAMPLE
        cmd.forward.force_daq_reset = not isRecording() # if recording, then DAQ is already running
        aton = socket.inet_aton(config.defaultForwardAddr)
        cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
        cmd.forward.dest_udp_port = config.defaultForwardPort
        cmd.forward.enable = True
        resp = _controlCmdWrapper(cmd)

def stopStreaming():
    """
    Stop streaming, both from datanode to daemon, and from daemon to proto2bytes
    """
    if not isStreaming():
        raise AlreadyError
    else:
        cmds = []
        cmd = dc.ControlCommand(type=dc.ControlCommand.FORWARD)
        cmd.forward.enable = False
        cmds.append(cmd)
        if not isRecording():
            cmd = dc.ControlCommand(type=dc.ControlCommand.ACQUIRE)
            cmd.acquire.enable = False
            cmds.append(cmd)
        resps = _controlCmdWrapper(cmds)

def startRecording():
    """
    Start recording (acquiring) to disk.
    Willow only supports contiguous recordings that start at beginning of disk.
    If already recording, this will raise AlreadyError.
    If already streaming, this will work, but expect a blip in the stream.
    """
    if isRecording():
        raise AlreadyError
    else:
        wasStreaming = isStreaming()
        cmds = []
        if wasStreaming:
            # temporarily turn off streaming
            cmd = dc.ControlCommand(type=dc.ControlCommand.FORWARD)
            cmd.forward.enable = False
            cmds.append(cmd)
        cmd = dc.ControlCommand(type=dc.ControlCommand.ACQUIRE)
        cmd.acquire.exp_cookie = long(time.time())
        cmd.acquire.start_sample = 0
        cmd.acquire.enable = True
        cmds.append(cmd)
        if wasStreaming:
            # turn streaming back on again
            cmd = dc.ControlCommand(type=dc.ControlCommand.FORWARD)
            cmd.forward.sample_type = dc.BOARD_SUBSAMPLE
            cmd.forward.force_daq_reset = False
            aton = socket.inet_aton(config.defaultForwardAddr)
            cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
            cmd.forward.dest_udp_port = config.defaultForwardPort
            cmd.forward.enable = True
            cmds.append(cmd)
        resps = _controlCmdWrapper(cmds)


def stopRecording():
    """
    Stop recording to disk.
    If already not recording, this will raise AlreadyError.
    If streaming was enabled, this will persist after a short blip in the stream.
    """
    if not isRecording():
        raise AlreadyError
    else:
        wasStreaming = isStreaming()
        cmds = []
        cmd = dc.ControlCommand(type=dc.ControlCommand.ACQUIRE)
        cmd.acquire.enable = False
        cmds.append(cmd)
        if wasStreaming:
            # turn streaming back on again
            cmd = dc.ControlCommand(type=dc.ControlCommand.FORWARD)
            cmd.forward.sample_type = dc.BOARD_SUBSAMPLE
            cmd.forward.force_daq_reset = True
            aton = socket.inet_aton(config.defaultForwardAddr)
            cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
            cmd.forward.dest_udp_port = config.defaultForwardPort
            cmd.forward.enable = True
            cmds.append(cmd)
        resps = _controlCmdWrapper(cmds)

def takeSnapshot(nsamples, filename):
    """
    Takes a snapshot (aka save_stream) of length nsamples, and saves it to filename, in HDF5 format.
    This will work whether you're streaming, recording, both or neither.
    Returns the actual number of samples captures, as reported by the daemon.
    Due to UDP packet drops, this may be less than the number of samples requested.
    """
    cmds = []
    if isStreaming():
        sampleType = getSampleType()
        if sampleType == 'boardsample':
            cmd = dc.ControlCommand(type=dc.ControlCommand.STORE)
            cmd.store.path = filename
            cmd.store.nsamples = nsamples
            cmds.append(cmd)
        elif sampleType == 'subsample':
            #TODO implement a work-around for this
            raise StateChangeError('Pause streaming before taking snapshot.')   
        else:
            print 'unrecognized sample type received!'
    elif isRecording():
        # if not streaming, but recording...
        cmd = dc.ControlCommand(type=dc.ControlCommand.STORE)
        cmd.store.path = filename
        cmd.store.nsamples = nsamples
        cmds.append(cmd)
        ####
        # need this to turn off daq->udp, otherwise state gets broken
        cmd = dc.ControlCommand(type=dc.ControlCommand.FORWARD)
        cmd.forward.enable = False
        cmds.append(cmd)
    else:
        # if idle...
        cmd = dc.ControlCommand(type=dc.ControlCommand.FORWARD)
        cmd.forward.sample_type = dc.BOARD_SAMPLE
        cmd.forward.force_daq_reset = True
        aton = socket.inet_aton(config.defaultForwardAddr) # TODO should this be its own exception?
        cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
        cmd.forward.dest_udp_port = config.defaultForwardPort
        cmd.forward.enable = True
        cmds.append(cmd)
        ####
        cmd = dc.ControlCommand(type=dc.ControlCommand.STORE)
        cmd.store.path = filename
        cmd.store.nsamples = nsamples
        cmds.append(cmd)
        ####
        cmd = dc.ControlCommand(type=dc.ControlCommand.ACQUIRE)
        cmd.acquire.enable = False
        cmds.append(cmd)
    resps = _controlCmdWrapper(cmds)
    for resp in resps:
        if resp.type==dc.ControlResponse.STORE_FINISHED:
            if resp.store.status==dc.ControlResStore.DONE:
                return resp.store.nsamples
            elif resp.store.status==dc.ControlResStore.PKTDROP:
                return resp.store.nsamples
            else:
                # this shouldn't happen, but..
                raise hwifError(3, message='ControlResStore Status: %d' % resp.store.status)

def doTransfer(filename, sampleRange=None):
    """
    Perform a transfer (aka save_stored), save to filename (HDF5 format).
    If sampleRange is specified, then only transfer BSI's from within that range.
    If sampleRange is not specified or NoneType, transfer the entire experiment.
    WARNING: make sure to check that the DAQ's "Current Board Sample Number" register
        is nonzero (e.g. by using getDaqBSI) before attempting a transfer with
        sampleRange=None, otherwise this will fail and the daemon will crash (which is a bug).
    Only works from an idle state - raises StateChangeError otherwise.
    """
    if isStreaming() or isRecording():
        raise StateChangeError
    else:
        cmd = dc.ControlCommand(type=dc.ControlCommand.STORE)
        if sampleRange:
            if _isValidSampleRange(sampleRange):
                startSample = sampleRange[0]
                nsamples = sampleRange[1] - sampleRange[0]
                cmd.store.start_sample = startSample
                cmd.store.nsamples = nsamples
            else:
                raise hwifError(3, message='sampleRange %s not valid' % repr(sampleRange))
        else:
            cmd.store.start_sample = 0
            # leave nsamples missing, which indicates whole experiment
        cmd.store.path = filename
        resp = _controlCmdWrapper(cmd)

def enableZCheck(chan, capscale):
    """
    Enable Intan impedance testing
    chan is an int between 0 and 31 inclusive
    capscale is either 0b00 (0.1pF), 0b01 (1pF), or 0b11 (10pF)
    Make sure DAQ is running, e.g. by calling startStreaming_boardSamples(), before
        calling this function.
    """
    # first set DAC configuration register
    enable = 0b1
    power = (0b1 << 6)
    scale = (capscale & 0b11) << 3
    settings = (enable | power | scale)
    # then set the DAC channel register
    chan = chan & 0b11111
    ####
    cmds = []
    cmds.append(_intanRegWrite(address=5, data=settings))
    cmds.append(_intanRegWrite(address=7, data=chan))
    cmds.append(_intanRegWrite(clear=True))
    resps = _controlCmdWrapper(cmds)

def disableZCheck():
    """
    Disable Intan impedance testing
    Make sure DAQ is running, e.g. by calling startStreaming_boardSamples(), before
        calling this function.
    """
    """
    cmdData_DACconfig = ((0x1 << 24) |
                        (0xFF << 16) |
                        (0b10000101 << 8) |
                        0) # clear register
    cmdData_DACchan =  ((0x1 << 24) |
                        (0xFF << 16) |
                        (0b10000111 << 8) |
                        0) # clear register
    """
    ####
    cmds = []
    #cmds.append(dc.reg_write(dc.MOD_DAQ, dc.DAQ_CHIP_CMD, cmdData_DACconfig))
    cmds.append(_intanRegWrite(address=5, data=0))
    #cmds.append(dc.reg_write(dc.MOD_DAQ, dc.DAQ_CHIP_CMD, cmdData_DACchan))
    cmds.append(_intanRegWrite(address=7, data=0))
    #cmds.append(dc.reg_write(dc.MOD_DAQ, dc.DAQ_CHIP_CMD, 0)) # clear the CMD register
    cmds.append(_intanRegWrite(clear=True))
    resps = _controlCmdWrapper(cmds)

def pingDatanode():
    """
    ping the datanode
    returns nothing
    mainly used to test for hwifErrors, as in checkVitals()
    """
    cmd = dc.ControlCommand(type=dc.ControlCommand.PING_DNODE)
    resp = _controlCmdWrapper(cmd)

def checkVitals():
    """
    This function is somewhat unusual, in that it does not raise hwifError
    in the event of an I/O error. Instead, it always returns vitals, a dict
    whose values indicate the status of the daemon and datanode.
    True means up, False means down, None means unknown.
    """
    vitals = {  'daemon' : None,
                'datanode' : None,
                'firmware' : None,
                'errors' : None,
                'stream' : None,
                'record' : None
                }
    try:
        pingDatanode()
        vitals['daemon'] = True
        vitals['datanode'] = True
        vitals['firmware'] = _doRegRead(dc.MOD_CENTRAL, dc.CENTRAL_GIT_SHA_PIECE)
        vitals['errors'] = _doRegRead(dc.MOD_ERR, dc.ERR_ERR0)
        vitals['stream'] = isStreaming()
        vitals['record'] = isRecording()
    except hwifError as e:
        if e.type in (0,2):
            # cannot connect to daemon
            vitals['daemon'] = False
            vitals['datanode'] = None
            vitals['firmware'] = None
            vitals['errors'] = None
            vitals['stream'] = None
            vitals['record'] = None
        elif e.type==1:
            if e.errcode in (dc.ControlResErr.NO_DNODE, dc.ControlResErr.DNODE_DIED):
                # cannot connect to datanode
                vitals['daemon'] = True
                vitals['datanode'] = False
                vitals['firmware'] = None
                vitals['errors'] = None
                vitals['stream'] = None
                vitals['record'] = None
            elif e.errcode==dc.ControlResErr.DNODE:
                # datanode is responding, but error condition is present
                vitals['daemon'] = True
                vitals['datanode'] = True
                vitals['firmware'] = _doRegRead(dc.MOD_CENTRAL, dc.CENTRAL_GIT_SHA_PIECE)
                vitals['errors'] = _doRegRead(dc.MOD_ERR, dc.ERR_ERR0)
                vitals['stream'] = isStreaming()
                vitals['record'] = isRecording()
    finally:
        return vitals

