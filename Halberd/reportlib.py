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


"""Output module.
"""

__revision__ = '$Id: reportlib.py,v 1.13 2004/04/06 12:07:29 rwx Exp $'


import sys

import hlbd.clues.analysis as analysis


def report(scantask):
    """Displays detailed report information to the user.
    """
    if scantask.out:
        out = open(scantask.out, 'a')
    else:
        out = sys.stdout

    clues = scantask.analyzed
    hits = analysis.hits(clues)

    # xxx This could be passed by the caller in order to avoid recomputation in
    # case the clues needed a re-analysis.
    diff_fields = analysis.diff_fields(clues)

    out.write('*** %s ' % scantask.url)
    if scantask.addr:
        out.write('(%s) ' % scantask.addr)
    out.write('-> %d real server(s)\n'  % len(clues))

    for num, clue in enumerate(clues):
        info = clue.info

        out.write('\n')
        out.write('server [ %d ]\t\t[ %s ]\n' % (num, info['server'].lstrip()))

        out.write('successful requests\t[ %2d ]\n' % clue.getCount())
        assert hits > 0
        out.write('traffic\t\t\t[ %.2f%% ]\n' \
                  % (clue.getCount() * 100 / float(hits)))

        out.write('difference\t\t[ %d ]\n' % clue.diff)

        if info['contloc']:
            out.write('content-location\t[ %s ]\n' % info['contloc'].lstrip())

        for cookie in info['cookies']:
            out.write('cookie\t\t\t[ %s ]\n' % cookie.lstrip())

        out.write('header fingerprint\t[ %s ]\n' % info['digest'])

        different = [(field, value) for field, value in clue.headers \
                                    if field in diff_fields]
        if different:
            out.write('different headers:\n')
            for field, value in different:
                out.write('  %s:%s\n' % (field, value))

        out.write('headers\t\t\t%s\n' % clue.headers)
        out.write('\n')


# vim: ts=4 sw=4 et
