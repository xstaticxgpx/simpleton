#!/usr/bin/env python3
import logging, logging.config, logging.handlers
import sys
import asyncio, asyncssh
from queue import Queue

# raised when asyncio.wait_for timeout reached
from concurrent.futures._base import TimeoutError

from simpleton import *

# 10ms poll cycle
YIELD_TIMEOUT=0.01
# Max. 50 parallel sessions
MAX_CONCURRENT=50
# Wait at most 5s to initiate connection
CONNECT_TIMEOUT=5

_host_dict = {}

def parse_hosts(path='/etc/hosts'):
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
    def __init__(self):
        self.cmd  = None
        self.user = None
        self.host = None
        self.fail = False

    def connection_made(self, chan):
        #self._chan    = chan
        self.host = ip2host(chan.get_extra_info('peername')[0])

    def data_received(self, data, datatype):
        log.info('[%s:%s] %s\ncat <<_EOF >>%s\n%s\n%s\n%s\n%s\n\n_EOF' % 
                (self.host, self.user, self.cmd, self.host+'_'+self.user+'.out', self.cmd, '-'*80, data.strip(), '-'*80))

    def exit_status_received(self, status):
        if status:
            log.error('[%s] Exit code %d' % (self.host, status))
            self.fail = True

    def connection_lost(self, exc):
        if exc:
            log.error('[%s] SSH session error: %s' % (self.host, str(exc) if str(exc) else "Timeout"))

@asyncio.coroutine
def SSHClient(host, cmdlist):
    try:
        with (yield from asyncio.wait_for(asyncssh.connect(host, known_hosts=None), CONNECT_TIMEOUT)) as conn:
            username = conn.get_extra_info("username")
            log.debug('[%s] Connection initiated as user %s' % (host, username))
            for cmd in cmdlist:
                chan, session = yield from conn.create_session(SSHClientSession, cmd)
                session.cmd  = cmd
                session.user = username
                yield from chan.wait_closed()
                if session.fail:
                    log.critical('[%s] Failure detected, breaking...' % host)
                    break
    except (OSError, asyncssh.Error, TimeoutError) as exc:
        log.error('[%s] SSH connection failed: %s' % (host, str(exc) if str(exc) else "Timeout"))

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

    _host_dict = parse_hosts()
    if args.hostmatch:
        for ip in _host_dict:
            for match in args.hostmatch:
                [queue.put_nowait(hostname) for hostname in _host_dict[ip] if match in hostname]

    _host_count = queue.qsize()
    
    _start = loop.time()
    loop.run_until_complete(SSHManager(loop, queue, args.cmdlist))
    _end   = loop.time()
    log.critical('Completed %d hosts in %.03fms' % (_host_count, (_end-_start)*1000))
