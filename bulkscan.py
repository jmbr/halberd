#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright (C) 2004 Juan M. Bello Rivas <rwx@synnergy.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


"""Massive load balancer scanner.
"""

__revision__ = '$Id: bulkscan.py,v 1.1 2004/02/19 14:55:33 rwx Exp $'


import os
import sys
import pickle

import halberd


def error(msg):
    sys.stderr.write(msg)
    sys.stderr.flush()
    sys.exit(-1)

def targets(urlfile):
    for url in urlfile:
        if url == '\r\n' or url == '\n':
            continue

        url = url[:-1]

        hostname = halberd.hostname(url)
        addrs = halberd.addresses(hostname)

        for addr in addrs:
            yield (url, addr)

def main():
    if len(sys.argv) < 2:
        error('usage: %s url-file\n' % sys.argv[0])

    print 'reading urls from', sys.argv[1]

    urlfile = ''
    try:
        urlfile = open(sys.argv[1], 'r')
    except IOError, msg:
        error('open: %s\n' % msg)
            
    for target in targets(urlfile):
        url, addr = target

        h = halberd.Halberd()
        h.setScantime(15)
        h.addr = addr
        h.setURL(url)
        h.verbose = True

        print 'scanning %s (%s)' % (url, addr)

        h.scan()

        f = open(os.path.join('data', addr), 'wb')
        pickle.dump((url, h.clues), f)
        f.close()


if __name__ == '__main__':
    main()


# vim: ts=4 sw=4 et
