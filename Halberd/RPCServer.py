# -*- coding: iso-8859-1 -*-

"""Distributed scan server.

This is the key component for halberd's distributed scanning architecture.
"""
__revision__ = '$Id: RPCServer.py,v 1.3 2004/04/07 00:35:10 rwx Exp $'

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


import sys
import base64
import pickle
import SocketServer

import hlbd.util
import hlbd.crew


class RPCRequestHandler(SocketServer.StreamRequestHandler):
    """Serves scanning requests.

    Those requests are pickled ScanTask instances encoded in Base64 and
    finished by an extra LF.
    """
    def handle(self):
        print 'RPCServer: connection from', self.client_address

        sys.stdout.flush()

        request = ''
        for line in self.rfile:
            if line == '\n':
                break
            request += line

        sys.stdout.flush()

        request = base64.decodestring(request)

        scantask = pickle.loads(request)
        # We remove some information to avoid recursive scans.
        scantask.rpc_servers = None
        scantask.isDistributed = False

        workcrew = hlbd.crew.WorkCrew(scantask)
        clues = workcrew.scan()

        # xxx - pickle.dumps(clues) may take a long time to run thus
        # invalidating the timestamp. Find a way to avoid this problem.
        
        timestamp = hlbd.util.utctime()
        response = pickle.dumps((timestamp, clues))
        self.wfile.write(response)
        

# A ThreadingTCPServer is not advisable because it would clash with signal
# handling in the WorkCrew's main thread.
class RPCServer(SocketServer.TCPServer):
    """Serves scanning requests, one at a time.
    """
    allow_reuse_address = True

    def __init__(self, server_address=('', 23), RequestHandlerClass=RPCRequestHandler):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)


# vim: ts=4 sw=4 et
