#!/usr/bin/env python3
"""
https://github.com/xstaticxgpx/simpleton
"""

import asyncio, asyncssh
import sys
from queue import Queue

# raised when asyncio.wait_for timeout reached
from concurrent.futures._base import TimeoutError

from _logconfig import *
from _argparser import *

## Definition and static variables
_delimiter = '-'
_hosts_dict = {}
connectfailures = {}
sessionfailures = {}
# pointers for sessionfailures list values
_CMD = 0
_STATUS = 1
# Characters to backslash escape in output script
_ESCAPE = [
    '`',
    '$',
]

## Global configuration

# 100ms poll cycle (used in SSHManager)
YIELD_TIMEOUT=0.1
# Max. 50 concurrent sessions
MAX_CONCURRENT=50
# Wait max. 10s for connection
CONNECT_TIMEOUT=10
# Max 5min session time
SESSION_TIMEOUT=300

def parse_hosts(path):
    """
    Read lines from path and parse legit entries with split()
    """
    with open(path) as f:
        hosts = f.readlines()

    # Parse out comments and blank lines, split on whitespace
    hosts = [line.strip().split() for line in hosts if not line.startswith('#') and line.strip()]
    log.debug('Parsed %d entries from %s' % (len(hosts), path))

    # Return dictionary of ip: [hostnames,..]
    return {line[0]: line[1:] for line in hosts}

def ip2host(ip):
    """
    Host dictionary lookup
    """
    global _hosts_dict

    try:
        return _hosts_dict[ip][0]
    except:
        return ip

def sanitize(s):
    """
    Backslash escape characters
    """
    global _ESCAPE

    for char in _ESCAPE:
        if char in s:
            s = s.replace(char, '\\'+char)
    return s

class SSHClientSession(asyncssh.SSHClientSession):
    global output
    global _delimiter

    def __init__(self):
        self.user  = "null"
        self.cmd   = "null"
        self.host  = None
        self.first = True
        self.error = False

    def connection_made(self, chan):
        self.host = ip2host(chan.get_extra_info('peername')[0])
        self.user = chan.get_extra_info('connection')._usr
        self.cmd  = chan.get_extra_info('connection')._cmd

    def data_received(self, data, datatype):
        if self.first:
            print('cat <<_EOF >>%s\n# %s\n%s\n%s\n_EOF\n' % 
                 (self.host+'_'+self.user+'.out', sanitize(self.cmd), _delimiter*80, data), file=output)
            log.info('[%s:%s] %s\n%s' % 
                    (self.host, self.user, self.cmd, data))
            self.first = False
        else:
            print('cat <<_EOF >>%s\n%s\n_EOF' % 
                 (self.host+'_'+self.user+'.out', data.strip()), file=output)
            log.info('[%s:%s] %s\n%s' % 
                    (self.host, self.user, self.cmd, data))


    def exit_status_received(self, status):
        if status:
            self.error = "exit code %d" % status
#            log.error('[%s:%s] %s (%s)' % (self.host, self.user, self.cmd, self.error))

    def connection_lost(self, exc):
        if exc:
            self.error = str(exc) if str(exc) else "Timeout"
#            log.error('[%s:%s] SSH session error: %s' % (self.host, self.user, self.error))

@asyncio.coroutine
def SSHClient(loop, host, cmdlist):
    global connectfailures
    global sessionfailures

    try:
        with (yield from asyncio.wait_for(asyncssh.connect(host, known_hosts=None), CONNECT_TIMEOUT)) as conn:
            conn._usr = conn.get_extra_info("username")
            log.warning('[%s:%s] SSH connection initiated' % (host, conn._usr))
            for cmd in cmdlist:
                conn._cmd = cmd.strip()
                try:
                    chan, session = yield from conn.create_session(SSHClientSession, conn._cmd)
                    yield from asyncio.wait_for(chan.wait_closed(), SESSION_TIMEOUT)
                except TimeoutError:
                    session.error = "Timeout"
                finally:
                    if session.error:
                        log.critical('[%s:%s] %s (%s)' % (host, conn._usr, conn._cmd, session.error))
                        log.critical('[%s:%s] Failure detected, breaking...' % (host, conn._usr))
                        sessionfailures[host] = [cmd, session.error]
                        break


    except (OSError, asyncssh.Error, TimeoutError) as exc:
        exc = str(exc) if str(exc) else "Timeout"
        log.error('[%s] SSH connection failed: %s' % (host, exc))
        connectfailures[host] = exc

@asyncio.coroutine
def SSHManager(loop, queue, cmdlist):
    global MAX_CONCURRENT
    global YIELD_TIMEOUT

    tasks = []
    while True:
        while (len(tasks) > MAX_CONCURRENT) or (tasks and queue.empty()):
            for task in tasks:
                if task.done():
                    tasks.remove(task)
            yield from asyncio.sleep(YIELD_TIMEOUT)
    
        if not queue.empty():
            host = yield from queue.get()
            tasks.append(asyncio.async(SSHClient(loop, host, cmdlist)))
        else:
            if not tasks:
                break
    loop.stop()


if __name__ == '__main__':
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # Open output script for writing
    output = open(args.output, 'w')

    # Configure logging format
    logging.config.dictConfig(SIMPLETON_LOGGING)
    log = logging.getLogger("default")

    # Startup logging thread
    _log_queue = Queue()
    log_async  = logging.handlers.QueueHandler(_log_queue)
    log_queue  = logging.handlers.QueueListener(_log_queue, *log.handlers)

    log_queue.start()
    log.handlers = [log_async,]

    # Bootstrap asyncio objects
    loop  = asyncio.get_event_loop()
    queue = asyncio.Queue()

    if args.cmdfile:
        with open(args.cmdfile) as f:
            args.cmdlist = f.readlines()

    _hosts_dict = parse_hosts(args.hostsfile)
    _hosts = set()
    if args.hostmatch:
        for ip in _hosts_dict:
            for match in args.hostmatch:
                [_hosts.add(hostname) for hostname in _hosts_dict[ip] if match in hostname]
    
    # Exclusion logic
    __hosts = list(_hosts)
    if args.hostexclude:
        for exclude in args.hostexclude:
            [_hosts.remove(hostname) for hostname in __hosts if exclude in hostname]
    del __hosts

    if not _hosts:
        log.critical('No hosts matched')
        log_queue.stop()
        sys.exit(1)

    [queue.put_nowait(hostname) for hostname in _hosts]
    _host_count = queue.qsize()

    try:
        _start = loop.time()
        loop.run_until_complete(SSHManager(loop, queue, args.cmdlist))

    finally:
        _end   = loop.time()
        log.debug(_delimiter*40)
        log.info('Finished run in %.03fms' % ((_end-_start)*1000))
        if sessionfailures or connectfailures:
            for host in sorted(_hosts):
                if host in sessionfailures:
                    log.warning('%s command failed: %s (%s)' % (host, sessionfailures[host][_CMD], sessionfailures[host][_STATUS]))
                elif host in connectfailures:
                    log.warning('%s connection failed: %s' % (host, connectfailures[host]))
        else:
            log.info('No errors reported.')
        log.debug(_delimiter*40)
        log.info('Saved output script to %s' % args.output)
        output.close()
        log_queue.stop()
