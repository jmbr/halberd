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


"""Massive load balancer scanner.
"""

__revision__ = '$Id: bulkscan.py,v 1.5 2004/03/04 11:55:57 rwx Exp $'


import os
import sys
import shutil
import pickle

import halberd
import hlbd.util
import hlbd.clues.file


def error(msg):
    sys.stderr.write('%s\n' % str(msg))
    sys.stderr.flush()
    sys.exit(-1)

def targets(urlfile):
    for url in urlfile:
        if url == '\n':
            continue

        # Strip end of line character.
        url = url[:-1]

        hostname = halberd.hostname(url)
        if not hostname:
            sys.stderr.write('*** unable to extract hostname from %s\n' \
                             % hostname)
            continue

        for addr in halberd.addresses(hostname):
            yield (url, addr)

def make_dir(dest):
    try:
        st = os.stat(dest)
    except OSError:
        try:
            os.mkdir(dest)
        except OSError, msg:
            error(msg)
    else:
        if not shutil.stat.S_ISDIR(st.st_mode):
            error('%s already exist and is not a directory' % dest)

def main():
    if len(sys.argv) < 3:
        error('usage: %s <url-file> <dest-dir>' % sys.argv[0])

    folder = sys.argv[2]

    make_dir(folder)

    urlfile = ''
    try:
        urlfile = open(sys.argv[1], 'r')
    except IOError, msg:
        error('open: %s' % msg)
            
    for target in targets(urlfile):
        url, addr = target

        h = halberd.Halberd()
        h.scantime = 15
        h.setAddr(addr)
        h.setURL(url)
        h.verbose = True

        print 'scanning %s (%s)' % (url, addr)

        h.scan()

        urldir = url.translate(hlbd.util.table)
        make_dir(os.path.join(folder, urldir))

        clue_file = os.path.join(folder, urldir, addr)
        try:
            hlbd.clues.file.save(clue_file, h.clues)
        except IOError, msg:
            error(msg)


if __name__ == '__main__':
    main()


# vim: ts=4 sw=4 et
