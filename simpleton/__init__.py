#!/usr/bin/env python3
"""
Simpleton's goal is to provide an extremely simple alternative to host/configuration management.

This is accomplished by using the SSH protocol for an agentless design.

As opposed to a forked or threaded model, I'm opting to try and use an asynchronous implementation using `asyncssh`
"""

import argparse

from simpleton.logging import *

VERSION='v0.1'

# Setting up parameter parsing
parser = argparse.ArgumentParser(description='Agentless host management using SSH protocol.')

parser.add_argument(dest='cmdlist', metavar='cmd', nargs='*', help='Command(s) to execute on the remote hosts.')

parser.add_argument('-H', '--host', dest='hostmatch', nargs='+', help='Complete or partial hostnames')
