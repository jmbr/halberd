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

"""Scanning engine for halberd.
"""

__revision__ = '$Id: scanlib.py,v 1.6 2004/02/02 07:32:08 rwx Exp $'


import sys
import time

import hlbd.cluelib as cluelib
import hlbd.clientlib as clientlib


__all__ = ["Scanner"]


_THRESHOLD = 10


class State:
    """Holds the state of the scanner at the current point in time.
    """
    def __init__(self, verbose):
        self.clues = []
        self.verbose = verbose

        self.round = 0
        self.missed = 0
        self.replies = 0
        self.errorfound = False
        self.cluesperreply = 0

        self.address = ''

    def update(self, remaining):
        """Updates certain statistics while the scan is happening.
        """
        self.round += 1

        ratio = self.ratio = len(self.clues) / float(self.replies)
        if self.replies > _THRESHOLD and ratio >= 0.7:
            # Start automagick clue inspector...
            import hlbd.inspectlib as inspectlib
            print '\r*** inspector started ***' + ' ' * 60

            # XXX Document and refactor heavily!
            ignore = inspectlib.get_diff_fields(self.clues, 80)
            print ignore
            assert len(ignore) > 0

            for field in ignore:
                method = '_get_' + cluelib.normalize(field)
                try:
                    getattr(cluelib.Clue, method)
                except AttributeError:
                    print '*** ignoring %s field ***' % field
                    setattr(cluelib.Clue, method, lambda s, f: None)
                    self.clues = []
                    self.replies = 0
            

        if self.verbose:
            self._show(remaining)

    def _show(self, remaining):
        """Displays progress information.
        """
        sys.stdout.write('\r%3d seconds left, %3d clue(s) so far, ' \
                '%3d valid replies and %3d missed) [%f]' \
                % (remaining, len(self.clues), self.replies, self.missed, self.ratio))
        sys.stdout.flush()


class Scanner:
    """Load-balancer scanner.
    """

    def __init__(self, scantime, verbose):
        """Initializes scanner object.

        @param scantime: Time (in seconds) to spend peforming the analysis.
        @type scantime: C{int}

        @param verbose: Specifies whether progress information should be printed or
        not.
        @type verbose: C{bool}
        """
        self.__scantime = scantime
        self.__state = State(verbose)

    def _makeClue(self, timestamp, headers):
        """Transforms timestamp-header pairs into clues.
        """
        self.__state.replies += 1

        clue = cluelib.Clue()
        clue.setTimestamp(timestamp)
        clue.processHdrs(headers)
#        print clue.info['server']

        try:
            i = self.__state.clues.index(clue)
            self.__state.clues[i].incCount()
        except ValueError:
            self.__state.clues.append(clue)

    def scan(self, address, url):
        """Scans for load balanced servers.

        @param address: Target IP address to scan.
        @type address: C{str}

        @param url: URL to scan.
        @type url: C{str}

        @return: list of clues found and number of replies received from the
        target.
        @rtype: C{tuple}
        """
        remaining = lambda end: int(end - time.time())
        hasexpired = lambda end: (remaining(end) <= 0)

        state = self.__state
        state.address = address

        # Start with the scanning loop
        stop = time.time() + self.__scantime		# Expiration time for the scan.
        while 1:
            client = clientlib.HTTPClient()

            try:
                reply = client.getHeaders(address, url)
            except clientlib.ConnectionRefused:
                sys.stderr.write('\r*** connection refused. aborting. ***\n')
                break

            if not reply:
                state.missed += 1
                continue

            timestamp, headers = reply
            self._makeClue(timestamp, headers) 

            # Check if the timer expired.
            if hasexpired(stop) or state.errorfound:
                break

            state.update(remaining(stop))

        if state.verbose:
            print


        return state.clues, state.replies


# vim: ts=4 sw=4 et
