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


"""Remote Procedure Calls.

This module implements client and server functionality to enable halberd to
work as a distributed application.
"""

__revision__ = '$Id: rpclib.py,v 1.4 2004/02/19 14:58:39 rwx Exp $'


import time
import socket
import pickle

import hlbd.scanlib as scanlib


# XXX Improve error checking


def utctime():
    return time.mktime(time.gmtime())


def server(addr, verbose=True):
    """RPC Server.
    """
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    serv.bind(addr)

    if verbose:
        print 'rpcserver: listening on %s:%d' \
              % (addr[0] or '0.0.0.0', addr[1])
        print

    serv.listen(1)

    client = None
    while True:
        if client:
            client.close()

        client, cliaddr = serv.accept()

        client.settimeout(5)
        try:
            data = client.recv(1024)
        except socket.timeout, msg:
            print 'rpcserver: %s' % msg
            continue

        command = pickle.loads(data)
        func, args = command[0], command[1:]
        if func != scanlib.scan:
            print 'rpcserver: invalid function', func
            continue

        if verbose:
            print '%s:%d ->' % (cliaddr[0], cliaddr[1]), func, args

        result = func(*args)
        client.sendall(pickle.dumps((utctime(), result)))

    serv.close()

    
def client(serv_addr, target_addr, url, scantime, parallelism, verbose, results):
    """RPC Client.

    @param results: Mutable object where to put the results + lock
    @type results: C{tuple}
    """
    params = tuple([scanlib.scan, target_addr, url, \
                    scantime, verbose, parallelism])
    request = pickle.dumps(params)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(scantime + 10)
    sock.connect(serv_addr)
    sock.sendall(request)

    data = ''
    while True:
        # XXX This function is vulnerable to an infinite stream of data.
        try:
            chunk = sock.recv(1024)
        except socket.timeout, msg:
            print msg
            return None

        if not chunk:
            break
        data += chunk

    seq, lock = results
    lock.acquire()

    # We receive two things from the target: the time at the moment of sending
    # the data and the list of found clues. To that information we prepend our
    # timestamp at the moment of reception so that clues can be normalized by
    # calculating the difference between our clock and our peer's one.
    payload = []
    payload.append(utctime())
    payload.extend(pickle.loads(data))
    # [local, remote, [clues...]]

    seq.append(payload)

    lock.release()


# vim: ts=4 sw=4 et
