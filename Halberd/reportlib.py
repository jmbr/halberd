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

__revision__ = '$Id: reportlib.py,v 1.3 2004/01/31 13:59:21 rwx Exp $'


import sys


def report(address, clues, hits, outfile=''):
    """Displays detailed report information to the user.

    @param address: Address of the scanned host.
    @type address: C{str}

    @param clues: Clues found and (pressumably) processed by an analyzer.
    @type clues: C{list}

    @param hits: Total number of replies received from the target.
    @type hits: C{int}
    """
    out = (outfile and open(outfile, 'w')) or sys.stdout

    out.write('\nfound %d possibly real server(s) at %s.\n'
              % (len(clues), address))
    for num, clue in enumerate(clues):
        info = clue.info
        out.write('\nserver %d: %s\n' % (num, info['server']))
        out.write('  received %.2f%% of the traffic\n' \
                  % (clue.getCount() * 100 / float(hits)))
        out.write('  time information:\n')
        out.write('    remote clock: %s\n' % info['date'])
        out.write('    difference: %d seconds\n' % (clue.calcDiff() - 3600))
        if info['contloc']:
            out.write('  content-location: %s\n' % info['contloc'])
        if info['cookie']:
            out.write('  cookie: %s\n' % info['cookie'])
        out.write('  header fingerprint: %s\n' % info['digest'])


# vim: ts=4 sw=4 et
