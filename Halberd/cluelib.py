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

__revision__ = '$Id: cluelib.py,v 1.17 2004/02/11 11:17:02 rwx Exp $'


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
            """Create a list of name, value tuples from the server's response.

            We use a list instead of a dictionary because with the list we keep
            the header's order as sent by the target, which is a relevant piece
            of information we cannot afford to miss.
            """
            # We split by ':' instead of ': ' because it's more robust (some
            # webservers may send badly written headers).
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

        if self.info['digest'] != other.info['digest']:
            return False

# WARNING: Re-enabling this might break the analysis functions.
#        local = (self._local, other._local)
#        remote = (self._remote, other._remote)
#        if ((local[0] < local[1]) and (remote[0] > remote[1]) \
#           or (local[0] > local[1]) and (remote[0] < remote[1])):
#            return False

        return True

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        if not (self.diff or self.info['digest']):
            return "<Clue at %x>" % id(self)
        return "<Clue at %x diff=%d found=%d digest='%s'>" \
                % (id(self), self.diff, self.__count,
                   self.info['digest'][:4] + '...')

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

    def _get_lastmodified(self, field):
        """Last-modified:"""
        pass

    def _get_etag(self, field):
        """ETag:"""
        pass


# ========================
# Clue analysis functions.
# ========================


def diff_fields(clues):
    """Study differences between fields.

    @param clues: Clues to analyze.
    @type clues: C{list}

    @return: Fields which were found to be different among the analyzed clues.
    @rtype: C{list}
    """
    import difflib

    scores = {}

    for i in range(len(clues)):
        for j in range(len(clues)):
            if i == j:
                continue

            one, other = clues[i].headers, clues[j].headers
            matcher = difflib.SequenceMatcher(None, one, other)
    
            diffs = [opcode for opcode in matcher.get_opcodes() \
                            if opcode[0] != 'equal']

            for tag, alo, ahi, blo, bhi in diffs:
                for name, value in one[alo:ahi] + other[blo:bhi]:
                    scores.setdefault(name, 0)
                    scores[name] += 1

    # XXX total should be either: a) passed as a param or b) not computed at
    # all (the caller would be responsible of computing the percentage.
    total = sum(scores.values())
    result = [(count * 100 / total, field) for field, count in scores.items()]
    result.sort()
    result.reverse()

    return result


class groupby(dict):
    """Group-by recipe.
    """
    def __init__(self, seq, key=lambda x: x):
        for value in seq:
            k = key(value)
            self.setdefault(k, []).append(value)

    __iter__ = dict.iteritems

def unzip(seq):
    """Inverse of zip.
    """
    return tuple(zip(*seq))

def decor_and_sort(clues):
    """Decorates a list of clues and sorts it by their time diff.
    """
    decorated = [(clue.diff, clue) for clue in clues]
    decorated.sort()
    return decorated


def find_clusters(clues, step=3):
    """Finds clusters of clues.

    A cluster is a group of at most 3 clues which only differ in 1 seconds
    between each other.
    """
    def iscluster(clues, num):
        """Determines if a list of clues form a cluster of the specified size.
        """
        assert len(clues) == num

        if abs(clues[0].diff - clues[-1].diff) <= num:
            return True
        return False

    def find_cluster(clues, num):
        if len(clues) >= num:
            if iscluster(clues[:num], num):
                return tuple(clues[:num])
        return ()

    invrange = lambda num: [(num - x) for x in range(num)]

    start = 0
    while True:
        clues = clues[start:]
        if not clues:
            break

        for i in invrange(step):
            cluster = find_cluster(clues, i)
            if cluster:
                yield cluster
                start = i
                break

def merge_cluster(cluster):
    """Merges a given cluster into one clue.
    """
    for clue in cluster[1:]:
        cluster[0].incCount(clue.getCount())
    return cluster[0]


def classify(clues):
    """Classify clues by remote clock time and digest.
    """
    classified = {}

    decorated = [(clue._remote, clue.info['digest'], clue.diff, clue) \
           for clue in clues]
    decorated.sort()

    # We build a dictionary with two key levels and a list of clues at the
    # innermost level.
    for rtime, digest, diff, clue in decorated:
        items = classified.setdefault(rtime, {}).setdefault(digest, [])
        items.append(clue)

    return classified

def get_deltas(diffs):
    """Generator function which yields the differences between the eleements of
    a list of integers.
    """
    prev = None
    for diff in diffs:
        if prev is None:
            prev = diff
            yield 0
            continue

        delta = diff - prev
        yield delta

        prev = diff

def get_slices(clues, indexes):
    start, end = 0, len(clues)
    for idx in indexes:
        yield (start, idx)
        start = idx
    yield (start, end)

def filter_proxies(clues):
    """Detect and merge clues pointing to a proxy cache on the remote end.
    """
    if __debug__:
        getcount = lambda x: x.getCount()
        total = sum(map(getcount, clues))

    results = []

    # Classify clues by remote time and digest.
    classified = classify(clues)

    for rtime in classified.keys():
        for digest in classified[rtime].keys():

            # Sort clues by their time diff.
            diffs, cur_clues = unzip(decor_and_sort(classified[rtime][digest]))

            indexes = [idx for idx, delta in enumerate(get_deltas(diffs)) \
                           if delta > 3]

            for i, j in get_slices(cur_clues, indexes):
                for clue in cur_clues[i:j]:
                    clues.remove(clue)

                results.append(merge_cluster(cur_clues[i:j]))

    if __debug__:
        assert total == sum(map(getcount, results))

    return results

def analyze(clues):
    """Draw conclusions from the clues obtained during the scanning phase.

    First we group all the clues at hand by their digest, second we sort them
    by time difference and afterwards we try to find groups of at most 3 clues
    which actually belong to the same real server.

    @param clues: Unprocessed clues obtained during the scanning stage.
    @type clues: C{list}

    @return: Coherent list of clues identifying real web servers.
    @rtype: C{list}
    """
    clues = filter_proxies(clues)

    results = []
    getdigest = lambda c: c.info['digest']

    # We discriminate the clues by their digests.
    for key, clues_by_digest in groupby(clues, getdigest):
        # Sort by time difference.
        group = unzip(decor_and_sort(clues_by_digest))[1]

        for cluster in find_clusters(group):
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
