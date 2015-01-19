import sys, os
from parameters import *
sys.path.append(os.path.join(DAEMON_DIR, 'util'))
from daemon_control import *

class DaemonControlError(Exception):
    """
    What this means is that the the daemon responded properly but with an
    error message. That error message can be further categorized into TYPE,
    but this is not yet implemented.
    """
    pass


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
    'another is ongoing'?)
    """
    pass

class AlreadyError(Exception):
    pass

###

class NO_DNODE_error(Exception):
    def __str__(self):
        return 'NO_DNODE: No datanode connected'

class DAEMON_error(Exception):
    def __str__(self):
        return 'DAEMON: Internal daemon error'

class DAEMON_IO_error(Exception):
    def __str__(self):
        return 'DAEMON_IO: Daemon I/O error'

class C_VALUE_error(Exception):
    def __str__(self):
        return 'C_VALUE: Invalid arguments on client control socket'

class C_PROTO_error(Exception):
    def __str__(self):
        return 'C_PROTO: Protocol error on client control socket'

class D_PROTO_error(Exception):
    def __str__(self):
        return 'D_Proto: Protocol error on datanode control socket'

class DNODE_error(Exception):
    def __str__(self):
        return 'DNODE: Datanode transaction failed'

class DNODE_ASYNC_error(Exception):
    def __str__(self):
        return 'DNODE_ASYNC: Asynchronous datanode error'

class DNODE_DIED_error(Exception):
    def __str__(self):
        return 'DNODE_DIED: Datanode connection died while processing request'

ERROR_DICT = {  ControlResErr.NO_DNODE : NO_DNODE_error,
                ControlResErr.DAEMON : DAEMON_error,
                ControlResErr.DAEMON_IO : DAEMON_IO_error,
                ControlResErr.C_VALUE : C_VALUE_error,
                ControlResErr.C_PROTO : C_PROTO_error,
                ControlResErr.D_PROTO : D_PROTO_error,
                ControlResErr.DNODE : DNODE_error,
                ControlResErr.DNODE_ASYNC : DNODE_ASYNC_error,
                ControlResErr.DNODE_DIED : DNODE_DIED_error
                }

