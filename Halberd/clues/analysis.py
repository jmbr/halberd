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


__revision__ = '$Id: analysis.py,v 1.1 2004/02/13 01:17:43 rwx Exp $'


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

    total = sum(scores.values())
    result = [(count * 100 / total, field) for field, count in scores.items()]
    result.sort()
    result.reverse()

    return result


def unzip(seq):
    """Inverse of zip.
    """
    return tuple(zip(*seq))

def decorate_and_sort(clues):
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

def sections(classified, sets=None):
    """Returns sections (and their items) from a nested dict.
    """
    if sets is None:
        sets = []

    # XXX turn this into a generator.
    if isinstance(classified, dict):
        for key in classified.keys():
            sections(classified[key], sets)
    elif isinstance(classified, list):
        sets.append(classified)

    return sets

def get_deltas(diffs):
    """Generator function which yields the differences between the elements of
    a list of integers.
    """
    prev = None
    for diff in diffs:
        if prev is None:
            prev = diff
            yield 0     # Maybe it should return None instead.
        else:
            delta = diff - prev
            prev = diff
            yield delta

def get_slices(clues, indexes):
    start, end = 0, len(clues)
    for idx in indexes:
        yield (start, idx)
        start = idx
    yield (start, end)

def filter_proxies(clues, maxdelta=3):
    """Detect and merge clues pointing to a proxy cache on the remote end.
    """
    results = []

    # Classify clues by remote time and digest.
    getrtime = lambda c: c._remote
    getdigest = lambda c: c.info['digest']
    classified = classify(clues, getrtime, getdigest)

    subsections = sections(classified)
    for section in subsections:
        # Sort clues by their time diff.
        diffs, cur_clues = unzip(decorate_and_sort(section))

        # We find the indexes of those clues which differ from the rest in
        # more than maxdelta seconds.
        indexes = [idx for idx, delta in enumerate(get_deltas(diffs)) \
                       if delta > maxdelta]

        for i, j in get_slices(cur_clues, indexes):
            for clue in cur_clues[i:j]:
                clues.remove(clue)

            results.append(merge_cluster(cur_clues[i:j]))

    return results

def uniq(clues):
    """Return a list of unique clues.

    This is needed when merging clues coming from different sources.
    """
    results = []

    getdiff = lambda c: c.diff
    getdigest = lambda c: c.info['digest']
    classified = classify(clues, getdigest, getdiff)

    for section in sections(classified):
        results.append(merge_cluster(section))

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
    results = []

    # XXX maybe the following two functions should be written as generators.
    clues = filter_proxies(uniq(clues))

    # We discriminate the clues by their digests.
    getdigest = lambda c: c.info['digest']
    cluesby = classify(clues, getdigest)
    for digest in cluesby.keys():
        # Sort by time difference.
        group = unzip(decorate_and_sort(cluesby[digest]))[1]

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
