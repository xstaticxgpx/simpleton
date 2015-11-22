#!/usr/bin/env python3
import logging, logging.config, logging.handlers
import sys
import asyncio, asyncssh
from queue import Queue

from simpleton import *

# 10ms poll cycle
YIELD_TIMEOUT=0.01
# Max. 50 parallel sessions
MAX_CONCURRENT=50

_host_dict = {}

def parse_hosts(path='/etc/hosts'):
    with open(path) as f:
        hosts = f.readlines()
    hosts = [line.strip().split() for line in hosts if not line.startswith('#') and line.strip()]
    log.debug('Parsed %d entries from %s' % (len(hosts), path))
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
        self.fail = False

    def connection_made(self, chan):
        #self._chan    = chan
        self.hostname = ip2host(chan.get_extra_info('peername')[0])

    def data_received(self, data, datatype):
        log.info('[%s] %s' % (self.hostname, data.strip()))

    def exit_status_received(self, status):
        if status:
            self.fail = True
            log.error('[%s] Exit code %d' % (self.hostname, status))
        #else:
        #    print('[%s]- Completed' % (self.hostname, (_end-self._start)*1000))

    def connection_lost(self, exc):
        if exc:
            print('[%s]? SSH session error: %s' % (self.hostname, str(exc)), file=sys.stderr)

@asyncio.coroutine
def SSHClient(host, cmdlist):
    try:
        with (yield from asyncssh.connect(host, known_hosts=None)) as conn:
            log.debug('[%s] Connection initiated' % host)
            for cmd in cmdlist:
                chan, session = yield from conn.create_session(SSHClientSession, cmd)
                log.warning('[%s] Executing command: %s' % (host, cmd))
                session.cmd = cmd
                yield from chan.wait_closed()
                if session.fail:
                    log.critical('[%s] Failure detected, breaking...' % host)
                    break
    except (OSError, asyncssh.Error) as exc:
        print('[%s]? SSH connection failed: %s' % (host, str(exc)), file=sys.stderr)

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

    _host_dict = parse_hosts()
    if args.hostmatch:
        for ip in _host_dict:
            for match in args.hostmatch:
                [queue.put_nowait(hostname) for hostname in _host_dict[ip] if match in hostname]

    loop.run_until_complete(SSHManager(loop, queue, args.cmdlist))
