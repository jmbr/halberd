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


"""Utilities for clue storage.
"""

__revision__ = '$Id: file.py,v 1.1 2004/02/25 04:01:15 rwx Exp $'


import csv
import types

from hlbd.clues.Clue import Clue


class InvalidFile(Exception):
    """The loaded file is not a valid clue file.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


def save(filename, clues):
    """Save a clues to a file.

    @param filename: Name of the file where the clues will be written to.
    @type filename: C{str}

    @param clues: Sequence of clues to write.
    @type clues: C{list}
    """
    # Create or truncate the destination file.
    cluefp = open(filename, 'w+')
    writer = csv.writer(cluefp)

    for clue in clues:
        # Store the most relevant clue information.
        writer.writerow((clue.getCount(), clue._local, clue.headers))

    cluefp.close()


def load(filename):
    """Load clues from file.

    @param filename: Name of the files where the clues are stored.
    @type filename: C{str}

    @return: Clues extracted from the file.
    @rtype: C{list}

    @raise InvalidFile: In case there's a problem while reinterpreting the
    clues.
    """
    cluefp = open(filename, 'r')
    reader = csv.reader(cluefp)

    clues = []
    for tup in reader:
        try:
            count, localtime, headers = tup
        except ValueError:
            raise InvalidFile, 'Cannot unpack fields'

        # Recreate the current clue.
        clue = Clue()
        try:
            clue._count = int(count)
            clue._local = float(localtime)
        except ValueError:
            raise InvalidFile, 'Could not convert fields'

        # This may be risky from a security standpoint.
        clue.headers = eval(headers, {}, {})
        if not (isinstance(clue.headers, types.ListType) or
                isinstance(clue.headers, types.TupleType)):
            raise InvalidFile, 'Wrong clue header field'
        clue.parse(clue.headers)

        clues.append(clue)

    cluefp.close()
    return clues


# vim: ts=4 sw=4 et
