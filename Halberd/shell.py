# -*- coding: iso-8859-1 -*-

"""Provides scanning patterns to be used as building blocks for more complex
scans.

Strategies are different ways in which target scans may be done. We provide
basic functionality so more complex stuff can be built upon this.
"""

__revision__ = '$Id: shell.py,v 1.4 2004/04/04 01:16:40 rwx Exp $'

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
import hlbd.shell
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
    """
    def __init__(self, scanopts):
        self.task = scanopts

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

    def scan(self):
        """Higher level target scan.
        """
        crew = hlbd.crew.WorkCrew(self.task)
        self.task.clues = crew.scan()

    def analyze(self):
        """Higher level clue analysis.
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
    def __init__(self, scanopts):
        BaseStrategy.__init__(self, scanopts)

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

        for addr in self.addrs:
            self.task.setAddr(addr)
            self.scan()

            self.analyze()
            hlbd.reportlib.report(self.task)

            if self.task.save:
                cluedir.save(self.task.url,
                             self.task.addr,
                             self.task.clues)

class MultiScanStrategy(BaseStrategy):
    """Scan multiple URLs.
    """
    def __init__(self, scanopts):
        BaseStrategy.__init__(self, scanopts)

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

            # Strip end of line character.
            url = url[:-1]

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
            self.task.setURL(url)
            self.task.setAddr(addr)
            self.info('scanning %s (%s)\n' % (url, addr))
            self.scan()

            cluedir.save(url, addr, self.task.clues)

            self.analyze()

            hlbd.reportlib.report(self.task)

class RPCServerStrategy(BaseStrategy):
    """Distributed scanner server strategy.
    """
    def __init__(self, scanopts):
        BaseStrategy.__init__(self, scanopts)

        self.rpcserver = RPCServer(scanopts.rpc_serv_addr)
    
    def run(self):
        """Turn the program into a provider of scan results.
        """
        return self.rpcserver.serve_forever()

class ClueReadStrategy(BaseStrategy):
    """Clue reader strategy.
    """
    def __init__(self, scanopts):
        BaseStrategy.__init__(self, scanopts)

    def run(self):
        """Reads and interprets previously stored clues.
        """
        self.task.clues = hlbd.clues.file.load(self.task.cluefile)
        self.analyze()
        self.task.url = self.task.cluefile
        hlbd.reportlib.report(self.task)
    

# vim: ts=4 sw=4 et
