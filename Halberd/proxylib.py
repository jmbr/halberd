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


"""Proxy module.
"""

__revision__ = '$Id: proxylib.py,v 1.1 2004/03/03 13:21:19 rwx Exp $'


import sys
import socket
from SocketServer import *


# XXX Refactor some network routines into a separate module (hlbd.netlib or
# something).
default_timeout = 5


class ProxyServer(TCPServer):
#class ProxyServer(TCPServer, ThreadingMixIn):

    allow_reuse_address = True


class ProxyHandler(StreamRequestHandler):
    """Extremely simple HTTP proxy handler.

    @ivar target_addr: Network address of the target.
    @type target_addr: C{tuple}

    @ivar target_host: The target's FQDN.
    @type target_host: C{str}
    """

    target_addr = ()
    target_host = ''

    def setup(self):
        StreamRequestHandler.setup(self)

        print 'connection from %s' % `self.client_address`

        self.target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.target.settimeout(default_timeout)
        print self.target_addr
        self.target.connect(self.target_addr)


    def handle(self):
        """Handle a proxy request.
        """

        # File summary
        # ============
        #
        # self.rfile -> What is read from the local socket
        # self.wfile -> What is written to the local socket
        # proxyrfile -> What is read from the socket connected to remote
        # proxywfile -> What is written to the socket connected to remote

        proxyrfile = self.target.makefile('rb', self.rbufsize)
        proxywfile = self.target.makefile('wb', self.wbufsize)

        found_terminator = lambda l: l == '\r\n' or l == '\n' or l == ''

        for line in self.rfile:
            if line.startswith('GET'):
                print line
            proxywfile.write(line)

            if found_terminator(line):
                break

        while True:
            try:
                data = self.target.recv(4096)
            except socket.timeout:
                break

            if not data:
                break

            print len(data)
            self.wfile.write(data)


    def finish(self):
        StreamRequestHandler.finish(self)
        self.target.close()


def main():
    target_addr = (sys.argv[1], int(sys.argv[2]))
    server_addr = ('', 8008)
    
    ProxyHandler.target_addr = target_addr
    ProxyHandler.target_host = sys.argv[1]

    httpd = ProxyServer(server_addr, ProxyHandler)

    sa = httpd.socket.getsockname()
    print "proxy server listening on %s:%d" % (sa[0] or '0.0.0.0', sa[1])

    httpd.serve_forever()

if __name__ == '__main__':
    main()


# vim: ts=4 sw=4 et
