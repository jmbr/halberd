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

__revision__ = '$Id: scanlib.py,v 1.2 2004/01/27 16:47:59 rwx Exp $'


import sys
import time
import asyncore

import hlbd.cluelib as cluelib
import hlbd.clientlib as clientlib


__all__ = ["Scanner"]


class State:
    """Holds the state of the scanner at the current point in time.
    """
    def __init__(self, sockets, verbose):
        self.clues = []
        self.sockets = sockets
        self.verbose = verbose

        self.replies = 0
        self.errorfound = False
        self.cluesperreply = 0

        self.address = ''

    def update(self, remaining):
        """Updates certain statistics while the scan is happening.
        """
        if len(self.clues) > 0:
            self.cluesperreply = len(self.clues) / float(self.replies)
            if self.cluesperreply >= 0.8:
                # 80% or more of the replies create new clues... This means
                # there's something wrong with the headers.
                pass
        
        if self.verbose:
            self._show(remaining)

    def _show(self, remaining):
        """Displays progress information.
        """
        sys.stdout.write('\r%3d seconds left, %3d clue(s) so far (out of ' \
                '%4d replies)' % (remaining, len(self.clues), self.replies))
        sys.stdout.flush()


# ===============================
# Callbacks passed to HTTPClient.
# ===============================

def _get_clues_cb(state, timestamp, headers):
    """Transforms timestamp-header pairs into clues.
    """
    state.replies += 1

    clue = cluelib.Clue()
    clue.setTimestamp(timestamp)
    clue.processHdrs(headers)

    try:
        i = state.clues.index(clue)
        state.clues[i].incCount()
    except ValueError:
        state.clues.append(clue)

def _error_cb(state):
    """Handles exceptions in a (somewhat) graceful way.
    """
    state.errorfound = True

    if sys.exc_type is KeyboardInterrupt:
        pass
    else:
        sys.stderr.write('Caught exception: ' + `sys.exc_type` + '\n')


class Scanner:
    """Load-balancer scanner.
    """

    def __init__(self, scantime, sockets, verbose):
        """Initializes scanner object.

        @param scantime: Time (in seconds) to spend peforming the analysis.
        @type scantime: C{int}

        @param sockets: Number of sockets to use in parallel to probe the target.
        @type sockets: C{int}

        @param verbose: Specifies whether progress information should be printed or
        not.
        @type verbose: C{bool}
        """
        self.__scantime = scantime
        self.__state = State(sockets, verbose)
        self.__clients = self._setupClientPool()

    def _setupClientPool(self):
        """Initializes the HTTP client pool before the scan starts.
        """
        clients = []

        if self.__state.verbose:
            sys.stdout.write('setting up client pool... ')
            sys.stdout.flush()

        for client in xrange(self.__state.sockets):
            client = clientlib.HTTPClient(_get_clues_cb, _error_cb,
                                          self.__state)
            clients.append(client)

        if self.__state.verbose:
            sys.stdout.write('done.')
            sys.stdout.flush()

        return clients

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
        state.round = 0
        stop = time.time() + self.__scantime		# Expiration time for the scan.
        while 1:
            for client in self.__clients:
                client.setURL(state.address, url).open()
                if state.errorfound:
                    break

            # Check if the timer expired.
            if hasexpired(stop) or state.errorfound:
                break

            asyncore.loop(remaining(stop))

            state.update(remaining(stop))

        if state.verbose:
            print

        return state.clues, state.replies


# vim: ts=4 sw=4 et
