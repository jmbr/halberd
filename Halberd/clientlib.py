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


"""Minimalistic asynchronous HTTP/HTTPS clients for halberd.

We need a custom client class because urllib2 and httplib don't really solve
our problems.

L{HTTPClient} and L{HTTPSClient} connect asynchronously to the specified target
and record a timestamp B{after} the connection is completed.  They also impose
a timeout so halberd doesn't wait forever if connected to a rogue HTTP server.
"""

__revision__ = '$Id: clientlib.py,v 1.1 2004/01/26 23:07:31 rwx Exp $'


import time
import socket
import urlparse
import asynchat


DEFAULT_HTTP_PORT = 80

DEFAULT_HDRS = """HEAD / HTTP/1.0\r\n\
Connection: Keep-Alive\r\n\
Accept-Encoding: gzip\r\n\
Accept-Language: en\r\n\
Accept-Charset: iso-8859-1,*,utf-8\r\n\r\n"""


class HTTPException(Exception):
    """Unspecified HTTP error.
    """
    pass

class InvalidURL(HTTPException):
    """Invalid URL.
    """
    pass

class UnknownProtocol(HTTPException):
    """Protocol not supported.
    """
    pass


class HTTPClient(asynchat.async_chat):
    """Minimalistic asynchronous HTTP client.
    """

    def __init__(self, callback, errback, callbackarg=None, hdrs=DEFAULT_HDRS):
        """Initializes the HTTPClient object.
        """
        asynchat.async_chat.__init__(self)

        # Supported protocols.
        self._schemes = ['http']

        # We store the URL as (scheme, netloc, path, params, query, fragment)
        self.__url = ()

        # Remote host address, name and port number.
        self.__address, self.__host, self.__port = '', '', 0

        # Local time when the connection to the server is established.
        self.__timestamp = 0

        # String containing the MIME headers returned by the server.
        self.__headers = ''

        self.__inbuf, self.__outbuf = '', hdrs

        # Function to call when a (time, headers) tuple is ready.
        self.__cb = callback
        # Callback argument.
        self.__cbarg = callbackarg
        # Function to call whenever an exception is captured.
        self.__eb = errback

        self.set_terminator('\r\n\r\n')

    def open(self):
        """Starts the HTTP transaction.
        """
        assert self.__host and self.__port

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.__address, self.__port))
        self.push(self.__outbuf)

    def setURL(self, address, url):
        """URL attribute accessor.

        @param address: Target IP address.
        @type address: str
        @param url: A valid URL.
        @type url: str
        """
        # XXX Change the query string according to the URL (right now it only
        # asks for /).
        self.__url = urlparse.urlparse(url)
        if self.__url[0] and self.__url[0] not in self._schemes:
            raise UnknownProtocol, 'Protocol not supported'

        # Get a valid host and port number
        if (self.__url[1].find(':') != -1):
            try:
                self.__host, port = self.__url[1].split(':')
            except ValueError:
                raise InvalidURL

            try:
                self.__port = int(port)
            except ValueError:
                raise InvalidURL
        else:
            self.__address = address
            self.__host = self.__url[1]
            self.__port = DEFAULT_HTTP_PORT

        return self

    def getURL(self):
        """URL attribute accessor.

        @return: Target URL.
        @rtype: str
        """
        return urlparse.urlunparse(self.__url)

    def getHost(self):
        """Host accessor.

        @return: Host name
        @rtype: str
        """
        return self.__host

    def getPort(self):
        """Port accessor.

        @return: Port number.
        @rtype: int
        """
        return self.__port

    def getTimestamp(self):
        """Timestamp accessor.

        @return: Local time at connection establishment.
        @rtype: int
        """
        return self.__timestamp

    def getHeaders(self):
        """Headers accessor.

        @return: Headers replied by the target server. It is the caller's
            responsibility to convert this into a proper rfc822.Message.
        @rtype: str
        """
        return self.__headers
        

    # ==========================
    # Extensions for async_chat.
    # ==========================

    def collect_incoming_data(self, data):
        self.__inbuf += str(data)

    def found_terminator(self):
        if self.__inbuf.startswith('HTTP/'):
            self.__headers = self.__inbuf[self.__inbuf.find('\r\n'):]
            self.close()
            self.__cb(self.__cbarg, self.__timestamp, self.__headers)

    def handle_connect(self):
        pass

    def handle_write(self):
        try:
            asynchat.async_chat.handle_write(self)
        except:
            self.__eb(self.__cbarg)

        self.__timestamp = time.time()

    def handle_read(self):
        try:
            asynchat.async_chat.handle_read(self)
        except:
            self.__eb(self.__cbarg)

    def handle_close(self):
        self.close()


class HTTPSClient(HTTPClient):
    """Minimalistic asynchronous HTTPS client.
    """

    def __init__(self):
        """Initializes the HTTPSClient object.
        """
        HTTPClient.__init__(self)
        self._schemes.append('https')


# vim: ts=4 sw=4 et
