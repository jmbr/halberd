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

"""Scanning engine.
"""

__revision__ = '$Id: scanlib.py,v 1.15 2004/03/02 02:10:30 rwx Exp $'


import sys
import time
import signal

# XXX For using dummy_threading the timeout must be checked in scan_thr
import threading
#try:
#    import threading
#except ImportError:
#    import dummy_threading as threading

import hlbd.clues.Clue as Clue
import hlbd.clientlib as clientlib


__all__ = ['scan']


class State:
    """Holds the state of the scanner at the current point in time.
    """
    def __init__(self, addr, url, scantime, verbose):
        """Initalizes the state object.
        """
        self.addr = addr
        self.url = url
        self.scantime = scantime
        self.verbose = verbose

        self.clues = []

        self.missed = 0
        self.replies = 0
        self.shouldstop = False

        self.lock = threading.Lock()

    def show(self, remaining):
        """Displays certain statistics while the scan is happening.
        """
        if not self.verbose:
            return

        statusline = """\
\r%15s | remaining: %3d | clues: %3d | replies: %3d | missed: %3d\
""" % (self.addr, remaining, len(self.clues), self.replies, self.missed)

        sys.stdout.write(statusline)
        sys.stdout.flush()


def scan(addr, url, scantime, parallelism=1, verbose=False):
    """Performs a parallel load balancer scanning.

    @param addr: Target IP address to scan.
    @type addr: C{str}

    @param url: URL to scan.
    @type url: C{str}

    @param scantime: Time (in seconds) to spend peforming the analysis.
    @type scantime: C{int}

    @param parallelism: Number of threads to spawn.
    @type parallelism: C{int}

    @param verbose: Specifies whether status info should be displayed or not.
    @type verbose: C{bool}

    @return: Clues found.
    @rtype: C{list}
    """
    assert parallelism > 0
    assert scantime > 0

    state = State(addr, url, scantime, verbose)

    # Set up interrupt handler to let the user stop the scan when he wishes.
    def interrupt(signum, frame):
        """SIGINT handler
        """
        state.shouldstop = True

    try:
        prev = signal.signal(signal.SIGINT, interrupt) 
    except ValueError:      # XXX this is temporary
        prev = None

    # This is a very POSIXish idiom but I don't think there's a need for
    # anything fancier.
    threads = []
    for i in xrange(parallelism):
        thread = threading.Thread(None, scan_thr, None, (state,))
        thread.start()

    remaining = lambda end: int(end - time.time())
    hasexpired = lambda end: (remaining(end) <= 0)

    # Expiration time for the scan.
    stop = time.time() + state.scantime
    while True:
        state.lock.acquire()
        state.show(remaining(stop))

        if state.shouldstop or hasexpired(stop):
            state.lock.release()
            break
        state.lock.release()

        try:
            time.sleep(0.5)
        except IOError:
            # Catch interrupted system call exception.
            break

    # Tell the threads to stop.
    state.lock.acquire()
    state.shouldstop = True
    state.lock.release()

    for thread in threads:
        thread.join()

    # Show the last update.
    state.show(remaining(stop))
    if verbose:
        sys.stdout.write('\n\n')

    try:
        signal.signal(signal.SIGINT, prev)  # Restore SIGINT handler.
    except ValueError:
        # XXX temp
        pass

    return state.clues


def insert_clue(clues, reply):
    """Transforms a timestamp-header pair into a clue and appends it to a list
    if it wasn't seen before.
    """
    timestamp, headers = reply

    clue = Clue.Clue()
    clue.setTimestamp(timestamp)
    clue.parse(headers)

    try:
        i = clues.index(clue)
        clues[i].incCount()
    except ValueError:
        clues.append(clue)

def scan_thr(state):
    """Scans a given target looking for load balanced web servers.
    """
    while True:
        state.lock.acquire()
        if state.shouldstop:
            state.lock.release()
            break
        state.lock.release()

        # XXX - Devise a way to pass keyfile and certfile from halberd.cfg to
        # the client factory.
        client = clientlib.client(state.url)

        try:
            reply = client.getHeaders(state.addr, state.url)
        except (clientlib.ConnectionRefused, clientlib.UnknownReply), msg:
            sys.stderr.write('\n*** %s. aborting. ***\n' % msg)
            state.lock.acquire()
            state.shouldstop = True
            state.lock.release()
            break

        state.lock.acquire()
        if not reply:
            state.missed += 1
            state.lock.release()
            continue

        state.replies += 1
        insert_clue(state.clues, reply)
        state.lock.release()


# vim: ts=4 sw=4 et
