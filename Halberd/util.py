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


"""Miscellaneous functions.

@var table: Translation table for normalizing strings.
@type table: C{str}
"""

__revision__ = '$Id: util.py,v 1.2 2004/04/03 15:10:45 rwx Exp $'


import time
import socket
import urlparse


table = '________________________________________________0123456789_______ABCDEFGHIJKLMNOPQRSTUVWXYZ______abcdefghijklmnopqrstuvwxyz_____________________________________________________________________________________________________________________________________'


def _gen_table():
    """Generate translation table.
    """
    tab = ''
    for c in map(chr, xrange(256)):
        tab += (c.isalnum() and c) or '_'

    return tab


def utctime():
    return time.mktime(time.gmtime())


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


if __name__ == '__main__':
    print "table = '%s'" % _gen_table()


# vim: ts=4 sw=4 et
