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


"""Unit tests for clue storage functionality.
"""

__revision__ = '$Id: test_clues_file.py,v 1.1 2004/02/25 04:01:29 rwx Exp $'


import os
import unittest

import hlbd.clues.file
from hlbd.clues.Clue import Clue


class TestStorage(unittest.TestCase):

    def setUp(self):
        self.clue = Clue()
        self.clue.setTimestamp(100)
        self.clue.headers = eval(r"""[
            ('Date', ' Tue, 24 Feb 2004 17:09:05 GMT'),
            ('Server', ' Apache/2.0.48 (Unix) DAV/2 SVN/0.35.1'),
            ('Content-Location', ' index.html.en'),
            ('Vary', ' negotiate,accept-language,accept-charset'),
            ('TCN', ' choice'),
            ('Last-Modified', ' Sat, 22 Nov 2003 15:56:12 GMT'),
            ('ETag', ' "252ff0-5b0-3b5aff00;253006-961-3b5aff00"'),
            ('Accept-Ranges', ' bytes'),
            ('Content-Length', ' 1456'),
            ('Keep-Alive', ' timeout=15, max=100'),
            ('Connection', ' Keep-Alive'),
            ('Content-Type', ' text/html; charset=ISO-8859-1'),
            ('Content-Language', ' en')
        ]""")
        self.clue.parse(self.clue.headers)

        self.filename = os.path.join('tests', 'data', 'test.clues')

    def tearDown(self):
        pass


    def testSimpleSaveAndLoad(self):
        try:
            hlbd.clues.file.save(self.filename, [self.clue])
            clues = hlbd.clues.file.load(self.filename)
        finally:
            os.unlink(self.filename)

        self.failUnless(len(clues) == 1)
        self.failUnless(clues[0] == self.clue)


if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
