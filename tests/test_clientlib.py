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


"""Unit tests for hlbd.clientlib
"""

__revision__ = '$Id: test_clientlib.py,v 1.1 2004/01/31 14:03:59 rwx Exp $'


import unittest
import urlparse

import hlbd.clientlib as clientlib


class TestHTTPClient(unittest.TestCase):

    def setUp(self):
        self.client = clientlib.HTTPClient()

    def tearDown(self):
        del self.client

    def testGetHostAndPort(self):
        hostname, port = self.client._getHostAndPort('localhost:8080')
        self.failUnless(hostname == 'localhost' and port == 8080)
        hostname, port = self.client._getHostAndPort('localhost')
        self.failUnless(hostname == 'localhost' \
                        and port == clientlib.default_port)
        hostname, port = self.client._getHostAndPort('localhost:abc')
        self.failUnless(port == clientlib.default_port)

    def testFillTemplate(self):
        def get_request(url):
            scheme, netloc, url, params, query, fragment = \
                urlparse.urlparse(url)
            hostname, port = self.client._getHostAndPort(netloc)
            return self.client._fillTemplate(hostname, url,
                                             params, query, fragment)

        req = get_request('http://www.real-iti.com:23/test?blop=777')
        self.failUnless(req.splitlines()[:2] == \
                        ['HEAD /test?blop=777 HTTP/1.1',
                         'Host: www.real-iti.com'])

        req = get_request('http://www.synnergy.net/~rwx/test;blop?q=something')
        self.failUnless(req.splitlines()[:2] == \
                        ['HEAD /~rwx/test;blop?q=something HTTP/1.1',
                         'Host: www.synnergy.net'])

        req = get_request('http://agartha:8080')
        self.failUnless(req.splitlines()[0] == 'HEAD / HTTP/1.1')

    def testAntiCache(self):
        req = self.client._fillTemplate('localhost', '/index.html')
        self.failUnless(req.splitlines()[2:4] == \
                        ['Pragma: no-cache', 'Cache-control: no-cache'])

    def testSendRequestSanityCheck(self):
        self.failUnlessRaises(clientlib.InvalidScheme,
                              self.client.putRequest, '127.0.0.1',
                                                       'gopher://blop')

    def testSendRequestToLocal(self):
        try:
            self.client.putRequest('127.0.0.1', 'http://agartha:8000')
        except clientlib.ConnectionRefused:
            return

        try:
            reply = self.client.getReply()
        except clientlib.UnknownReply:
            pass

#        if reply:
#            print len(reply)

    def testSendRequestToRemote(self):
        self.client.putRequest('212.204.249.161', 'http://www.synnergy.net')
        reply = self.client.getReply()
        self.failUnless(reply.splitlines()[0].startswith('HTTP/'))

    def testGetHeaders(self):
        reply = self.client.getHeaders('212.204.249.161',
                                       'http://www.synnergy.net')
        self.failUnless(reply is not None)
        

if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
