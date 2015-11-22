#!/usr/bin/env python3
import asyncio, asyncssh, sys

from simpleton import parser

# 10ms poll cycle
YIELD_TIMEOUT=0.01

# Max. 50 parallel sessions
MAX_CONCURRENT=50

_cmds = ['ls -la /etc/hosts', 'exit 127', 'whoami']
_host_dict = {}

def parse_hosts(path='/etc/hosts'):
    with open(path) as f:
        hosts = f.readlines()
    hosts = [line.strip().split() for line in hosts if not line.startswith('#') and line.strip()]
    return {line[0]: line[1:] for line in hosts}

def ip2host(ip):
    global _host_dict

    try:
        return _host_dict[ip][0]
    except:
        return ip

class MySSHClientSession(asyncssh.SSHClientSession):
    def connection_made(self, chan):
        self._start   = loop.time()
        self._chan    = chan
        self.hostname = ip2host(chan.get_extra_info('peername')[0])

    def data_received(self, data, datatype):
        print('[%s]~' % self.hostname, data, end='')

    def exit_status_received(self, status):
        _end = loop.time()
        if status:
            print('[%s]! Exit code %d, took %.03fms' % (self.hostname, status, (_end-self._start)*1000), file=sys.stderr)
        else:
            print('[%s]- Completed, took %.03fms' % (self.hostname, (_end-self._start)*1000))

    def connection_lost(self, exc):
        if exc:
            print('[%s]? SSH session error: %s' % (self.hostname, str(exc)), file=sys.stderr)

@asyncio.coroutine
def run_client(host):
    try:
        with (yield from asyncssh.connect(host, known_hosts=None)) as conn:
            print('[%s]+ Connection initiated' % host)
            for cmd in _cmds:
                chan, session = yield from conn.create_session(MySSHClientSession, cmd)
                print('[%s]* Executing command: %s' % (host, cmd))
                yield from chan.wait_closed()
    except (OSError, asyncssh.Error) as exc:
        print('[%s]? SSH connection failed: %s' % (host, str(exc)), file=sys.stderr)

@asyncio.coroutine
def manager(loop, queue):
    tasks = []
    while True:
        while (len(tasks) > MAX_CONCURRENT) or (tasks and queue.empty()):
            for task in tasks:
                if task.done():
                    tasks.remove(task)
                yield from asyncio.sleep(YIELD_TIMEOUT)
    
        if not queue.empty():
            host = yield from queue.get()
            tasks.append(asyncio.async(run_client(host)))
        else:
            if not tasks:
                break
    loop.stop()


if __name__ == '__main__':

    _host_dict = parse_hosts()

    loop = asyncio.get_event_loop()

    queue = asyncio.Queue()
#    asyncio.async(manager(loop, queue))

    for host in ['archt01', 'archt02', 'archt03', 'archt04', 'archt05']*100:
        queue.put_nowait(host)

    loop.run_until_complete(manager(loop, queue))
