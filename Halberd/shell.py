#!/usr/bin/env python
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


"""Shell for common usage patterns.

@var default_scantime: Time to spend probing the target expressed in seconds.
@type default_scantime: C{int}

@var default_parallelism: Number of parallel threads to launch for the scan.
@type default_parallelism: C{int}

@var default_conf_dir: Path to the directory where the configuration file is
located.
@type default_conf_dir: C{str}

@var default_conf_file: Name of the default configuration file for halberd.
@type default_conf_file: C{str}

@var default_ratio_threshold: Minimum clues-to-realservers ratio to trigger a
clue reanalysis.
@type default_ratio_threshold: C{float}
"""

__revision__ = '$Id: shell.py,v 1.1 2004/03/26 00:48:25 rwx Exp $'


import os
import sys
import socket
import urlparse


default_scantime = 30

default_parallelism = 4

default_conf_dir = os.path.join(os.path.expanduser('~'), '.halberd')
default_conf_file = os.path.join(default_conf_dir, 'halberd.cfg')

default_ratio_threshold = 0.6


class Halberd:
    """HTTP load balancer detector.

    @ivar verbose: Display status information during the scan.
    @type verbose: C{bool}

    @ivar url: URL to scan.
    @type url: C{str}

    @ivar addr: Address of the target web server.
    @type addr: C{str}

    @ivar clues: Sequence of clues obtained from the target.
    @type clues: C{list}

    @ivar analyzed: Sequence of clues after the analysis phase.
    @type analyzed: C{list}

    @ivar rpc_servers: List of addresses were scanning agents are listening.
    @type rpc_servers: C{list}

    @ivar rpc_serv_addr: Address + port where to listen when launching halberd
    as an agent scanner.
    @type rpc_serv_addr: C{tuple}

    @ivar proxy_serv_addr: Address + port where to listen when operating as a
    proxy.
    @type proxy_serv_addr: C{tuple}
    """

    def __init__(self, verbose=False):
        self.verbose = verbose

        self.url = None
        self.addr = None

        self.clues = []
        self.analyzed = []

        self.parallelism = default_parallelism
        self.scantime = default_scantime

        self.rpc_servers = None
        self.rpc_serv_addr = None

        self.proxy_serv_addr = None


    def setURL(self, url):
        """Ensures the URL is a valid one.
        
        Characters aren't escaped, so strings like 'htt%xx://' won't be parsed.

        @param url: An incomplete (or not) URL.
        @type url: C{str}
        """
        if url.startswith('http://') or url.startswith('https://'):
            self.url = url
        else:
            self.url = 'http://' + url

        return self

    def setAddr(self, addr):
        """Sets the target address.
        """
        self.clues = self.analyzed = []
        self.addr = addr

        return self


    def info(self, msg):
        """Display information to the user.
        """
        if self.verbose:
            sys.stdout.write(str(msg))
            sys.stdout.flush()

    # XXX - Replace calls to fatal with calls to raise.
    def fatal(msg):
        """Fatal error notification.
        """
        sys.stderr.write(str(msg))
        sys.stderr.flush()
        sys.exit(-1)

    fatal = staticmethod(fatal)


    def scan(self):
        import hlbd.scanlib as scanlib

        self.clues += scanlib.scan(self.addr, self.url, self.scantime,
                                  self.parallelism, self.verbose)
    def analyze(self):
        """Analyze clues.
        """
        if len(self.clues) == 0:
            return

        import hlbd.clues.analysis as analysis

        self.analyzed = analysis.analyze(self.clues)

        self.analyzed = analysis.reanalyze(self.clues,
                                           self.analyzed,
                                           default_ratio_threshold,
                                           self.verbose)

    def report(self, outfile):
        """Write a report.
        """
        import hlbd.reportlib

        hlbd.reportlib.report(self.addr, self.analyzed, outfile)


    def server(self):
        """Launch the program as a server.
        """
        import hlbd.rpclib

        hlbd.rpclib.server(self.rpc_serv_addr, self.verbose)

    def client(self):
        """Launch the program as a client.
        """
        def run_thr(addr, port, clues, lock):
            rpclib.client((addr, port), self.addr, self.url, self.scantime,
                          self.parallelism, self.verbose, (clues, lock))

        def normalize_clues(clues, delta):
            for clue in clues:
                clue._local -= delta
                clue._calcDiff()
            return clues

        import threading
        import hlbd.rpclib as rpclib

        assert self.rpc_servers is not None

        threads = []
        results = []
        lock = threading.Lock()

        thread = (threading.Thread(None, self.scan, None, ()))
        thread.start()
        threads.append(thread)

        for rpc_server in self.rpc_servers:
            addr, port = rpc_server.split(':')
            port = int(port)

            self.info('scanning through %s:%d\n' % (addr, port))

            thread = threading.Thread(None, run_thr, None, \
                                            (addr, port, results, lock))
            thread.start()
            threads.append(thread)

        self.info('\n')

        for thread in threads:
            thread.join()

#        for local, remote, clues in results:
        for result in results:
            if len(result) == 3:
                # Clues coming from a distributed scan.
                local, remote, clues = result
                self.clues.extend(normalize_clues(clues, remote - local))
            else:
                # Clues acquired locally.
                self.clues.extend(result)


    def readConf(self, conf_file):
        """Read configuration file.

        This method tries to read the specified configuration file. If we try
        to read it at the default path and it's not there we create a
        bare-bones file and use that one.

        @param conf_file: Path to the configuration file.
        @type conf_file: C{str}
        """
        import hlbd.conflib as conflib

        reader = conflib.ConfReader()

        try:
            reader.open(conf_file)
        except IOError:
            if conf_file == default_conf_file:
                try:
                    os.mkdir(default_conf_dir)
                    reader.writeDefault(default_conf_file)
                    self.info('created default configuration at %s\n' \
                              % conf_file)
                    reader.open(default_conf_file)
                except (OSError, IOError), msg:
                    self.fatal('unable to create a default conf. file.\n')
            else:
                self.fatal('unable to open configuration file %s\n')
        except conflib.InvalidConfFile:
            self.fatal('invalid configuration file %s\n' % conf_file)

        options = reader.parse()
        self.proxy_serv_addr = options.proxy_serv_addr

        self.rpc_serv_addr = options.rpc_serv_addr
        self.rpc_servers = options.rpc_servers

        reader.close()


def hostname(url):
    """Get the hostname part of an URL.

    @param url: A valid URL (must be preceded by scheme://).
    @type url: C{str}

    @return: Hostname corresponding to the URL or the empty string in case of
    failure.
    @rtype: C{str}
    """
    netloc = urlparse.urlparse(url)[1]
    if netloc == '':
        return ''

    return netloc.split(':', 1)[0]

def addresses(host):
    """Get the network addresses to which a given host resolves to.

    @param host: Hostname we want to resolve.
    @type host: C{str}

    @return: Network addresses.
    @rtype: C{tuple}
    """
    assert host != ''

    try:
        name, aliases, addrs = socket.gethostbyname_ex(host)
    except socket.error:
        return ()

    return addrs


# vim: ts=4 sw=4 et
