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


"""HTTP client module.

XXX Explain why this module is written as it is.

@var default_port: Default TCP port to connect to.
@type default_port: C{int}

@var default_timeout: Default timeout for socket operations.
@type default_timeout: C{float}

@var default_bufsize: Default number of bytes to try to read from the network.
@type default_bufsize: C{int}

@var default_template: Request template, must be filled by L{HTTPClient}
@type default_template: C{str}
"""

__revision__ = '$Id: clientlib.py,v 1.5 2004/02/19 14:59:11 rwx Exp $'


import time
import socket
import urlparse


default_port = 80
default_timeout = 2

default_bufsize = 4096

default_template = """\
HEAD %(request)s HTTP/1.1\r\n\
Host: %(hostname)s\r\n\
Pragma: no-cache\r\n\
Cache-control: no-cache\r\n\
User-Agent: Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)\r\n\
Accept: image/gif, image/x-xbitmap, image/jpeg, image/pjpeg,\
 application/x-shockwave-flash, */*\r\n\
Accept-Language: en-us, en;q=0.50\r\n\
Accept-Encoding: gzip, deflate, compress;q=0.9\r\n\
Accept-Charset: ISO-8859-1, utf-8;q=0.66, *;q=0.66\r\n\
Keep-Alive: 300\r\n\
Connection: keep-alive\r\n\r\n\
"""


class HTTPException(Exception):
    pass

class InvalidScheme(HTTPException):
    pass

class TimedOut(HTTPException):
    pass

class ConnectionRefused(HTTPException):
    """Unable to reach webserver"""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class UnknownReply(HTTPException):
    """The remote host didn't return an HTTP reply"""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class HTTPClient:

    def __init__(self, timeout=default_timeout):
        """Initializes the object.

        @param timeout: Timeout for socket operations (expressed in seconds).
        @type timeout: C{float}
        """
        self.__schemes = ['http']        # Supported URL schemes.
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(timeout)

    def getHeaders(self, address, urlstr):
        self.putRequest(address, urlstr)

        timestamp, reply = self.getReply()
        if not reply:
            return None

        reply = reply.splitlines()[1:]
        reply.append('\r\n')
        reply = '\r\n'.join(reply)

        return timestamp, reply

    def putRequest(self, address, urlstr):
        """Sends an HTTP request to the target webserver.

        This method connects to the target server, sends the HTTP request and
        records a timestamp.

        @param address: Target address.
        @type address: C{str}

        @param urlstr: A valid Unified Resource Locator.
        @type urlstr: C{str}

        @raise InvalidScheme: In case the URL scheme is not HTTP or HTTPS
        @raise ConnectionRefused: If it can't reach the target webserver.
        @raise TimedOut: If we cannot send the data within the specified time.
        """
        scheme, netloc, url, params, query, fragment = urlparse.urlparse(urlstr)

        if scheme not in self.__schemes:
            raise InvalidScheme, '%s is not a supported protocol' % scheme

        hostname, port = self._getHostAndPort(netloc)
        # NOTE: address and hostname may not be the same. The caller is
        # responsible for checking that.

        try:
            self._sock.connect((address, port))
        except socket.error:
            raise ConnectionRefused, 'connection refused'
            
        req = self._fillTemplate(hostname, url, params, query, fragment)

        try:
            self._sock.sendall(req)
        except socket.timeout:
            raise TimedOut, 'timed out while writing to the network'

    def _getHostAndPort(self, netloc):
        """Determine the hostname and port to connect to from an URL

        @param netloc: Relevant part of the parsed URL.
        @type netloc: C{str}

        @return: Hostname (C{str}) and port (C{int})
        @rtype: C{tuple}
        """
        try:
            hostname, portnum = netloc.split(':')
            port = int(portnum)
        except ValueError:
            hostname, port = netloc, default_port

        return hostname, port

    def _fillTemplate(self, hostname, url, params='', query='', fragment='',
                      template=default_template):
        """Fills the request template with relevant information.

        @param hostname: Target host to reach.
        @type hostname: C{str}

        @param url: URL to use as source.
        @type url: C{str}

        @return: A request ready to be sent
        @rtype: C{str}
        """
        urlstr = url or '/'
        if params:
            urlstr += ';' + params
        if query:
            urlstr += '?' + query
        if fragment:
            urlstr += '#' + fragment

        d = {'request': urlstr, 'hostname': hostname}

        return template % d

    def getReply(self):
        """Read a reply from the server.

        @return: Received data plus the time when it arrived.
        @rtype: C{tuple}

        @raise UnknownReply: If the remote server doesn't return a valid HTTP
        reply.
        """
        # XXX Implement a real timeout for the case:
        # $ cat /dev/urandom | nc -lp 8080
        # In such situation it would read endlessly. That's bad.

        data = ''
        timestamp = None
        while 1:
            try:
                chunk = self._sock.recv(default_bufsize)
                if not timestamp:
                    timestamp = time.time()
            except:
                return None, None
    
            if not chunk:   # chunk == '' when the remote end finishes writing.
                break
            try:
                idx = chunk.index('\r\n\r\n')   # Look for terminator.
                data += chunk[:idx]
                break
            except ValueError:
                pass
            data += chunk

        if not data.startswith('HTTP/'):
            raise UnknownReply, 'invalid protocol'

        return timestamp, data


    def __del__(self):
        if self._sock:
            self._sock.close()


class HTTPSClient(HTTPClient):

    def __init__(self):
        HTTPClient.__init__(self)
        self.__schemes.append(['https'])


# vim: ts=4 sw=4 et
