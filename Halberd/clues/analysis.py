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


"""Clue analysis and miscellaneous utilities.

XXX Write good documentation (with doctest)
"""

__revision__ = '$Id: analysis.py,v 1.2 2004/02/15 04:33:11 rwx Exp $'


def diff_fields(clues):
    """Study differences between fields.

    @param clues: Clues to analyze.
    @type clues: C{list}

    @return: Fields which were found to be different among the analyzed clues.
    @rtype: C{list}
    """
    def pairs(num):
        for i in xrange(num):
            for j in xrange(num):
                if i == j:
                    continue
                yield (i, j)

    import difflib

    scores = {}

    for i, j in pairs(len(clues)):
        one, other = clues[i].headers, clues[j].headers
        matcher = difflib.SequenceMatcher(None, one, other)

        for tag, alo, ahi, blo, bhi in matcher.get_opcodes():
            if tag == 'equal':
                continue
                
            for name, value in one[alo:ahi] + other[blo:bhi]:
                scores.setdefault(name, 0)
                scores[name] += 1

    total = sum(scores.values())
    result = [(count * 100 / total, field) for field, count in scores.items()]
    result.sort()
    result.reverse()

    return result


def unzip(seq):
    """Inverse of zip.

    >>> unzip([('a', 1), ('b', 2), ('c', 3)])
    (('a', 'b', 'c'), (1, 2, 3))
    """
    return tuple(zip(*seq))

def get_digest(clue):
    """Returns the specified clue's digest.
    """
    return clue.info['digest']

def decorate_and_sort(clues):
    """Decorates a list of clues and sorts it by their time diff.

    >>> import Clue
    >>> a, b, c = Clue.Clue(), Clue.Clue(), Clue.Clue()
    >>> a.diff, b.diff, c.diff = range(1, 4)
    >>> clues = undecorate(decorate_and_sort([c, b, a]))
    >>> (clues[0] == a, clues[1] == b, clues[2] == c)
    (True, True, True)
    """
    decorated = [(clue.diff, clue) for clue in clues]
    decorated.sort()
    return decorated

def undecorate(decorated):
    """Undecorate a list of decorated clues.
    """
    return unzip(decorated)[-1]

def clusters(clues, step=3):
    """Finds clusters of clues.

    A cluster is a group of at most C{step} clues which only differ in 1 seconds
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

    # Sort the clues by their time difference.
    clues = undecorate(decorate_and_sort(clues))

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

def merge(clues):
    """Merges a sequence of clues into one.

    The first clue from the sequence will be the one aggregating the count values
    from the rest.

    >>> from Clue import Clue
    >>> a, b, c = Clue(), Clue(), Clue()

    We are aware each Clue has a starting count of 1
    >>> sum([x.getCount() for x in [a, b, c]])
    3
    >>> a.incCount(5), b.incCount(11), c.incCount(23)
    (None, None, None)
    >>> merged = merge((a, b, c))
    >>> merged.getCount()
    42
    >>> merged == a
    True
    """
    for clue in clues[1:]:
        clues[0].incCount(clue.getCount())
    return clues[0]

def classify(seq, *classifiers):
    """Classify a sequence according to one or several criteria.

    We store each item into a nested dictionary using the classifiers as key
    generators.
    """
    classified = {}

    for item in seq:
        section = classified
        for classifier in classifiers[:-1]:
            assert callable(classifier)
            section = section.setdefault(classifier(item), {})

        # At the end no more dict nesting is needed. We simply store the items.
        last = classifiers[-1]
        section.setdefault(last(item), []).append(item)

    return classified

def sections(classified, sects=None):
    """Returns sections (and their items) from a nested dict.
    """
    if sects is None:
        sects = []

    if isinstance(classified, dict):
        for key in classified.keys():
            sections(classified[key], sects)
    elif isinstance(classified, list):
        sects.append(classified)

    return sects

def deltas(diffs):
    """Returns the differences between the elements of a sequence of integers.

    >>> list(deltas([-1, 0, 1]))
    [None, 1, 1]
    >>> list(deltas([1, 1, 3, 2, 3, 4, 6, 2]))
    [None, 0, 2, -1, 1, 1, 2, -4]
    >>> list(deltas(range(10)))
    [None, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    """
    prev = None
    for diff in diffs:
        if prev is None:
            prev = diff
            yield None
        else:
            delta = diff - prev
            prev = diff
            yield delta

def slices(seq, indexes):
    """Returns slices of a given sequence separated by the specified indexes.

    @param seq: Sequence to split in slices.
    @type seq: Any (mutable) sequence which provides de __len__ method.

    @return: A sequence of C{slice} objects suitable for splitting the given
    sequence.
    @rtype: C{tuple}

    For example. We want to get the slices necessary to split range(20) in
    sub-sequences of 5 items each:
    >>> seq, points = range(20), range(5, 20, 5)
    >>> for sl in slices(seq, points):
    ...     print seq[sl]
    [0, 1, 2, 3, 4]
    [5, 6, 7, 8, 9]
    [10, 11, 12, 13, 14]
    [15, 16, 17, 18, 19]
    """
    start, end = 0, len(seq)
    for idx in indexes:
        yield slice(start, idx)
        start = idx
    yield slice(start, end)

def filter_proxies(clues, maxdelta=3):
    """Detect and merge clues pointing to a proxy cache on the remote end.
    """
    results = []

    # Classify clues by remote time and digest.
    get_rtime = lambda c: c._remote
    classified = classify(clues, get_rtime, get_digest)

    subsections = sections(classified)
    for section in subsections:
        # Sort clues by their time diff.
        diffs, cur_clues = unzip(decorate_and_sort(section))

        # We find the indexes of those clues which differ from the rest in
        # more than maxdelta seconds.
        indexes = [idx for idx, delta in enumerate(deltas(diffs)) \
                       if delta is not None and abs(delta) > maxdelta]

        for sl in slices(cur_clues, indexes):
            for clue in cur_clues[sl]:
                clues.remove(clue)

            results.append(merge(cur_clues[sl]))

    return results

def uniq(clues):
    """Return a list of unique clues.

    This is needed when merging clues coming from different sources. Clues with
    the same time diff and digest are not discarded, they are merged into one
    clue with the aggregated number of hits.
    """
    results = []

    get_diff = lambda c: c.diff
    classified = classify(clues, get_digest, get_diff)

    for section in sections(classified):
        results.append(merge(section))

    return results

def analyze(clues):
    """Draw conclusions from the clues obtained during the scanning phase.

    @param clues: Unprocessed clues obtained during the scanning stage.
    @type clues: C{list}

    @return: Coherent list of clues identifying real web servers.
    @rtype: C{list}
    """
    results = []

    clues = uniq(clues)

    clues = filter_proxies(clues)

    cluesbydigest = classify(clues, get_digest)

    for key in cluesbydigest.keys():
        for cluster in clusters(cluesbydigest[key]):
            results.append(merge(cluster))

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


def _test():
    import doctest, analysis
    return doctest.testmod(analysis)

if __name__ == '__main__':
    _test()


# vim: ts=4 sw=4 et
