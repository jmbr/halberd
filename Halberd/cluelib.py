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

@var delta: Allowed delta for L{cmp_delta_diff}
@type delta: C{int}
"""

__revision__ = '$Id: cluelib.py,v 1.7 2004/02/01 03:50:28 rwx Exp $'


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


delta = 2


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
            'server': None,
            'contloc': None,
            'cookie': None,
            'date': None,
            'digest': None
        }

        # Local time and remote time (in seconds since the Epoch)
        self._local, self._remote = 0, 0

        # Fingerprint for the reply.
        self.__fp = hashfn('')
        # We store the headers we're interested in digesting in a string and
        # calculate its hash _after_ the header processing takes place. This
        # way we incur in less computational overhead.
        self.__tmphdrs = ''

        # Original MIME headers. They're useful during analysis and reporting.
        self.headers = None

        self.__equalscmp = CmpOperator([cmp_diff, cmp_timeskew, cmp_server,
                                        cmp_contloc, cmp_digest])
        self.__containscmp = CmpOperator([cmp_delta_diff, cmp_timeskew,
                                          cmp_server, cmp_contloc, cmp_digest])


    def processHdrs(self, headers):
        """Extracts all relevant information from the MIME headers replied by
        the target.

        @param headers: MIME headers replied by the target.
        @type headers: str
        """

        hdrfp = StringIO(headers)
        hdrs = rfc822.Message(hdrfp)
        hdrfp.close()
        self.headers = hdrs.items()         # Save a copy of the headers.

        # We examine each MIME field and try to find an appropriate handler. If
        # there is none we simply digest the info it provides.
        for name, value in hdrs.items():
            try:
                handlerfn = getattr(self, '_get_' + self._normalize(name))
                handlerfn(value)
            except AttributeError:
                self.__tmphdrs += '%s: %s ' % (name, value)
        self._updateDigest()

    def _normalize(self, name):
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
        normal = filter(lambda c: c.isalnum(), list(name))
        while normal[0].isdigit():
            normal = normal[1:]
        return ''.join(normal)

    def _updateDigest(self):
        """Updates header fingerprint.
    
        Updates self._digest and derreferences the self.__fp object because SHA
        or MD5 objects are unpickable and this way we get rid of that problem.
        """
        self.__fp.update(self.__tmphdrs)
        self.__tmphdrs = ''
        self.info['digest'] = self.__fp.hexdigest()
        self.__fp = None


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

    def calcDiff(self):
        """Compute the time difference between the remote and local clocks.

        @return: Time difference.
        @rtype: C{int}
        """
        return (int(self._local) - int(self._remote))


    def __eq__(self, other):
        return (self.__equalscmp.compare(self, other) == 0)

    def __ne__(self, other):
        return not self == other

    def __contains__(self, other):
        return (self.__containscmp.compare(self, other) == 0)

    def __repr__(self):
        return "<Clue diff=%d found=%d digest='%s'>" \
                % (self.calcDiff(), self.__count, self.info['digest'])

    # ==================================================================
    # The following methods extract relevant data from the MIME headers.
    # ==================================================================

    def _get_server(self, field):
        """Server:"""
        self.info['server'] = field

    def _get_date(self, field):
        """Date:"""
        self.info['date'] = field
        self._remote = time.mktime(rfc822.parsedate(field))

    def _get_contentlocation(self, field):
        """Content-location:"""
        self.info['contloc'] = field
        self.__tmphdrs += field     # Make sure this gets hashed too.

    def _get_setcookie(self, field):
        """Set-cookie:"""
        self.info['cookie'] = field

    def _get_expires(self, field):
        """Expires:"""
        pass    # By passing we prevent this header from being hashed.

    def _get_age(self, field):
        """Age:"""
        pass


def analyze(clues):
    """Draw conclusions from the clues obtained during the scanning phase.
    """
    def makedict(clues):
        def append(cluedict, clue):
            digest = clue.info['digest']
            try:
                l = cluedict[digest]
            except KeyError:
                l = []
                cluedict[digest] = l
            l.append(clue)
            
        cluedict = {}
        # Put all the clues into the dictionary.
        map(append, [cluedict] * len(clues), clues)

        return cluedict

    def sort(clues):
        """Perform the schwartzian transform to sort clues by time diff.
        """
        # We proceed through the decorate-sort-undecorate steps.
        decorate = lambda c: (c.calcDiff(), c)
        decorated = map(decorate, clues)
        
        decorated.sort()

        return [diff_clue[1] for diff_clue in decorated]

    def groups(clues):
        # XXX refactor
        # maybe turning this into a generator could be nice.
        idx = 0

        cluesleft = lambda clues, idx: (len(clues) - idx)
        while cluesleft(clues, idx):
            step = 1
            if cluesleft(clues, idx) >= 3:
                avg = sum([clue.calcDiff() for clue in clues[idx:idx + 3]]) / 3
                if (avg == clues[idx + 1].calcDiff()):
                    yield (tuple(clues[idx:idx + 3]))
                    step = 3
            if cluesleft(clues, idx) == 2:
                if abs(clues[idx].calcDiff() - clues[idx + 1].calcDiff()) <= 1:
                    yield (clues[idx], clues[idx + 1])
                    step = 2
            if cluesleft(clues, idx) == 1:
                yield (clues[idx], )

            idx += step

    def merge(group):
        # XXX refactor
        assert len(group) <= 3

        if len(group) == 3:
            group[1].incCount(group[0].getCount())
            group[1].incCount(group[2].getCount())
            return group[1]
        elif len(group) == 2:
            group[0].incCount(group[1].getCount())
            return group[0]
        else:
            return group[0]

    results = []
    cluedict = makedict(clues)

    for key in cluedict.keys():
        cluedict[key] = sort(cluedict[key])

    for key in cluedict.keys():
        for group in groups(cluedict[key]):
            results.append(merge(group))

    return results


# =====================
# Comparison operators.
# =====================

def cmp_diff(one, other):
    """Compares time differences.

    @return: 0 if both clues have the time difference, -1 if L{one} less than
    L{other} and 1 if L{one} is greater than L{other}
    @rtype: C{int}
    """
    if one.calcDiff() < other.calcDiff():
        return -1
    elif one.calcDiff() > other.calcDiff():
        return 1
    return 0

def cmp_delta_diff(one, other):
    """Compares two clues with a delta.
    """
    onediff, otherdiff = one.calcDiff(), other.calcDiff()
    if abs(onediff - otherdiff) > delta:
        return -1
    return 0

def cmp_server(one, other):
    """Compares Server fields.

    @return: 0 if both clues have the same server, a non-zero value otherwise.
    @rtype: C{int}
    """
    if one.info['server'] != other.info['server']:
        return -1
    return 0

def cmp_digest(one, other):
    """Compares header digests.

    @return: 0 if both clues have the same digest, a non-zero value otherwise.
    @rtype: C{int}
    """
    if one.info['digest'] < other.info['digest']:
        return -1
    elif one.info['digest'] > other.info['digest']:
        return 1
    return 0

def cmp_timeskew(one, other):
    """Ensures there are no incoherent timestamps.
    """
    local = (one._local, other._local)
    remote = (one._remote, other._remote)
    if ((local[0] < local[1]) and (remote[0] > remote[1]) \
       or (local[0] > local[1]) and (remote[0] < remote[1])):
        return -1
    return 0

def cmp_contloc(one, other):
    """Compares Content-location fields.
    """
    if one.info['contloc'] != other.info['contloc']:
        return -1
    return 0

class CmpOperator:
    """Customizable comparison operator.
    """
    def __init__(self, operators):
        self.__operators = operators

    def compare(self, one, other):
        """Compares two clues
        """
        for comp in self.__operators:
            status = comp(one, other)
            if status != 0:
                break
        return status


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
