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


from distutils.core import setup

from hlbd.version import version


setup(name = 'halberd', version = version.v_short,
      description = 'HTTP load balancer detector',
      author = 'Juan M. Bello Rivas',
      author_email = 'rwx+halberd@synnergy.net',
      url = 'http://www.synnergy.net/~rwx/halberd',
      license = 'GNU GENERAL PUBLIC LICENSE',
      package_dir = {'hlbd': 'hlbd'},
      scripts = ['halberd.py'],
)


# vim: ts=4 sw=4 et
