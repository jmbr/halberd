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

__revision__ = '$Id: cluelib.py,v 1.11 2004/02/06 16:02:26 rwx Exp $'


import time
import rfc822

try:
    from sha import new as hashfn
except ImportError:
    from md5 import new as hashfn


def normalize(name):
    """Normalize string.

    This method takes a string coming out of mime-fields and transforms it
    into a valid Python identifier. That's done by removing invalid
    non-alphanumeric characters and also numeric ones placed at the
    beginning of the string.

    @param name: String to be normalized.
    @type name: C{str}

    @return: Normalized string.
    @rtype: C{str}
    """
    normal = [char for char in list(name.lower()) if char.isalnum()]
    while normal[0].isdigit():
        normal = normal[1:]
    return ''.join(normal)


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

        # Generic server info (sometimes useful for distinguising servers).
        self.info = {
            'server': '',
            'contloc': '',
            'cookie': '',
            'date': '',
            'digest': ''
        }

        # Local time and remote time (in seconds since the Epoch)
        self._local, self._remote = 0, 0

        self.diff = None

        # We store the headers we're interested in digesting in a string and
        # calculate its hash _after_ the header processing takes place. This
        # way we incur in less computational overhead.
        self.__tmphdrs = ''

        # Original MIME headers. They're useful during analysis and reporting.
        self.headers = None

    def parse(self, headers):
        """Extracts all relevant information from the MIME headers replied by
        the target.

        @param headers: MIME headers replied by the target.
        @type headers: str
        """
        def make_list(hdrs):
            return [tuple(line.split(':', 1)) for line in hdrs.splitlines() \
                                              if line != '']

        self.headers = make_list(headers)

        # We examine each MIME field and try to find an appropriate handler. If
        # there is none we simply digest the info it provides.
        for name, value in self.headers:
            try:
                handlerfn = getattr(self, '_get_' + normalize(name))
                handlerfn(value)
            except AttributeError:
                self.__tmphdrs += '%s: %s ' % (name, value)

        self._updateDigest()
        self._calcDiff()

    def _updateDigest(self):
        """Updates header fingerprint.
        """
        fingerprint = hashfn(self.__tmphdrs)
        self.__tmphdrs = ''
        self.info['digest'] = fingerprint.hexdigest()

    def _calcDiff(self):
        """Compute the time difference between the remote and local clocks.

        @return: Time difference.
        @rtype: C{int}
        """
        self.diff = int(self._local - self._remote)


    def incCount(self, num=1):
        """Increase the times this clue has been found.

        @param num: A positive non-zero number of hits to increase.
        @type num: C{int}

        @raise ValueError: in case L{num} is less than or equal to zero.
        """
        if num <= 0:
            raise ValueError
        self.__count += num

    def getCount(self):
        """Retrieve the number of times the clue has been found

        @return: Number of hits.
        @rtype: C{int}.
        """
        return self.__count


    def setTimestamp(self, timestamp):
        """Sets the local clock attribute.

        @param timestamp: The local time (expressed in seconds since the Epoch)
        when the connection to the target was successfully completed.
        @type timestamp: C{int}
        """
        self._local = timestamp


    def __eq__(self, other):
        if self.diff != other.diff:
            return False

#        local = (self._local, other._local)
#        remote = (self._remote, other._remote)
#        if ((local[0] < local[1]) and (remote[0] > remote[1]) \
#           or (local[0] > local[1]) and (remote[0] < remote[1])):
#            return False

        if self.info['digest'] != other.info['digest']:
            return False

        return True

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "<Clue diff=%d found=%d digest='%s'>" \
                % (self.diff, self.__count, self.info['digest'][:4] + '...')

    # ==================================================================
    # The following methods extract relevant data from the MIME headers.
    # ==================================================================

    def _get_server(self, field):
        """Server:"""
        self.info['server'] = field
        self.__tmphdrs += field     # Make sure this gets hashed too.

    def _get_date(self, field):
        """Date:"""
        self.info['date'] = field
        self._remote = time.mktime(rfc822.parsedate(field))

    def _get_contentlocation(self, field):
        """Content-location:"""
        self.info['contloc'] = field
        self.__tmphdrs += field

    def _get_setcookie(self, field):
        """Set-cookie:"""
        self.info['cookie'] = field

    def _get_expires(self, field):
        """Expires:"""
        pass    # By passing we prevent this header from being hashed.

    def _get_age(self, field):
        """Age:"""
        pass

    def _get_contentlength(self, field):
        """Content-length:"""
        pass


