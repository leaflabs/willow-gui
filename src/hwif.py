"""
hwif.py (hwif = HardWare InterFace)
created by Chris Chronopoulos on 20141109 
These functions interface with the Willow hardware, accounting for state,
and raising informative exceptions when things go wrong.
"""

import sys, os, socket
from time import time

from parameters import *
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

import CustomExceptions as ex

def isStreaming():
    resp = do_control_cmd(reg_read(3,9))
    if resp:
        if resp.type==ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]
    else:
        raise ex.NoResponseError
    return resp.reg_io.val == 1

def isRecording():
    resp = do_control_cmd(reg_read(3,11))
    if resp:
        if resp.type==ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]
    else:
        raise ex.NoResponseError
    return resp.reg_io.val == 3

def getSampleType():
    val = doRegRead(3,10)
    if val == 0:
        return 'subsample'
    elif val == 1:
        return 'boardsample'
    else:
        return -1

def startStreaming():
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
        resp = do_control_cmd(cmd)
        if resp:
            if resp.type==ControlResponse.ERR:
                raise ex.ERROR_DICT[resp.err.code]
        else:
            raise ex.NoResponseError

def startStreaming_boardSamples():
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
        resp = do_control_cmd(cmd)
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
        resps = do_control_cmds(cmds)
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
        cmd.acquire.exp_cookie = long(time())
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
        resps = do_control_cmds(cmds)
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
        resps = do_control_cmds(cmds)
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
    resps = do_control_cmds(cmds)
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

def doTransfer(nsamples=None, filename=None):
    if isStreaming() or isRecording():
        raise ex.StateChangeError
    else:
        cmd = ControlCommand(type=ControlCommand.STORE)
        cmd.store.start_sample = 0
        if nsamples:
            cmd.store.nsamples = nsamples
        # (else leave missing which indicates whole experiment)
        cmd.store.path = filename
        resp = do_control_cmd(cmd)
        if resp:
            if resp.type==ControlResponse.ERR:
                raise ex.ERROR_DICT[resp.err.code]
        else:
            raise ex.NoResponseError


def pingDatanode():
    cmd = ControlCommand(type=ControlCommand.PING_DNODE)
    resp = do_control_cmd(cmd)
    if resp:
        if resp.type==ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]
    else:
        raise ex.NoResponseError

def doRegRead(module, address):
    resp = do_control_cmd(reg_read(module, address))
    if resp:
        if resp.type == ControlResponse.REG_IO:
            return resp.reg_io.val
        elif resp.type==ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]
    else:
        raise ex.NoResponseError

def doRegWrite(module, address, data):
    resp = do_control_cmd(reg_write(module, address, data))
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
    resps = do_control_cmds(cmds)
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


