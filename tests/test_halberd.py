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


"""Unit tests for halberd.Halberd
"""

__revision__ = '$Id: test_halberd.py,v 1.2 2004/03/02 00:54:10 rwx Exp $'


import unittest

import halberd
import hlbd.clues.analysis as analysis


class testNetutils(unittest.TestCase):

    def testHostname(self):
        url = 'http://agartha/'
        self.assertEqual(halberd.hostname(url), 'agartha')

        url = 'http://agartha:777'
        self.assertEqual(halberd.hostname(url), 'agartha')

        url = 'http://agartha:777:1:2/'
        self.assertEqual(halberd.hostname(url), 'agartha')

        url = 'agartha'
        self.assertEqual(halberd.hostname(url), '')


#def testAddresses(self):
#    self.failUnlessEqual(halberd.addresses('abcdefghijk'), ())
#    self.failUnless(halberd.addresses('agartha') != ())


class TestHalberd(unittest.TestCase):

    def setUp(self):
        self.h = halberd.Halberd()

    def tearDown(self):
        pass

    def testSetURL(self):
        url = 'agartha'
        self.h.setURL(url)
        self.assertEqual(self.h.url, 'http://' + url)

        url = 'http://fnord'
        self.h.setURL(url)
        self.assertEqual(self.h.url, url)

        url = 'https://fnord'
        self.h.setURL(url)
        self.assertEqual(self.h.url, url)

    def testSetAddr(self):
        """This test addresses a bug found when developing bulkscan.py
        """
        self.h.clues = [1, 2, 3]
        self.h.setAddr(('', 0))
        self.failUnlessEqual(self.h.clues, [])

    def testReadConf(self):
        pass


if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
