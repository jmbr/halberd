# -*- coding: iso-8859-1 -*-

"""Provides scanning patterns to be used as building blocks for more complex
scans.

Strategies are different ways in which target scans may be done. We provide
basic functionality so more complex stuff can be built upon this.
"""

__revision__ = '$Id: shell.py,v 1.7 2004/04/07 00:26:44 rwx Exp $'

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


import sys

import hlbd.crew
import hlbd.reportlib
import hlbd.clues.file
import hlbd.clues.analysis as analysis
from hlbd.RPCServer import RPCServer


class ScanError(Exception):
    """Generic error during scanning.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class BaseStrategy:
    """Defines the strategy used to scan.

    A strategy is a certain way to use the program. Theses can be layered to
    build a bigger strategy doing more complex things, etc.
    """
    def __init__(self, scantask):
        self.task = scantask

    def run(self):
        """Executes the strategy.
        """
        pass
        
    def info(self, msg):
        if self.task.verbose:
            sys.stdout.write(msg)
            sys.stdout.flush()

    def warn(self, msg):
        sys.stdout.write('warning: %s' % msg)
        sys.stdout.flush()

    # ---------------------------
    # Higher-level helper methods
    # ---------------------------

    def _scan(self):
        """Allocates a work crew of scanners and launches them on the target.
        """
        assert self.task.url and self.task.addr

        self.task.clues = []
        self.task.analyzed = []
        crew = hlbd.crew.WorkCrew(self.task)
        self.task.clues = crew.scan()

    def _analyze(self):
        """Performs clue analysis.
        """
        if len(self.task.clues) == 0:
            return

        self.task.analyzed = analysis.analyze(self.task.clues)
        self.task.analyzed = analysis.reanalyze(self.task.clues,
                                self.task.analyzed, self.task.ratio_threshold,
                                self.task.verbose)

class UniScanStrategy(BaseStrategy):
    """Scan a single URL.
    """
    def __init__(self, scantask):
        BaseStrategy.__init__(self, scantask)

        if not self.task.url:
            raise ScanError, 'Didn\'t provide an URL to scan'

        if self.task.addr:
            # The user passed a specific address as a parameter.
            self.addrs = [self.task.addr]
        else:
            host = hlbd.util.hostname(self.task.url)
            self.info('looking up host %s... ' % host)

            try:
                self.addrs = hlbd.util.addresses(host)
            except KeyboardInterrupt:
                raise ScanError, 'interrupted by the user'

            if not self.addrs:
                raise ScanError, 'unable to resolve %s' % host

            self.addrs.sort()
            self.info('done.\n\n')

    def run(self):
        """Scans, analyzes and presents results coming a single target.
        """
        if self.task.save:
            cluedir = hlbd.clues.file.ClueDir(self.task.save)

        for self.task.addr in self.addrs:
            self._scan()

            self._analyze()
            hlbd.reportlib.report(self.task)

            if self.task.save:
                cluedir.save(self.task.url,
                             self.task.addr,
                             self.task.clues)

class MultiScanStrategy(BaseStrategy):
    """Scan multiple URLs.
    """
    def __init__(self, scantask):
        BaseStrategy.__init__(self, scantask)

        if not self.task.urlfile:
            raise ScanError, 'An urlfile parameter must be provided'

        self.urlfp = open(self.task.urlfile, 'r')

    def _targets(self, urlfp):
        """Obtain target addresses from URLs.

        @param urlfp: File where the list of URLs is stored.
        @type urlfp: C{file}

        @return: Generator providing the desired addresses.
        """
        for url in urlfp:
            if url == '\n':
                continue

            # Strip end of line character and whitespaces.
            url = url[:-1].strip()

            host = hlbd.util.hostname(url)
            if not host:
                self.warn('unable to extract hostname from %s\n' % host)
                continue

            self.info('looking up host %s... ' % host)
            try:
                addrs = hlbd.util.addresses(host)
            except KeyboardInterrupt:
                raise ScanError, 'interrupted by the user'

            for addr in addrs:
                self.info('done.\n')
                yield (url, addr)

    def run(self):
        """Launch a multiple URL scan.
        """
        cluedir = hlbd.clues.file.ClueDir(self.task.save)

        for url, addr in self._targets(self.urlfp):
            self.task.url = url
            self.task.addr = addr
            self.info('scanning %s (%s)\n' % (url, addr))
            self._scan()

            cluedir.save(url, addr, self.task.clues)

            self._analyze()

            hlbd.reportlib.report(self.task)

class RPCServerStrategy(BaseStrategy):
    """Distributed scanner server strategy.

    Turns the program into an RPC server.
    """
    def __init__(self, scantask):
        BaseStrategy.__init__(self, scantask)

        self.rpcserver = RPCServer(scantask.rpc_serv_addr)
    
    def run(self):
        """Listen for scanning requests and serve them.
        """
        return self.rpcserver.serve_forever()

class ClueReaderStrategy(BaseStrategy):
    """Clue reader strategy.

    Works by reading and analyzing files of previously stored clues.
    """
    def __init__(self, scantask):
        BaseStrategy.__init__(self, scantask)

    def run(self):
        """Reads and interprets clues.
        """
        self.task.clues = hlbd.clues.file.load(self.task.cluefile)
        self._analyze()
        self.task.url = self.task.cluefile
        hlbd.reportlib.report(self.task)
    

# vim: ts=4 sw=4 et
