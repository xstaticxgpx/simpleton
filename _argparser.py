#!/usr/bin/env python3

import argparse

# Setting up parameter parsing
parser = argparse.ArgumentParser(description="""
Simple asynchronous host management using SSH
""")

parser.add_argument(dest='cmdlist', metavar='cmd', nargs='*', help='Command(s) to execute on the remote hosts.')

parser.add_argument('--maxconcurrent', '-p', dest='maxconcurrent', metavar='int', nargs='?', default=None,
        help='Override maximum concurrent/parallel sessions')

parser.add_argument('--connecttimeout', '-c', dest='connecttimeout', metavar='int', nargs='?', default=None,
        help='Override connect timeout')

parser.add_argument('--sessiontimeout', '-t', dest='sessiontimeout', metavar='int', nargs='?', default=None,
        help='Override session timeout')

parser.add_argument('--hostsfile', dest='hostsfile', metavar='path', nargs='?', default='/etc/hosts',
        help='Path to hosts file (default: /etc/hosts)')

parser.add_argument('-H', '--host', dest='hostmatch', metavar='host', nargs='+',
        help='Complete or partial hostnames')

parser.add_argument('-X', '--exclude', dest='hostexclude', metavar='host', nargs='+',
        help='Exclude complete or partial hostnames')

parser.add_argument('-i', '--interface', dest='interface', metavar='dev', nargs='?', default=None,
        help='Utilize specific network interface')

parser.add_argument('-f', '--file', dest='cmdfile', metavar='path', nargs='?',
        help='Command list file')

parser.add_argument('-o', '--output', dest='output', metavar='path', nargs='?', default='./out.sh',
        help='Path to save output script (default: ./out.sh) Automatically overwritten.')
