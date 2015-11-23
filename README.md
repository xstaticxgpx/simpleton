# simpleton
Simple agentless host management using the SSH protocol.

# Usage

Configure SSH authorized_keys with the public key of the management host, ideally with no-pty, as such:

```
# cat /root/.ssh/authorized_keys 
no-pty,from="mgmt01,10.0.0.1" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDJk0StZE0eVXSRUR/M/5FHzhEv3CHft5pFhQrhokpsNJWXCLF2tXyZtgXtxPcGqUCr+ZEuwaQef8QyBWzazBdJARFZ/5wkdimYpUTV5xb2uK+99CnDEOBjmLNpX6CjbPt7CxClWzoKQMlnNw9JciUYkAPjYuijXUNFZBV2WTj3mbZ7ns71j/w7Uru2nxA4qH50ygq9rENVWj75h27CF2zjujQKTsUdR2MID+JHUPtIc5l7s+PTlcgFurfkzGPaNZ0hUqLljxdxKBYNuwEix9M0gfcnJCdVQ8FbNWwhEme5U2by0/umL6jr6Ef7pP2RUHN29WFnvPANxEdwOnLBz2LRObXi8L5NJ4I30zuj/fq/CDYbSeyID21OnrpP5VomBsbhKMoceRjgjMi3NwVLzldYdT6TGvJFkN5tvvljoN2P1278VrlJmvFiMgIGCcAcmXXLT9cNvevuS3f6OnwGowS93kTs4GgaOil8YI5iRTcUlNAHAeH1bY43sf1Ra+mV/Bn2ByULWsCbLCkzKVrDDu48L3KloN6O23N/hGETWaDYMXAanetxtiTeUYklaPRS217rOm+EjgbEAL/UVE2jFWenWLOU2TSdHVHN969fsLDIXqivcvk/LgezXGf/cVU7PFFwjeXU32n4CAt1Z5Zk/AKdLRrM0sRZM/kLr8zCV9mj/w== root@mgmt01
```

And execute simpleton from the management host:

```
mgmt01$ sudo ./simpleton.py -H archt -- 'echo `hostname`: `whoami`'
#?# [2015-11-23T13:26:32.886Z] Parsed 10 entries from /etc/hosts
#?# [2015-11-23T13:26:33.074Z] [archt04:root] Connection initiated
#?# [2015-11-23T13:26:33.100Z] [archt05:root] Connection initiated
#?# [2015-11-23T13:26:33.116Z] [archt01:root] Connection initiated
#?# [2015-11-23T13:26:33.117Z] [archt02:root] Connection initiated
#?# [2015-11-23T13:26:33.117Z] [archt03:root] Connection initiated
#~# [2015-11-23T13:26:33.506Z] [archt01:root] echo `hostname`: `whoami`
archt01: root
#~# [2015-11-23T13:26:33.923Z] [archt03:root] echo `hostname`: `whoami`
archt03: root
#~# [2015-11-23T13:26:33.975Z] [archt04:root] echo `hostname`: `whoami`
archt04: root
#~# [2015-11-23T13:26:34.058Z] [archt05:root] echo `hostname`: `whoami`
archt05: root
#~# [2015-11-23T13:26:34.139Z] [archt02:root] echo `hostname`: `whoami`
archt02: root
#!# [2015-11-23T13:26:34.295Z] Connected to 5 hosts successfully, 0 hosts failed: 
#!# [2015-11-23T13:26:34.295Z] Failed commands on 0 hosts: 
#!# [2015-11-23T13:26:34.295Z] Finished run in 1408.684ms
```
