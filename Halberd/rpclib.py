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


"""Remote Procedure Calls for halberd.

This module implements client and server functionality to enable halberd to
work as a distributed application.
"""

__revision__ = '$Id: rpclib.py,v 1.2 2004/02/13 01:24:51 rwx Exp $'


import time
import socket
import pickle

import hlbd.scanlib as scanlib


# XXX Improve error checking


def utctime():
    return time.ctime(time.gmtime())


def server(addr):
    """RPC Server.
    """
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    serv.bind(addr)
    print 'listening on', addr
    serv.listen(1)

    client = None
    while True:
        if client:
            client.close()

        client, clientaddr = serv.accept()

        print clientaddr
        client.settimeout(5)
        try:
            data = client.recv(1024)
        except socket.timeout, msg:
            print msg
            continue

        command = pickle.loads(data)
        func, args = command[0], command[1:]
        if func != scanlib.scan:
            print 'Invalid function', func
            continue

        print func, args

        result = func(*args)
        client.sendall(pickle.dumps((utctime(), result)))

    serv.close()

    
def client(serv_addr, target_addr, url, scantime, verbose, parallelism, results):
    """RPC Client.

    @param results: Place to put the results + lock
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
    import time
    seq.append((utctime(), pickle.loads(data)))
    lock.release()


# vim: ts=4 sw=4 et
