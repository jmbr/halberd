# -*- coding: iso-8859-1 -*-

"""Strategy module.

Provides the halberd shell with several scanning strategies to perform its
task.
"""
__revision__ = '$Id: strategy.py,v 1.2 2004/03/29 10:36:22 rwx Exp $'

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

import hlbd.shell
import hlbd.clues.file
from hlbd.shell.factory import halberdFactory, DIRECT_SCAN, DIST_SCAN


class BaseScan:
    """Defines the strategy used to scan.
    """
    scan_type = DIRECT_SCAN

    def __init__(self, **kw):
        self.verbose = kw.get('verbose', False)

    def run(self, output):
        pass

    def info(self, msg):
        if self.verbose:
            sys.stdout.write(msg)
            sys.stdout.flush()

    def warn(self, msg):
        sys.stdout.write('warning: %s' % msg)
        sys.stdout.flush()
        

class DistScanMixIn:
    """Performs scans through several halberd scanning agents.
    """
    scan_type = DIST_SCAN


class UniScan(BaseScan):
    """Scan a single URL.
    """
    def __init__(self, **kw):
        BaseScan.__init__(self, **kw)

        try:
            self.url = kw['url']
        except KeyError:
            raise TypeError, 'Didn\'t provide an URL to scan'
        addr = kw.get('addr', None)

        self.halberd = halberdFactory(self.scan_type, **kw)

        if addr:
            # The user passed a specific address as a parameter.
            self.addrs = [addr]
        else:
            host = hlbd.shell.hostname(self.url)
            self.info('looking up host %s... ' % host)

            self.addrs = hlbd.shell.core.addresses(host)
            if not self.addrs:
                # XXX - Turn this into an exception
                self.Halberd.fatal('unable to resolve %s\n' % host)

            self.addrs.sort()
            self.info('done.\n\n')

    def run(self, savefile=None, output=None):
        self.halberd.setURL(self.url)
        for addr in self.addrs:
            self.halberd.setAddr(addr)
            self.halberd.run()

            self.halberd.analyze()

            self.halberd.report(output)

        if savefile:
            import hlbd.clues.file

            if len(self.addrs) > 1:
                self.warn('only the last clues will be stored\n')
            hlbd.clues.file.save(savefile, self.halberd.clues)


class MultiScan(BaseScan):
    """Scan multiple URLs.
    """
    def __init__(self, **kw):
        BaseScan.__init__(self, **kw)

        self.opts = {}
        self.opts.update(kw)

        urlfile = kw.get('urlfile', None)
        if not urlfile:
            raise TypeError, 'An urlfile parameter must be provided'
        self.urlfp = open(urlfile, 'r')

    def _targets(self):
        for url in self.urlfp:
            if url == '\n':
                continue

            # Strip end of line character.
            url = url[:-1]

            host = hlbd.shell.hostname(url)
            if not host:
                self.warn('unable to extract hostname from %s\n' % host)
                continue

            self.info('looking up host %s... ' % host)
            for addr in hlbd.shell.addresses(host):
                self.info('done.\n')
                yield (url, addr)

    def run(self, savefile, output=None):
        cluedir = hlbd.clues.file.ClueDir(savefile)
        for url, addr in self._targets():
            halberd = halberdFactory(self.scan_type, **self.opts)
            halberd.setURL(url)
            halberd.setAddr(addr)
            self.info('scanning %s (%s)\n' % (url, addr))
            halberd.run()

            cluedir.save(url, addr, halberd.clues)

            halberd.analyze()
            halberd.report(output)

class DistUniScan(DistScanMixIn, UniScan):
    pass

class DistMultiScan(DistScanMixIn, MultiScan):
    pass
    

# vim: ts=4 sw=4 et
