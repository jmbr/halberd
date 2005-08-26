# -*- coding: iso-8859-1 -*-

"""Output module.
"""

__revision__ = '$Id: reportlib.py,v 1.17 2005/08/26 11:44:23 rwx Exp $'

# Copyright (C) 2004, 2005 Juan M. Bello Rivas <rwx@synnergy.net>
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


import sys

import hlbd.logger
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
    logger = hlbd.logger.getLogger()

    # xxx This could be passed by the caller in order to avoid recomputation in
    # case the clues needed a re-analysis.
    diff_fields = analysis.diff_fields(clues)

    out.write('=' * 70 + '\n')
    out.write('%s' % scantask.url)
    if scantask.addr:
        out.write(' (%s)' % scantask.addr)
    out.write(': %d real server(s)\n'  % len(clues))
    out.write('=' * 70 + '\n')

    for num, clue in enumerate(clues):
        assert hits > 0
        info = clue.info

        out.write('\n')
#        out.write('-' * 70 + '\n')
        out.write('server %d: %s\n' % (num + 1, info['server'].lstrip()))
        out.write('-' * 70 + '\n\n')

        out.write('difference: %d seconds\n' % clue.diff)

        out.write('successful requests: %d hits (%.2f%% of the traffic)\n' \
                  % (clue.getCount(), clue.getCount() * 100 / float(hits)))

        if info['contloc']:
            out.write('content-location: %s\n' % info['contloc'].lstrip())

        if len(info['cookies']) > 0:
            out.write('cookie(s):\n')
        for cookie in info['cookies']:
            out.write('  %s\n' % cookie.lstrip())

        out.write('header fingerprint: %s\n' % info['digest'])

        different = [(field, value) for field, value in clue.headers \
                                    if field in diff_fields]
        if different:
            out.write('different headers:\n')
            idx = 1
            for field, value in different:
                out.write('  %d. %s:%s\n' % (idx, field, value))
                idx += 1

        if scantask.debug:
            out.write('headers:\n  %s\n' % clue.headers)


# vim: ts=4 sw=4 et
