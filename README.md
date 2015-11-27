# simpleton

Simple agentless host management using the SSH protocol.

Built for python3.4, does not implement [PEP-492](https://www.python.org/dev/peps/pep-0492/)

Utilizes [asyncio](https://docs.python.org/3.4/library/asyncio.html) for event driven concurrency, with SSH capability implemented via [asyncssh](https://github.com/ronf/asyncssh)

# Configuration

```
## Global configuration

# 96 concurrent sessions max.
MAX_CONCURRENT = 96
# Wait max. 10s for connection stand up
CONNECT_TIMEOUT = 10
# 5min session timeout (no input received)
SESSION_TIMEOUT = 300
```

# Usage

```
$ ./simpleton.py --help
usage: simpleton.py [-h] [--hostsfile [path]] [-H host [host ...]]
                    [-X host [host ...]] [-f [path]] [-o [path]]
                    [cmd [cmd ...]]

Simple agentless host management using the SSH protocol.

positional arguments:
  cmd                   Command(s) to execute on the remote hosts.

optional arguments:
  -h, --help            show this help message and exit
  --hostsfile [path]    Path to hosts file (default: /etc/hosts)
  -H host [host ...], --host host [host ...]
                        Complete or partial hostnames
  -X host [host ...], --exclude host [host ...]
                        Exclude complete or partial hostnames
  -f [path], --file [path]
                        Command list file
  -o [path], --output [path]
                        Path to save output script (default: ./out.sh)
                        Automatically overwritten.
```

# Quick start

On the remote host(s), configure SSH authorized_keys with the public key for the management host:

```
remote-host# cat /root/.ssh/authorized_keys 
no-pty,from="mgmt-host,10.0.0.1" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDJk0StZE0eVXSRUR/M/5FHzhEv3CHft5pFhQrhokpsNJWXCLF2tXyZtgXtxPcGqUCr+ZEuwaQef8QyBWzazBdJARFZ/5wkdimYpUTV5xb2uK+99CnDEOBjmLNpX6CjbPt7CxClWzoKQMlnNw9JciUYkAPjYuijXUNFZBV2WTj3mbZ7ns71j/w7Uru2nxA4qH50ygq9rENVWj75h27CF2zjujQKTsUdR2MID+JHUPtIc5l7s+PTlcgFurfkzGPaNZ0hUqLljxdxKBYNuwEix9M0gfcnJCdVQ8FbNWwhEme5U2by0/umL6jr6Ef7pP2RUHN29WFnvPANxEdwOnLBz2LRObXi8L5NJ4I30zuj/fq/CDYbSeyID21OnrpP5VomBsbhKMoceRjgjMi3NwVLzldYdT6TGvJFkN5tvvljoN2P1278VrlJmvFiMgIGCcAcmXXLT9cNvevuS3f6OnwGowS93kTs4GgaOil8YI5iRTcUlNAHAeH1bY43sf1Ra+mV/Bn2ByULWsCbLCkzKVrDDu48L3KloN6O23N/hGETWaDYMXAanetxtiTeUYklaPRS217rOm+EjgbEAL/UVE2jFWenWLOU2TSdHVHN969fsLDIXqivcvk/LgezXGf/cVU7PFFwjeXU32n4CAt1Z5Zk/AKdLRrM0sRZM/kLr8zCV9mj/w== root@mgmt-host
```

And execute simpleton from the management host:

```
mgmt-host$ sudo ./simpleton.py -H archt -- 'echo `hostname`: `whoami`' '[ $HOSTNAME == "archt05" ] && exit 0'
#?# [2015-11-27T06:59:36.000Z] Parsed 11 entries from /etc/hosts
#?# [2015-11-27T06:59:36.000Z] Matched 6 hosts like ['archt'], unlike ''
#+# [2015-11-27T06:59:36.185Z] [archt04:root] SSH connection initiated
#+# [2015-11-27T06:59:36.188Z] [archt02:root] SSH connection initiated
#+# [2015-11-27T06:59:36.190Z] [archt05:root] SSH connection initiated
#+# [2015-11-27T06:59:36.191Z] [archt01:root] SSH connection initiated
#+# [2015-11-27T06:59:36.197Z] [archt03:root] SSH connection initiated
#~# [2015-11-27T06:59:36.393Z] [archt02:root] echo `hostname`: `whoami`
archt02: root

#~# [2015-11-27T06:59:36.429Z] [archt04:root] echo `hostname`: `whoami`
archt04: root

#~# [2015-11-27T06:59:36.430Z] [archt03:root] echo `hostname`: `whoami`
archt03: root

#~# [2015-11-27T06:59:36.431Z] [archt05:root] echo `hostname`: `whoami`
archt05: root

#~# [2015-11-27T06:59:36.431Z] [archt01:root] echo `hostname`: `whoami`
archt01: root

#!# [2015-11-27T06:59:36.475Z] [archt02:root] [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-27T06:59:36.475Z] [archt02:root] Failure detected, breaking...
#!# [2015-11-27T06:59:36.513Z] [archt03:root] [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-27T06:59:36.513Z] [archt03:root] Failure detected, breaking...
#!# [2015-11-27T06:59:36.513Z] [archt04:root] [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-27T06:59:36.513Z] [archt04:root] Failure detected, breaking...
#!# [2015-11-27T06:59:36.515Z] [archt01:root] [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-27T06:59:36.516Z] [archt01:root] Failure detected, breaking...
#*# [2015-11-27T06:59:46.010Z] [archt06] SSH connection failed: TimeoutError()
#?# [2015-11-27T06:59:46.010Z] ----------------------------------------
#~# [2015-11-27T06:59:46.010Z] Successfully ran on 1 hosts in 10.011s
#+# [2015-11-27T06:59:46.011Z] Failed on 5 hosts:
#+# [2015-11-27T06:59:46.011Z] archt01 command failed: [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-27T06:59:46.011Z] archt02 command failed: [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-27T06:59:46.011Z] archt03 command failed: [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-27T06:59:46.011Z] archt04 command failed: [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-27T06:59:46.011Z] archt06 connection failed: TimeoutError()
#?# [2015-11-27T06:59:46.011Z] ----------------------------------------
#~# [2015-11-27T06:59:46.011Z] Saved output script to ./out.sh
```

