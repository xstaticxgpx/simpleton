# simpleton
Simple agentless host management using the SSH protocol.

Designed with asynchronous SSH calls implemented via [asyncssh](https://github.com/ronf/asyncssh)

# Configuration
```
# 100ms poll cycle (used in SSHManager)
YIELD_TIMEOUT=0.1
# Max. 50 concurrent sessions
MAX_CONCURRENT=50
# Wait max. 10s for connection
CONNECT_TIMEOUT=10
# Max 5min session time
SESSION_TIMEOUT=300
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

On the remote host(s), configure SSH authorized_keys with the public key for the management host:

```
remote-host# cat /root/.ssh/authorized_keys 
no-pty,from="mgmt-host,10.0.0.1" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDJk0StZE0eVXSRUR/M/5FHzhEv3CHft5pFhQrhokpsNJWXCLF2tXyZtgXtxPcGqUCr+ZEuwaQef8QyBWzazBdJARFZ/5wkdimYpUTV5xb2uK+99CnDEOBjmLNpX6CjbPt7CxClWzoKQMlnNw9JciUYkAPjYuijXUNFZBV2WTj3mbZ7ns71j/w7Uru2nxA4qH50ygq9rENVWj75h27CF2zjujQKTsUdR2MID+JHUPtIc5l7s+PTlcgFurfkzGPaNZ0hUqLljxdxKBYNuwEix9M0gfcnJCdVQ8FbNWwhEme5U2by0/umL6jr6Ef7pP2RUHN29WFnvPANxEdwOnLBz2LRObXi8L5NJ4I30zuj/fq/CDYbSeyID21OnrpP5VomBsbhKMoceRjgjMi3NwVLzldYdT6TGvJFkN5tvvljoN2P1278VrlJmvFiMgIGCcAcmXXLT9cNvevuS3f6OnwGowS93kTs4GgaOil8YI5iRTcUlNAHAeH1bY43sf1Ra+mV/Bn2ByULWsCbLCkzKVrDDu48L3KloN6O23N/hGETWaDYMXAanetxtiTeUYklaPRS217rOm+EjgbEAL/UVE2jFWenWLOU2TSdHVHN969fsLDIXqivcvk/LgezXGf/cVU7PFFwjeXU32n4CAt1Z5Zk/AKdLRrM0sRZM/kLr8zCV9mj/w== root@mgmt-host
```

And execute simpleton from the management host:

```
mgmt-host$ sudo ./simpleton.py -H archt -- 'echo `hostname`: `whoami`' '[ "$HOSTNAME" == "archt05" ] && exit 0'
#?# [2015-11-25T17:35:34.049Z] Parsed 11 entries from /etc/hosts
#+# [2015-11-25T17:35:34.231Z] [archt02:root] SSH connection initiated
#+# [2015-11-25T17:35:34.236Z] [archt01:root] SSH connection initiated
#+# [2015-11-25T17:35:34.238Z] [archt04:root] SSH connection initiated
#+# [2015-11-25T17:35:34.243Z] [archt03:root] SSH connection initiated
#+# [2015-11-25T17:35:34.244Z] [archt05:root] SSH connection initiated
#~# [2015-11-25T17:35:34.305Z] [archt02:root] echo `hostname`: `whoami`
archt02: root

#!# [2015-11-25T17:35:34.387Z] [archt02:root] [ "$HOSTNAME" == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-25T17:35:34.387Z] [archt02:root] Failure detected, breaking...
#~# [2015-11-25T17:35:34.396Z] [archt05:root] echo `hostname`: `whoami`
archt05: root

#~# [2015-11-25T17:35:34.424Z] [archt01:root] echo `hostname`: `whoami`
archt01: root

#!# [2015-11-25T17:35:34.506Z] [archt01:root] [ "$HOSTNAME" == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-25T17:35:34.506Z] [archt01:root] Failure detected, breaking...
#~# [2015-11-25T17:35:34.621Z] [archt04:root] echo `hostname`: `whoami`
archt04: root

#~# [2015-11-25T17:35:34.693Z] [archt03:root] echo `hostname`: `whoami`
archt03: root

#!# [2015-11-25T17:35:34.703Z] [archt04:root] [ "$HOSTNAME" == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-25T17:35:34.703Z] [archt04:root] Failure detected, breaking...
#!# [2015-11-25T17:35:34.775Z] [archt03:root] [ "$HOSTNAME" == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-25T17:35:34.775Z] [archt03:root] Failure detected, breaking...
#*# [2015-11-25T17:35:44.050Z] [archt06] SSH connection failed: Timeout
#?# [2015-11-25T17:35:44.175Z] ----------------------------------------
#~# [2015-11-25T17:35:44.175Z] Finished run in 10125.379ms
#+# [2015-11-25T17:35:44.175Z] archt01 command failed: [ "$HOSTNAME" == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-25T17:35:44.175Z] archt02 command failed: [ "$HOSTNAME" == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-25T17:35:44.175Z] archt03 command failed: [ "$HOSTNAME" == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-25T17:35:44.175Z] archt04 command failed: [ "$HOSTNAME" == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-25T17:35:44.175Z] archt06 connection failed: Timeout
#?# [2015-11-25T17:35:44.175Z] ----------------------------------------
#~# [2015-11-25T17:35:44.175Z] Saved output script to ./out.sh
```

