#!/usr/bin/env python3
"""
https://github.com/xstaticxgpx/simpleton
"""

import asyncio, asyncssh
import sys

from asyncio import wait_for as aiowait

# raised when asyncio.wait_for/aiowait timeout reached
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

# 96 concurrent sessions max.
MAX_CONCURRENT = 96
# Wait max. 10s for connection stand up
CONNECT_TIMEOUT = 10
# 5min session timeout (no input received)
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
    """
    Inherits asyncssh.SSHClientSession
    https://asyncssh.readthedocs.org/en/stable/api.html#sshclientsession
    """

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

    def connection_lost(self, exc):
        if exc:
            self.error = str(exc) if str(exc) else "Timeout"

@asyncio.coroutine
def SSHClient(host, cmdlist):
    """
    Perform SSH client logic
    """

    try:
        with (yield from aiowait(asyncssh.connect(host, **_SSH_OPTS), CONNECT_TIMEOUT)) as conn:
            conn.usr = conn.get_extra_info("username")
            log.warning('[%s:%s] SSH connection initiated', host, conn.usr)

            for cmd in cmdlist:
                conn.cmd = cmd.strip()
                try:
                    chan, session = yield from conn.create_session(SSHClientSession, conn.cmd)
                    yield from aiowait(chan.wait_closed(), SESSION_TIMEOUT)

                except AIOTimeout:
                    session.error = "Timeout"

                finally:
                    if session.error:
                        log.critical('[%s:%s] %s (%s)', host, conn.usr, conn.cmd, session.error)
                        log.critical('[%s:%s] Failure detected, breaking...', host, conn.usr)
                        sessionfailures[host] = (cmd, session.error)
                        break # pylint: disable=lost-exception

    except (OSError, asyncssh.Error, AIOTimeout) as exc:
        log.error('[%s] SSH connection failed: %s', host, repr(exc))
        connectfailures[host] = repr(exc)


@asyncio.coroutine
def SSHManager(host_queue, cmdlist):
    """
    Parallel SSHClient
    """

    tasks = []
    while True:
        while (len(tasks) > MAX_CONCURRENT) or (tasks and host_queue.empty()):
            done, pending = yield from asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED) # pylint: disable=unused-variable
            [tasks.remove(task) for task in done] # pylint: disable=expression-not-assigned

        if not host_queue.empty():
            tasks.append(asyncio.async(SSHClient((yield from host_queue.get()), cmdlist)))
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
    _host_queue = asyncio.Queue()
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
                [_hosts.add(hostname) for hostname in _hosts_dict[ip] if match in hostname] # pylint: disable=expression-not-assigned

    # Host exclusion logic
    __hosts = list(_hosts)
    if args.hostexclude:
        for exclude in args.hostexclude:
            [_hosts.remove(hostname) for hostname in __hosts if exclude in hostname] # pylint: disable=expression-not-assigned

    if not _hosts:
        log.critical('No hosts matched')
        log_queue.stop()
        sys.exit(1)
    log.debug('Matched %d hosts like %s, unlike %s',
              len(_hosts), args.hostmatch, args.hostexclude if args.hostexclude else "''")

    # Place matched hosts into queue
    #for _ in range(200):
    [_host_queue.put_nowait(hostname) for hostname in _hosts] # pylint: disable=expression-not-assigned
    _host_count = _host_queue.qsize()

    try:
        # Open output script for writing
        output = open(args.output, 'w')

        _start = loop.time()
        # Begin asynchronous loop execution
        loop.run_until_complete(SSHManager(_host_queue, args.cmdlist))

    finally:
        _end = loop.time()

        log.debug(_delimiter*40)
        _fail_count = len(connectfailures)+len(sessionfailures)
        log.info('Successfully ran on %d hosts in %.03fs', (_host_count-_fail_count), (_end-_start))
        if _fail_count:
            log.warn('Failed on %d hosts:', _fail_count)

        if sessionfailures or connectfailures:
            # Only report unique failures (_hosts set)
            for _host in sorted(_hosts):
                if _host in sessionfailures:
                    log.warning('%s command failed: %s (%s)',
                                _host,
                                sessionfailures[_host][_CMD], sessionfailures[_host][_STATUS])

                elif _host in connectfailures:
                    log.warning('%s connection failed: %s', _host, connectfailures[_host])
        else:
            log.info('No errors reported.')

        log.debug(_delimiter*40)
        log.info('Saved output script to %s', args.output)
        output.close()
        log_queue.stop()
