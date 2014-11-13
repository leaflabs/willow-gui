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
    return resp.reg_io.val == 1

def isRecording():
    resp = do_control_cmd(reg_read(3,11))
    return resp.reg_io.val == 3

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
        if resp.type == ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]

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
            if resp.type==ControlResponse.ERR:
                raise ex.ERROR_DICT[resp.err.code]

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
            if resp.type==ControlResponse.ERR:
                raise ex.ERROR_DICT[resp.err.code]

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
            if resp.type==ControlResponse.ERR:
                raise ex.ERROR_DICT[resp.err.code]

def takeSnapshot(nsamples, filename):
    cmds = []
    if isStreaming():
        # can't handle this yet (GUI crashes, look into BSMP vs BSUB issue)
        raise ex.StateChangeError
        """
        cmd = ControlCommand(type=ControlCommand.STORE)
        cmd.store.path = filename
        cmd.store.nsamples = nsamples
        cmds.append(cmd)
        ###
        # need this to set sample_type back to BOARD_SAMPLE, otherwise daemon barfs forever
        cmd = ControlCommand(type=ControlCommand.FORWARD)
        cmd.forward.sample_type = BOARD_SAMPLE
        cmd.forward.force_daq_reset = False # ???
        try:
            aton = socket.inet_aton(DEFAULT_FORWARD_ADDR)
        except socket.error:
            self.parent.statusBox.append('Invalid address: ' + DEFAULT_FORWARD_ADDR)
            return
        cmd.forward.dest_udp_addr4 = struct.unpack('!l', aton)[0]
        cmd.forward.dest_udp_port = DEFAULT_FORWARD_PORT
        cmd.forward.enable = True
        cmds.append(cmd)
        """
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
        if resp.type==ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]
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
        if resp.type==ControlResponse.ERR:
            raise ex.ERROR_DICT[resp.err.code]


def pingDatanode():
    cmd = ControlCommand(type=ControlCommand.PING_DNODE)
    resp = do_control_cmd(cmd)
    if resp.type==ControlResponse.ERR:
        raise ex.ERROR_DICT[resp.err.code]

def doRegRead(module, address):
    resp = do_control_cmd(reg_read(module, address))
    if resp.type == ControlResponse.REG_IO:
        return resp.reg_io.val
    else:
        raise DaemonControlError

def checkVitals():
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


