# -*- coding: iso-8859-1 -*-

"""Halberd factory.

Abstracts the work needed to instatiate Halberd objects for specific purposes.
"""
__revision__ = '$Id: factory.py,v 1.1 2004/03/29 09:49:06 rwx Exp $'

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


import hlbd.shell


DIRECT_SCAN = 0
DIST_SCAN = 1


def halberdFactory(scan_type, **kw):
    halberd = hlbd.shell.Halberd()

    scantime = kw.get('scantime', None)
    if scantime:
        halberd.scantime = scantime

    parallelism = kw.get('parallelism', None)
    if parallelism:
        halberd.parallelism = parallelism

    # XXX - Configuration files are always re-read. Write this in a way that
    # avoids un-needed repetition.
    conf_file = kw.get('conf_file', None)
    if conf_file:
        halberd.readConf(conf_file)
    else:
        halberd.readConf()

    halberd.verbose = kw.get('verbose', True)

    # Here we create a run method in our Halberd instance pointing to the
    # apropriate scanning method.
    if scan_type == DIST_SCAN:
        halberd.run = halberd.client
    elif scan_type == DIRECT_SCAN:
        halberd.run = halberd.scan
    else:
        # This is not supposed to happen!
        assert False

    return halberd
    

# vim: ts=4 sw=4 et
