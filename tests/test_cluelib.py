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

__revision__ = '$Id: test_cluelib.py,v 1.2 2004/01/29 13:11:33 rwx Exp $'


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
        id = '123content-location*23'
        self.failUnless(self.clue._normalize(id) == 'contentlocation23')
        id = 'content/location'
        self.failUnless(self.clue._normalize(id) == 'contentlocation')
        id = '*content/location123'
        self.failUnless(self.clue._normalize(id) == 'contentlocation123')


class TestCmpOperators(unittest.TestCase):
    
    def setUp(self):
        self.clue1 = cluelib.Clue()
        self.clue2 = cluelib.Clue()

    def test_cmp_diff(self):
        diff = cluelib.CmpOperator([cluelib.cmp_diff])

        self.clue1._local, self.clue1._remote = 0, 10
        self.clue2._local, self.clue2._remote = 10, 12
        self.failIfEqual(diff.compare(self.clue1, self.clue2), 0)

        self.clue1._local, self.clue1._remote = 0, 10
        self.clue2._local, self.clue2._remote = 10, 20
        self.failUnlessEqual(diff.compare(self.clue1, self.clue2), 0)

    def test_cmp_delta_diff(self):
        diff = cluelib.CmpOperator([cluelib.cmp_delta_diff])
        cluelib.delta = 0

        self.clue1._local, self.clue1._remote = 0, 10
        self.clue2._local, self.clue2._remote = 10, 20
        self.failUnlessEqual(diff.compare(self.clue1, self.clue2), 0)

        cluelib.delta = 1
        self.clue1._local, self.clue1._remote = 0, 11
        self.clue2._local, self.clue2._remote = 10, 20
        self.failUnlessEqual(diff.compare(self.clue1, self.clue2), 0)

        self.clue1._local, self.clue1._remote = 0, 12
        self.failUnlessEqual(diff.compare(self.clue1, self.clue2), -1)

        cluelib.delta = 2
        self.failUnlessEqual(diff.compare(self.clue1, self.clue2), 0)
        self.clue1._local, self.clue1._remote = 0, 13
        self.failUnlessEqual(diff.compare(self.clue1, self.clue2), -1)


if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
