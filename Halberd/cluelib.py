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

"""Clue management module.

This module implements a few classes related to creation and and analysis of
pieces of information returned by a webserver which may help in locating load
balanced devices.
"""

__revision__ = '$Id: cluelib.py,v 1.1 2004/01/26 23:07:31 rwx Exp $'


import time
import rfc822

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from sha import new as hashfn
except ImportError:
    from md5 import new as hashfn


DELTA = 1


class Clue:
    """A clue is what we use to tell real servers from virtual ones.

    Clues are gathered during several connections to the target and they try to
    identify clearly potential patterns in the HTTP responses.
    """

    def __init__(self):
        """Initializes the clue object.
        """

        # Number of times this clue has been found.
        self.__count = 1

        # Server information.
        self._server = ''

        # Local and remote time in seconds since the Epoch.
        self._local, self._remote = 0, 0

        # Content-Location field. In case the server is misconfigured and
        # advertises IP addresses those will be shown here.
        self._contloc = ''

        # Fingerprint for the reply.
        self._fp = hashfn('')
        # We store the headers we're interested in digesting in a string and
        # calculate its hash _after_ the header processing takes place. This
        # way we incur in less computational overhead.
        self.__tmphdrs = ''

        # Cookie. Sometimes it helps pointing out real servers.
        self._cookie = ''

        # Original MIME headers. They're useful during analysis and reporting.
        self.headers = None


    def processHdrs(self, headers):
        """Extracts all relevant information from the MIME headers replied by
        the target.

        @param headers: MIME headers replied by the target.
        @type headers: str
        """

        hdrfp = StringIO(headers)
        hdrs = rfc822.Message(hdrfp)
        hdrs.readheaders()
        hdrfp.close()

        self.headers = hdrs         # Save a copy of the headers.

        normalize = lambda s: s.replace('-', '_')

        # We examine each MIME field and try to find an appropriate handler. If
        # there is none we simply digest the info it provides.
        for name, value in hdrs.items():
            try:
                handlerfn = getattr(self, '_get_' + normalize(name))
                handlerfn(value)
            except AttributeError:
                self.__tmphdrs += '%s: %s ' % (name, value)

        self._fp.update(self.__tmphdrs)


    def incCount(self, num=1):
        """Increase the times this clue has been found.

        param num: Number of hits to add.
        type num: int
        """
        self.__count += num

    def getCount(self):
        """Retrieve the number of times the clue has been found

        @return: Number of hits.
        @rtype: integer.
        """
        return self.__count


    def setTimestamp(self, timestamp):
        """Sets the local clock attribute.

        @param timestamp: The local time (expressed in seconds since the Epoch)
        when the connection to the target was successfully completed.
        @type timestamp: numeric.
        """
        self._local = timestamp

    def calcDiff(self):
        """Compute the time difference between the remote and local clocks.
        """
        return (int(self._local) - int(self._remote))


    # ===================
    # Comparison methods.
    # ===================

    def __eq__(self, other):
        """Rich comparison method implementing ==
        """
        if self._server != other._server:
            return False

        # Important sanity check for the timestamps:
        #   Time can't (usually) go backwards.
        local = (self._local, other._local)
        remote = (self._remote, other._remote)
        if ((local[0] < local[1]) and (remote[0] > remote[1]) \
           or (local[0] > local[1]) and (remote[0] < remote[1])):
            return False

        if self.calcDiff() != other.calcDiff():
            return False

        if self._contloc != other._contloc:
            return False

        if self._fp.digest() != other._fp.digest():
            return False

        return True

    def __ne__(self, other):
        """Rich comparison method implementing !=
        """
        return not self == other

    # =========
    # Contains.
    # =========

    def __contains__(self, other):
        onediff, otherdiff = self.calcDiff(), other.calcDiff()

        if abs(onediff - otherdiff) > DELTA:
            return False

        # Important sanity check for the timestamps:
        #   Time can't (usually) go backwards.
        local = (self._local, other._local)
        remote = (self._remote, other._remote)
        if ((local[0] < local[1]) and (remote[0] > remote[1]) \
           or (local[0] > local[1]) and (remote[0] < remote[1])):
            return False

        if self._contloc != other._contloc:
            return False

        if self._fp.digest() != other._fp.digest():
            return False

        return True


    def __repr__(self):
        return "<Clue diff=%d found=%d digest='%s'>" \
                % (self.calcDiff(), self.__count, self._fp.hexdigest())

    # ==================================================================
    # The following methods extract relevant data from the MIME headers.
    # ==================================================================

    def _get_server(self, field):
        """Server:"""
        self._server = field

    def _get_date(self, field):
        """Date:"""
        self._remote = time.mktime(rfc822.parsedate(field))

    def _get_content_location(self, field):
        """Content-location."""
        self._contloc = field
        self.__tmphdrs += field     # Make sure this gets hashed too.

    def _get_set_cookie(self, field):
        """Set-cookie:"""
        self._cookie = field

    def _get_expires(self, field):
        """Expires:"""
        pass    # By passing we prevent this header from being hashed.

    def _get_age(self, field):
        """Age:"""
        pass


def _comp_clues(one, other):
    """Clue comparison for list sorting purposes.

    We take into account fingerprint and time differences.
    """
    if one._fp.digest() < other._fp.digest():
        return -1
    elif one._fp.digest() > other._fp.digest():
        return 1

    if one.calcDiff() < other.calcDiff():
        return -1
    elif one.calcDiff() > other.calcDiff():
        return 1

    return 0

class Analyzer:
    """Makes sens of the data gathered during the scanning stage.
    """

    def __init__(self, pending):
        """Initializes the analyzer object
        """
        assert pending is not None
        self.__pending = pending
        self.__analyzed = []

    def analyze(self):
        """Processes the list of pending clues checking for duplicated entries.

        Duplicated entries (differing in one second and equal in everything
        else) are moved from the list of pending clues to the list of analyzed
        ones.
        """
        self.__pending.sort(_comp_clues)

        while self.__pending:
            cur = self.__pending[0]
            if len(self.__pending) >= 2:
                next = self.__pending[1]
                if cur in next:
                    self._consolidateClues(cur, next)
                    continue

            self._moveClue(cur)

        return self.__analyzed

    def _consolidateClues(self, one, two):
        """Converts two or three clues into one.

        Note that the first one is the one which survives.
        """
        one.incCount(two.getCount())
        self._moveClue(one)
        self.__pending.remove(two)

    def _moveClue(self, clue):
        """Moves a clue from pending to analyzed.
        """
        self.__analyzed.append(clue)
        self.__pending.remove(clue)


# vim: ts=4 sw=4 et
