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

__revision__ = '$Id: scanlib.py,v 1.7 2004/02/07 13:33:30 rwx Exp $'


import sys
import time

import hlbd.cluelib as cluelib
import hlbd.clientlib as clientlib


__all__ = ["Scanner"]


#_THRESHOLD = 25


class State:
    """Holds the state of the scanner at the current point in time.
    """
    def __init__(self, verbose):
        self.clues = []
        self.verbose = verbose

        self.missed = 0
        self.replies = 0
        self.ratio = 0
        self.errorfound = False
        self.cluesperreply = 0

    def update(self, remaining):
        """Updates certain statistics while the scan is happening.
        """
        self._show(remaining)

#        if not self.clues or not self.replies:
#            return
#        
#        self.ratio = len(self.clues) / float(self.replies)
#        if self.replies > _THRESHOLD and self.ratio >= 0.5:
#            # Start automagick clue inspector...
#            import hlbd.inspectlib as inspectlib
#
#            # XXX Document and refactor heavily!
#            ignore = inspectlib.get_diff_fields(self.clues, 0)
#            assert len(ignore) > 0
#
#            for field in ignore:
#                method = '_get_' + cluelib.normalize(field)
#                if not hasattr(cluelib.Clue, method):
#                    print '\n*** inspector: ignoring "%s" field ***' % field
#                    setattr(cluelib.Clue, method, lambda s, f: None)
#                    self.clues = []
#                    self.replies = 0

    def _show(self, remaining):
        """Displays progress information.
        """
        if not self.verbose:
            return

        sys.stdout.write('\r%3d seconds left, %3d clue(s) so far, ' \
                '%3d valid replies and %3d missed) [%.02f]' \
                % (remaining, len(self.clues), self.replies, self.missed,
                   self.ratio))
        sys.stdout.flush()


def insert_clue(clues, timestamp, headers):
    """Transforms a timestamp-header pair into a clue and appends it to a list
    if it wasn't seen before.
    """
    clue = cluelib.Clue()
    clue.setTimestamp(timestamp)
    clue.parse(headers)

    try:
        i = clues.index(clue)
        clues[i].incCount()
    except ValueError:
        clues.append(clue)

def rpcscan(addr, url, scantime):
    pass

def scan(addr, url, scantime, verbose=False, parallelism=1):
    if parallelism <= 1:
        return _scan_thr(addr, url, scantime, verbose)

    import threading

    threads = []
    results = [[] for i in range(parallelism)]

    for i in range(parallelism):
        thread = threading.Thread(None, _scan_thr, None,
                                  (addr, url, scantime, verbose, results[i]))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    clues = []
    replies = 0

    for result in results:
        for partial_clues, partial_replies in result:
            replies += partial_replies
            for clue in partial_clues:
                if clue not in clues:
                    clues.append(clue)
                else:
                    i = clues.index(clue)
                    clues[i].incCount(clue.getCount())

    return clues, replies

def _scan_thr(addr, url, scantime, verbose=False, results=None):
    """Scans a given target looking for load balanced web servers.

    @param addr: Target IP address to scan.
    @type addr: C{str}

    @param url: URL to scan.
    @type url: C{str}

    @param scantime: Time (in seconds) to spend peforming the analysis.
    @type scantime: C{int}

    @return: list of clues found and number of replies received from the
    target.
    @rtype: C{tuple}
    """
    state = State(verbose)

    remaining = lambda end: int(end - time.time())
    hasexpired = lambda end: (remaining(end) <= 0)

    stop = time.time() + scantime		# Expiration time for the scan.
    while 1:
        if hasexpired(stop) or state.errorfound:
            break

        client = clientlib.HTTPClient()

        try:
            reply = client.getHeaders(addr, url)
        except clientlib.ConnectionRefused:
            sys.stderr.write('\r*** connection refused. aborting. ***\n')
            break

        if not reply:
            state.missed += 1
            state.update(remaining(stop))
            continue

        timestamp, headers = reply
        state.replies += 1
        insert_clue(state.clues, timestamp, headers)

        state.update(remaining(stop))

    if state.verbose:
        print

    if results is not None:
        results.append((state.clues, state.replies))
    return state.clues, state.replies


# vim: ts=4 sw=4 et
