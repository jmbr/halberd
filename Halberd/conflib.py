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


"""Configuration file management module.

Halberd uses configuration files mainly for its proxy support and the
distributed framework. Configuration files keep the information the program
needs to act as a proxy server or connect to other peers in order to scan a
target in parallel.

@var default_cfgfile: Path and name of the configuration file used by default.
@type default_cfgfile: C{str}

@var default_proxy_port: Default TCP port to listen when acting as a proxy.
@type default_proxy_port: C{int}

@var default_rpc_port: Default TCP port to listen when acting as an RPC server.
@type default_rpc_port: C{int}
"""

__revision__ = '$Id: conflib.py,v 1.4 2004/03/02 11:56:42 rwx Exp $'


import os
import os.path
import ConfigParser


default_proxy_port = 8080
default_rpc_port = 2323


class InvalidConfFile(Exception):
    """Invalid configuration file.
    """


class ConfOptions:
    proxy_serv_addr = ()
    rpc_serv_addr = ()
    rpc_servers = []


class ConfReader:

    def __init__(self):
        self.__dict = {}
        self.__conf = None

        self.confparser = ConfigParser.RawConfigParser()

    def open(self, fname):
        """Opens the configuration file.

        @param fname: Pathname to the configuration file.
        @type fname: C{str}

        @raise InvalidConfFile: In case the passed file is not a valid one.
        """
        self.__conf = open(os.path.expanduser(fname))
        try:
            self.confparser.readfp(self.__conf, fname)
        except ConfigParser.MissingSectionHeaderError, msg:
            raise InvalidConfFile, msg

    def close(self):
        """Release the configuration file's descriptor.
        """
        if self.__conf:
            self.__conf.close()


    def _getAddr(self, sectname, default_port):
        section = self.__dict[sectname]
        addr = section.get('address', '')
        try:
            port = int(section.get('port', default_port))
        except ValueError:
            port = default_port

        return (addr, port)

    def parse(self):
        """Parses the configuration file.
        """
        assert self.__conf, 'The configuration file is not open'

        options = ConfOptions()

        # The orthodox way of doing this is via ConfigParser.get*() but those
        # methods lack the convenience of dict.get. While another approach
        # could be to subclass ConfigParser I think it's overkill for the
        # current situation.
        for section in self.confparser.sections():
            sec = self.__dict.setdefault(section, {})
            for name, value in self.confparser.items(section):
                sec.setdefault(name, value)

        if self.__dict.has_key('proxy'):
            options.proxy_serv_addr = self._getAddr('proxy',
                                                    default_proxy_port)

        if self.__dict.has_key('rpcserver'):
            options.rpc_serv_addr = self._getAddr('rpcserver',
                                                  default_rpc_port)

        try:
            rpc_servers = self.__dict['rpcclient']['servers']
            rpc_servers = [server.strip() for server in rpc_servers.split(',')\
                                          if server]
        except KeyError:
            rpc_servers = []

        options.rpc_servers = rpc_servers

        return options


    def __del__(self):
        self.close()


# vim: ts=4 sw=4 et
