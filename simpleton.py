#!/usr/bin/env python3
"""
https://github.com/xstaticxgpx/simpleton
"""

import asyncio, asyncssh
import sys

from asyncio import wait_for

# raised when asyncio.wait_for timeout reached
from concurrent.futures._base import TimeoutError as AIOTimeout

from _logconfig import log, log_queue
from _argparser import parser

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
# SSH connection options
_SSH_OPTS = {
    'known_hosts': None,
}

## Global configuration

# 100ms poll cycle (used in SSHManager)
YIELD_TIMEOUT = 0.1
# Max. 50 concurrent sessions
MAX_CONCURRENT = 50
# Wait max. 10s for connection
CONNECT_TIMEOUT = 10
# Max 5min session time
SESSION_TIMEOUT = 300


def parse_hosts(path):
    """
    Read lines from path and parse entries with split()
    """
    with open(path) as hostsfile:
        hosts = hostsfile.readlines()

    # Parse out comments and blank lines, split on whitespace
    hosts = [line.strip().split() for line in hosts if not line.startswith('#') and line.strip()]
    log.debug('Parsed %d entries from %s', len(hosts), path)

    # Return dictionary of ip: [hostnames,..]
    return {line[0]: line[1:] for line in hosts}

def ip2host(peername):
    """
    Host dictionary lookup
    """

    try:
        return _hosts_dict[peername][0]
    except (KeyError, IndexError):
        return peername

def sanitize(s):
    """
    Backslash escape characters
    """

    for char in _ESCAPE:
        if char in s:
            s = s.replace(char, '\\'+char)
    return s

class SSHClientSession(asyncssh.SSHClientSession):

    def __init__(self):
        self.error = False

        self._first = True
        self._host = None
        self._usr = "null"
        self._cmd = "null"
        self._file = None

    def connection_made(self, chan):
        self._host = ip2host(chan.get_extra_info('peername')[0])
        self._usr = chan.get_extra_info('connection').usr
        self._cmd = chan.get_extra_info('connection').cmd
        self._file = '%s_%s.out' % (self._host, self._usr)

    def data_received(self, data, datatype):
        if self._first:

            print('cat <<_EOF >>%s\n%s\n%s\n%s\n_EOF\n' %
                  (self._file,
                   "# "+sanitize(self._cmd),
                   _delimiter*80,
                   data), file=output)

            log.info('[%s:%s] %s\n%s', self._host, self._usr, self._cmd, data)
            self._first = False

        else:

            print('cat <<_EOF >>%s\n%s\n_EOF' % (self._file, data.strip()),
                  file=output)

            log.info('[%s:%s] %s\n%s', self._host, self._usr, self._cmd, data)


    def exit_status_received(self, status):
        if status:
            self.error = "exit code %d" % status

    def connection_lost(self, e):
        if e:
            self.error = str(e) if str(e) else "Timeout"

@asyncio.coroutine
def SSHClient(host, cmdlist):

    try:
        with (yield from wait_for(asyncssh.connect(host, **_SSH_OPTS), CONNECT_TIMEOUT)) as conn:
            conn.usr = conn.get_extra_info("username")
            log.warning('[%s:%s] SSH connection initiated', host, conn.usr)

            for cmd in cmdlist:
                conn.cmd = cmd.strip()
                try:
                    chan, session = yield from conn.create_session(SSHClientSession, conn.cmd)
                    yield from asyncio.wait_for(chan.wait_closed(), SESSION_TIMEOUT)

                except AIOTimeout:
                    session.error = "Timeout"

                finally:
                    if session.error:
                        log.critical('[%s:%s] %s (%s)', host, conn.usr, conn.cmd, session.error)
                        log.critical('[%s:%s] Failure detected, breaking...', host, conn.usr)
                        sessionfailures[host] = [cmd, session.error]
                        break

    except (OSError, asyncssh.Error, AIOTimeout) as e:
        e = repr(e)
        log.error('[%s] SSH connection failed: %s', host, e)
        connectfailures[host] = e


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


    # Bootstrap asyncio objects
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    # Load commands from file if specified
    # overwrites commands specified on CLI
    if args.cmdfile:
        with open(args.cmdfile) as cmdfile:
            args.cmdlist = cmdfile.readlines()

    # Host matching logic
    _hosts_dict = parse_hosts(args.hostsfile)
    _hosts = set()
    if args.hostmatch:
        for ip in _hosts_dict:
            for match in args.hostmatch:
                [_hosts.add(hostname) for hostname in _hosts_dict[ip] if match in hostname]

    # Host exclusion logic
    __hosts = list(_hosts)
    if args.hostexclude:
        for exclude in args.hostexclude:
            [_hosts.remove(hostname) for hostname in __hosts if exclude in hostname]
    del __hosts

    if not _hosts:
        log.critical('No hosts matched')
        log_queue.stop()
        sys.exit(1)

    # Place matched hosts into queue
    [queue.put_nowait(hostname) for hostname in _hosts]
    _host_count = queue.qsize()

    try:
        # Open output script for writing
        output = open(args.output, 'w')

        _start = loop.time()
        # Begin asynchronous loop execution
        loop.run_until_complete(SSHManager(loop, queue, args.cmdlist))

    finally:
        _end = loop.time()

        log.debug(_delimiter*40)
        log.info('Finished run in %.03fms', (_end-_start)*1000)

        if sessionfailures or connectfailures:
            for host in sorted(_hosts):
                if host in sessionfailures:
                    log.warning('%s command failed: %s (%s)',
                                host, sessionfailures[host][_CMD], sessionfailures[host][_STATUS])

                elif host in connectfailures:
                    log.warning('%s connection failed: %s', host, connectfailures[host])
        else:
            log.info('No errors reported.')

        log.debug(_delimiter*40)
        log.info('Saved output script to %s', args.output)
        output.close()
        log_queue.stop()
