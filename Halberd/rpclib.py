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
This is useful when the user wants to send a lot of traffic to the target but
it doesn't have enough bandwith with just one computer/network. In that case,
he would start halberd in sever mode on one or several machines and from
another computer he would start the program in client mode telling it where the
halberd servers are located.
The RPC mechanism is the XML-RPC protocol.
"""

__revision__ = '$Id: rpclib.py,v 1.1 2004/02/07 13:28:02 rwx Exp $'


import pickle
import xmlrpclib
import SimpleXMLRPCServer

import hlbd.scanlib as scanlib


class RPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
    def __init__(self, addr,
                 requestHandler=SimpleXMLRPCServer.SimpleXMLRPCRequestHandler,
                 logRequests=1):
        self.allow_reuse_address = True
        SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(self, addr,
                requestHandler, logRequests)


def client(serv_url, addr, url, scantime):
    server = xmlrpclib.ServerProxy(serv_url, None, None, 1, 1)
    #server = xmlrpclib.ServerProxy(serv_url)
#    return pickle.loads(server.scan(addr, url, scantime, True))
    return server.scan(addr, url, scantime, True)

def server(addr):
    def scan(addr, url, scantime, verbose):
        return scanlib.scan(addr, url, scantime, verbose)
#        return pickle.dumps(scanlib.scan(addr, url, scantime, verbose))

    rpcserver = RPCServer(addr)

    rpcserver.register_introspection_functions()
    rpcserver.register_function(scan)

    rpcserver.serve_forever()
    # Handle one request.
    #server.handle_request()


# vim: ts=4 sw=4 et