# ========================
# Clue analysis functions.
# ========================


class groupby(dict):
    """Group-by recipe.
    """
    def __init__(self, seq, key=lambda x: x):
        for value in seq:
            k = key(value)
            self.setdefault(k, []).append(value)

    __iter__ = dict.iteritems


def sort_by_diff(clues):
    """Perform the schwartzian transform to sort clues by time diff.

    @return: A sorted list by time difference.
    @rtype: C{list}
    """
    # We proceed through the decorate-sort-undecorate steps.
    decorated = [(clue.diff, clue) for clue in clues]
    decorated.sort()
    return [diff_clue[1] for diff_clue in decorated]


def find_clusters(clues):
    """Finds clusters of clues.

    A cluster is a group of at most 3 clues which only differ in 1 seconds
    between each other.
    """
    def isclusterof(clues, num):
        """Determines if a list of clues form a cluster of the specified size.
        """
        assert len(clues) == num, \
               'len(clues) == %d / num == %d' % (len(clues), num)

        if abs(clues[0].diff - clues[-1].diff) <= num:
            return True
        return False

    idx = 0

    cluesleft = lambda clues, idx: (len(clues) - idx)
    while cluesleft(clues, idx):
        step = 1
        if cluesleft(clues, idx) >= 3 \
            and isclusterof(clues[idx:idx+3], 3):
            step = 3
            yield tuple(clues[idx:idx+3])
        elif cluesleft(clues, idx) == 2 \
            and isclusterof(clues[idx:idx+2], 2):
            step = 2
            yield tuple(clues[idx:idx+2])
        elif cluesleft(clues, idx) == 1:
            yield (clues[idx], )

        idx += step

def merge_cluster(group):
    """Merges a given cluster into one clue.
    """
    assert len(group) <= 3

    aggregate = lambda src, dst: group[dst].incCount(group[src].getCount())

    if len(group) == 3:
        aggregate(0, 1)
        aggregate(2, 1)
        return group[1]
    elif len(group) == 2:
        aggregate(1, 0)
        return group[0]
    else:
        return group[0]


def analyze(clues):
    """Draw conclusions from the clues obtained during the scanning phase.

    @param clues: Unprocessed clues obtained during the scanning stage.
    @type clues: C{list}

    @return: Coherent list of clues identifying real web servers.
    @rtype: C{list}
    """
    results = []
    getdigest = lambda c: c.info['digest']

    for key, clues_by_digest in groupby(clues, getdigest):
        sorted = sort_by_diff(clues_by_digest)

        for cluster in find_clusters(sorted):
            results.append(merge_cluster(cluster))

    return results


# =============================
# Misc. clue-related utilities.
# =============================

def save_clues(filename, clues):
    """Save a clues to a file.

    @param filename: Name of the file where the clues will be written to.
    @type filename: C{str}

    @param clues: Clues to write.
    @type clues: C{list}
    """
    import pickle

    cluefp = open(filename, 'w')
    pickle.dump(clues, cluefp)
    cluefp.close()

def load_clues(filename):
    """Load clues from file.

    @param filename: Name of the files where the clues are stored.
    @type filename: C{str}

    @return: Clues extracted from the file.
    @rtype: C{list}
    """
    import pickle

    cluefp = open(filename, 'r')
    clues = pickle.load(cluefp)
    cluefp.close()

    return clues


# vim: ts=4 sw=4 et
