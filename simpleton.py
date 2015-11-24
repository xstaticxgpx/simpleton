#!/usr/bin/env python3
"""
https://github.com/xstaticxgpx/simpleton
"""

import logging, logging.config, logging.handlers
import sys
import asyncio, asyncssh
from queue import Queue

# raised when asyncio.wait_for timeout reached
from concurrent.futures._base import TimeoutError

from simpleton import *

## Global configuration

# 100ms poll cycle (used in SSHManager)
YIELD_TIMEOUT=0.1
# Max. 50 concurrent sessions
MAX_CONCURRENT=50
# Wait max. 10s for connection
CONNECT_TIMEOUT=10

## Definitions
_host_dict = {}
_delimiter = '-'*80
connectfailures = {}
sessionfailures = {}

## Static variables
# pointers for sessionfailures list values
_CMD = 0
_EXITCODE = 1

def parse_hosts(path):
    with open(path) as f:
        hosts = f.readlines()
    # Parse out comments and blank lines
    hosts = [line.strip().split() for line in hosts if not line.startswith('#') and line.strip()]
    log.debug('Parsed %d entries from %s' % (len(hosts), path))
    # Return dictionary of ip: [hostnames,..]
    return {line[0]: line[1:] for line in hosts}

def ip2host(ip):
    global _host_dict

    try:
        return _host_dict[ip][0]
    except:
        return ip

class SSHClientSession(asyncssh.SSHClientSession):

    global output

    def __init__(self):
        self.user = "null"
        self.cmd  = "null"
        self.host = None
        self.fail = False
        self.first = True

    def connection_made(self, chan):
        self.user = chan.get_extra_info('connection')._usr
        self.cmd  = chan.get_extra_info('connection')._cmd
        self.host = ip2host(chan.get_extra_info('peername')[0])

    def data_received(self, data, datatype):
        global _delimiter
        if self.first:
            print('cat <<_EOF >>%s\n\n# %s\n%s\n%s\n_EOF\n' % 
                 (self.host+'_'+self.user+'.out', self.cmd, _delimiter, data.strip()), file=output)
            log.info('[%s:%s] %s\n%s' % 
                    (self.host, self.user, self.cmd, data.strip()))
            self.first = False
        else:
            print('cat <<_EOF >>%s\n%s\n_EOF' % 
                 (self.host+'_'+self.user+'.out', data.strip()), file=output)
            log.info('[%s:%s] %s\n%s' % 
                    (self.host, self.user, self.cmd, data.strip()))


    def exit_status_received(self, status):
        if status:
            self.fail = status
            log.error('[%s:%s] %s -> error code %d' % (self.host, self.user, self.cmd, status))

    def connection_lost(self, exc):
        if exc:
            self.fail = True
            log.error('[%s:%s] SSH session error: %s' % (self.host, self.user, str(exc) if str(exc) else "Timeout"))

@asyncio.coroutine
def SSHClient(host, cmdlist):

    global connectfailures
    global sessionfailures

    try:
        with (yield from asyncio.wait_for(asyncssh.connect(host, known_hosts=None), CONNECT_TIMEOUT)) as conn:
            conn._usr = conn.get_extra_info("username")
            log.debug('[%s:%s] Connection initiated' % (host, conn._usr))
            for cmd in cmdlist:
                conn._cmd = cmd
                chan, session = yield from conn.create_session(SSHClientSession, cmd)
                yield from chan.wait_closed()
                if session.fail:
                    log.critical('[%s:%s] Failure detected, breaking...' % (host, conn._usr))
                    sessionfailures[host] = [cmd, session.fail]
                    break
    except (OSError, asyncssh.Error, TimeoutError) as exc:
        exc = str(exc) if str(exc) else "Timeout"
        log.error('[%s] SSH connection failed: %s' % (host, exc))
        connectfailures[host] = exc

@asyncio.coroutine
def SSHManager(loop, queue, cmdlist):

    tasks = []
    while True:
        while (len(tasks) > MAX_CONCURRENT) or (tasks and queue.empty()):
            for task in tasks:
                if task.done():
                    tasks.remove(task)
            yield from asyncio.sleep(YIELD_TIMEOUT)
    
        if not queue.empty():
            host = yield from queue.get()
            tasks.append(asyncio.async(SSHClient(host, cmdlist)))
        else:
            if not tasks:
                break
    loop.stop()


if __name__ == '__main__':

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    output = open(args.output, 'w')

    # Configure logging format
    logging.config.dictConfig(SIMPLETON_LOGGING)
    log = logging.getLogger("default")

    _log_queue = Queue()
    log_async  = logging.handlers.QueueHandler(_log_queue)
    log_queue  = logging.handlers.QueueListener(_log_queue, *log.handlers)

    log_queue.start()
    log.handlers = [log_async,]

    loop  = asyncio.get_event_loop()
    queue = asyncio.Queue()

    if args.cmdfile:
        with open(args.cmdfile) as f:
            args.cmdlist = f.readlines()

    _host_dict = parse_hosts(args.hostsfile)
    _hosts = []
    if args.hostmatch:
        for ip in _host_dict:
            for match in args.hostmatch:
                #i = 'i'*10
                #for c in i:
                [_hosts.append(hostname) for hostname in _host_dict[ip] if match in hostname]
    
    _uniq = set(_hosts)
    if args.hostexclude:
        for exclude in args.hostexclude:
            [_uniq.remove(hostname) for hostname in _hosts if exclude in hostname]

    if not _uniq:
        log.critical('No hosts matched')
        log_queue.stop()
        sys.exit(1)

    try:
        [queue.put_nowait(hostname) for hostname in _uniq]
        _host_count = queue.qsize()

        _start = loop.time()
        loop.run_until_complete(SSHManager(loop, queue, args.cmdlist))

    finally:
        _end   = loop.time()
        #log.critical('Completed %d hosts, failed %d hosts: %s %s' % (_host_count-len(connectfailures), len(connectfailures), ' '.join(sorted(connectfailures)), ' '.join(sorted(sessionfailures))))
        log.debug(_delimiter)
        log.critical('Finished run in %.03fms' % ((_end-_start)*1000))
        for host in sorted(_uniq):
            if host in sessionfailures:
                log.warning('%s command failed: %s (exit code: %d)' % (host, sessionfailures[host][_CMD], sessionfailures[host][_EXITCODE]))
            elif host in connectfailures:
                log.critical('%s connection failed: %s' % (host, connectfailures[host]))
        log.debug(_delimiter)
        log.info('Saved output script to %s' % args.output)
        log_queue.stop()
