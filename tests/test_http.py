#-*- coding: iso-8859-1 -*-

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

__revision__ = '$Id: test_http.py,v 1.1 2004/01/26 23:07:31 rwx Exp $'


import time
import unittest
import asyncore
from test.test_support import run_unittest

from hlbd.http import *


class TestHTTPClient(unittest.TestCase):

    def setUp(self):
        none = lambda: None
        self.client = HTTPClient(none, none)

    def tearDown(self):
        pass

    def testURLAccessors(self):
        url = 'www.example.net/test?param=fnord'

        self.assertRaises(UnknownProtocol, self.client.setURL,
                          'gopher://example.net')

        self.client.setURL(url)
        self.assertEquals(url, self.client.getURL())
        self.client.setURL('http' + url)
        self.assertEquals('http' + url, self.client.getURL())

    def testHostAndPort(self):
        self.client.setURL('www.example.com')
        self.failUnless(self.client.getPort() == 80)

        self.client.setURL('http://www.example.net:8080')
        self.failUnless(self.client.getPort() == 8080)

        self.assertRaises(InvalidURL, self.client.setURL,
                          'http://www.example.net:abc')

        self.assertRaises(InvalidURL, self.client.setURL,
                          'http://www.example.org:777:8080')

    def testConnect(self):
        url = 'http://agartha:8080'

        self.failUnless(self.client.setURL(url) == self.client)
        t = time.time()
        self.client.open()
        asyncore.loop()

        self.failUnless(int(self.client.getTimestamp()) == int(t))
        #print self.client.getHeaders()

#   def testMultipleConnections(self):
#       url = 'http://www.telefonica.net:80'
#
#       clients = []
#       for x in xrange(10):
#           client = HTTPClient()
#           client.setURL(url).open()
#           clients.append(client)
#
#       asyncore.loop()
#
#       count = 1
#       endtime = time.time() + 10
#       for timestamp, headers in collect_tuples(clients):
#           if time.time() > endtime:
#               break
#
#           print timestamp
#           count += 1
#
#       print count
#               
#def collect_tuples(clients):
#   for client in clients:
#       yield (client.getTimestamp(), client.getHeaders())


if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
