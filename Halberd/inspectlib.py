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


"""Clue inspection module.
"""

__revision__ = '$Id: inspectlib.py,v 1.1 2004/02/02 07:21:08 rwx Exp $'


import difflib
import hlbd.cluelib as cluelib


def get_diffs(one, other):
    matcher = difflib.SequenceMatcher(None, one, other)
    isdiff = lambda opcode: (opcode[0] != 'equal')
    return filter(isdiff, matcher.get_opcodes())

def get_diff_fields(clues, threshold):
    # XXX DOCUMENT AND REFACTOR!!
    stop = False
    i = 0
    ranking = {}
    while not stop:
        j = i + 1
        if j == len(clues):
            stop = True
            j = 0
        
        one, other = clues[i].headers, clues[j].headers
        for tag, alo, ahi, blo, bhi in get_diffs(one, other):
            for name, value in one[alo:ahi] + other[blo:bhi]:
                try:
                    ranking[name] += 1
                except KeyError:
                    ranking[name] = 1
        i += 1

    sorted = [(count, field) for field, count in ranking.items()]
    sorted.sort()
    sorted.reverse()

#    for count, field in sorted:
#        print '%s (%.3f%%)' % (field, count * 100.0 / (len(clues)* 2))

    return [field for count, field in sorted if count * 100 / (len(clues) * 2) >= threshold]


# vim: ts=4 sw=4 et
