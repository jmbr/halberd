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

"""Unit test for hlbd.cluelib
"""

__revision__ = '$Id: test_cluelib.py,v 1.4 2004/02/04 04:11:54 rwx Exp $'


import unittest

import hlbd.cluelib as cluelib


class TestClue(unittest.TestCase):

    def setUp(self):
        self.clue = cluelib.Clue()

    def tearDown(self):
        pass

    def testCount(self):
        self.failUnlessEqual(self.clue.getCount(), 1)
        self.clue.incCount()
        self.failUnlessEqual(self.clue.getCount(), 2)
        self.clue.incCount(21)
        self.failUnlessEqual(self.clue.getCount(), 23)

        self.failUnlessRaises(ValueError, self.clue.incCount, 0)
        self.failUnlessRaises(ValueError, self.clue.incCount, -7)

    def testNormalize(self):
        value = '123content-location*23'
        self.failUnless(cluelib.normalize(value) == 'contentlocation23')
        value = 'content/location'
        self.failUnless(cluelib.normalize(value) == 'contentlocation')
        value = '*content/location123'
        self.failUnless(cluelib.normalize(value) == 'contentlocation123')


if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
