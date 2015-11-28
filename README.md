# simpleton

Simple asynchronous host management using SSH

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

Define hosts in /etc/hosts on the management host, then run simpleton:

```
mgmt-host$ sudo ./simpleton.py -H remote-host -- 'echo `hostname`: `whoami`' 'ps aux'
#?# [2015-11-28T06:17:29.546Z] Parsed 10 entries from /etc/hosts
#?# [2015-11-28T06:17:29.546Z] Matched 1 hosts like ['remote-host'], unlike ''
#+# [2015-11-28T06:17:29.722Z] [remote-host:root] SSH connection initiated
#~# [2015-11-28T06:17:29.843Z] [remote-host:root] echo `hostname`: `whoami`
archt01: root

#~# [2015-11-28T06:17:29.926Z] [remote-host:root] ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  35772  4672 ?        Ss   Nov23   0:04 /usr/lib/systemd/systemd
root        15  0.0  0.1  87820 21320 ?        Ss   Nov23   0:04 /usr/lib/systemd/systemd-journald
root        22  0.0  0.0  15420  1816 ?        Ss   Nov23   0:01 /usr/lib/systemd/systemd-logind
dbus        24  0.0  0.0  37220  2032 ?        Ss   Nov23   0:03 /usr/bin/dbus-daemon --system --address=systemd: --nofork --nopidfile --systemd-activation
systemd+    31  0.0  0.0  28516   260 ?        Ss   Nov23   0:00 /usr/lib/systemd/systemd-networkd
root        33  0.0  0.0   6348   308 console  Ss+  Nov23   0:00 /sbin/agetty --noclear --keep-baud console 115200 38400 9600 vt220
root        79  0.0  0.0   6744  1168 ?        Ss   Nov23   0:00 /usr/bin/dhcpcd -q -w host0
root        91  0.0  0.0  34164   788 ?        Ss   Nov23   0:00 /usr/lib/systemd/systemd --user
root        92  0.0  0.0  97044  1332 ?        S    Nov23   0:00 (sd-pam)
root      2077  0.0  0.0  40420  4300 ?        Ss   Nov25   0:00 /usr/bin/sshd -D
root     11382  0.0  0.0  99892  6952 ?        Ss   01:17   0:00 sshd: root@notty
root     11389  0.0  0.0  34716  2808 ?        Rs   01:17   0:00 ps aux

#?# [2015-11-28T06:17:29.927Z] ----------------------------------------
#~# [2015-11-28T06:17:29.927Z] Successfully ran on 1 hosts in 0.381s
#~# [2015-11-28T06:17:29.927Z] No errors reported.
#?# [2015-11-28T06:17:29.927Z] ----------------------------------------
#~# [2015-11-28T06:17:29.927Z] Saved output script to ./out.sh
```

# Further examples

Running on multiple hosts in parallel:

```
mgmt-host$ sudo ./simpleton.py -H archt -- 'echo `hostname`: `whoami`'
#?# [2015-11-28T06:19:24.729Z] Parsed 10 entries from /etc/hosts
#?# [2015-11-28T06:19:24.729Z] Matched 5 hosts like ['archt'], unlike ''
#+# [2015-11-28T06:19:24.919Z] [archt05:root] SSH connection initiated
#+# [2015-11-28T06:19:24.919Z] [archt02:root] SSH connection initiated
#+# [2015-11-28T06:19:24.921Z] [archt01:root] SSH connection initiated
#+# [2015-11-28T06:19:24.922Z] [archt04:root] SSH connection initiated
#+# [2015-11-28T06:19:24.924Z] [archt03:root] SSH connection initiated
#~# [2015-11-28T06:19:25.157Z] [archt05:root] echo `hostname`: `whoami`
archt05: root

#~# [2015-11-28T06:19:25.158Z] [archt02:root] echo `hostname`: `whoami`
archt02: root

#~# [2015-11-28T06:19:25.159Z] [archt04:root] echo `hostname`: `whoami`
archt04: root

#~# [2015-11-28T06:19:25.159Z] [archt03:root] echo `hostname`: `whoami`
archt03: root

#~# [2015-11-28T06:19:25.159Z] [archt01:root] echo `hostname`: `whoami`
archt01: root

#?# [2015-11-28T06:19:25.161Z] ----------------------------------------
#~# [2015-11-28T06:19:25.161Z] Successfully ran on 5 hosts in 0.432s
#~# [2015-11-28T06:19:25.161Z] No errors reported.
#?# [2015-11-28T06:19:25.161Z] ----------------------------------------
#~# [2015-11-28T06:19:25.161Z] Saved output script to ./out.sh
```

Failure reporting:

```
mgmt-host$ sudo ./simpleton.py -H archt -- 'echo `hostname`: `whoami`' '[ $HOSTNAME == "archt05" ] && exit 0'
#?# [2015-11-28T06:22:04.551Z] Parsed 11 entries from /etc/hosts
#?# [2015-11-28T06:22:04.552Z] Matched 6 hosts like ['archt'], unlike ''
#+# [2015-11-28T06:22:04.737Z] [archt05:root] SSH connection initiated
#+# [2015-11-28T06:22:04.738Z] [archt03:root] SSH connection initiated
#+# [2015-11-28T06:22:04.742Z] [archt04:root] SSH connection initiated
#+# [2015-11-28T06:22:04.743Z] [archt02:root] SSH connection initiated
#+# [2015-11-28T06:22:04.745Z] [archt01:root] SSH connection initiated
#~# [2015-11-28T06:22:04.977Z] [archt05:root] echo `hostname`: `whoami`
archt05: root

#~# [2015-11-28T06:22:04.978Z] [archt04:root] echo `hostname`: `whoami`
archt04: root

#~# [2015-11-28T06:22:04.979Z] [archt01:root] echo `hostname`: `whoami`
archt01: root

#~# [2015-11-28T06:22:04.979Z] [archt02:root] echo `hostname`: `whoami`
archt02: root

#~# [2015-11-28T06:22:04.980Z] [archt03:root] echo `hostname`: `whoami`
archt03: root

#!# [2015-11-28T06:22:05.061Z] [archt04:root] [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-28T06:22:05.061Z] [archt04:root] Failure detected, breaking...
#!# [2015-11-28T06:22:05.063Z] [archt01:root] [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-28T06:22:05.063Z] [archt01:root] Failure detected, breaking...
#!# [2015-11-28T06:22:05.064Z] [archt02:root] [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-28T06:22:05.064Z] [archt02:root] Failure detected, breaking...
#!# [2015-11-28T06:22:05.065Z] [archt03:root] [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#!# [2015-11-28T06:22:05.065Z] [archt03:root] Failure detected, breaking...
#*# [2015-11-28T06:22:14.562Z] [archt06] SSH connection failed: TimeoutError()
#?# [2015-11-28T06:22:14.563Z] ----------------------------------------
#~# [2015-11-28T06:22:14.563Z] Successfully ran on 1 hosts in 10.011s
#+# [2015-11-28T06:22:14.563Z] Failures on 5 hosts:
#+# [2015-11-28T06:22:14.563Z] archt01 command failed: [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-28T06:22:14.563Z] archt02 command failed: [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-28T06:22:14.563Z] archt03 command failed: [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-28T06:22:14.563Z] archt04 command failed: [ $HOSTNAME == "archt05" ] && exit 0 (exit code 1)
#+# [2015-11-28T06:22:14.563Z] archt06 connection failed: TimeoutError()
#?# [2015-11-28T06:22:14.563Z] ----------------------------------------
#~# [2015-11-28T06:22:14.563Z] Saved output script to ./out.sh
```

