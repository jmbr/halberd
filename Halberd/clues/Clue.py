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


"""Clue generation module.

Clues are pieces of information obtained from the responses sent by a
webserver.
Their importance comes from the fact that they're the datastructure we use to
detect real servers behind HTTP load balancer devices.
"""

__revision__ = '$Id: Clue.py,v 1.3 2004/02/15 17:00:39 rwx Exp $'


import time
import rfc822

try:
    from sha import new as hashfn
except ImportError:
    from md5 import new as hashfn



class Clue:
    """A clue is what we use to tell real servers behind a virtual IP. 

    Clues are gathered during several connections to a web server and they
    allow us to try to identify patterns in its responses. Those patterns could
    allow us to find out which real servers are behind a VIP
    """
    def __init__(self):
        # Number of times this clue has been found.
        self.__count = 1

        # Generic server info (sometimes useful for distinguising servers).
        self.info = {
            'server': '',
            'contloc': '',
            'cookie': '',
            'date': '',
            'digest': ''
        }

        # Local time and remote time (in seconds since the Epoch)
        self._local, self._remote = 0, 0

        self.diff = None

        # We store the headers we're interested in digesting in a string and
        # calculate its hash _after_ the header processing takes place. This
        # way we incur in less computational overhead.
        self.__tmphdrs = ''

        # Original MIME headers. They're useful during analysis and reporting.
        self.headers = None


    def parse(self, headers):
        """Extracts all relevant information from the MIME headers replied by
        the target.

        @param headers: MIME headers replied by the target.
        @type headers: str
        """
        def make_list(hdrs):
            """Create a list of name, value tuples from the server's response.

            We use a list instead of a dictionary because with the list we keep
            the header's order as sent by the target, which is a relevant piece
            of information we cannot afford to miss.
            """
            # We split by ':' instead of ': ' because it's more robust (some
            # webservers may send badly written headers).
            return [tuple(line.split(':', 1)) for line in hdrs.splitlines() \
                                              if line != '']

        self.headers = make_list(headers)

        # We examine each MIME field and try to find an appropriate handler. If
        # there is none we simply digest the info it provides.
        for name, value in self.headers:
            try:
                handlerfn = getattr(self, '_get_' + Clue.normalize(name))
                handlerfn(value)
            except AttributeError:
                self.__tmphdrs += '%s: %s ' % (name, value)

        self._updateDigest()
        self._calcDiff()

    def normalize(name):
        """Normalize string.

        This method takes a string coming out of mime-fields and transforms it
        into a valid Python identifier. That's done by removing invalid
        non-alphanumeric characters and also numeric ones placed at the
        beginning of the string.

        @param name: String to be normalized.
        @type name: C{str}

        @return: Normalized string.
        @rtype: C{str}
        """
        normal = [char for char in list(name.lower()) if char.isalnum()]
        while normal[0].isdigit():
            normal = normal[1:]
        return ''.join(normal)

    normalize = staticmethod(normalize)

    def _updateDigest(self):
        """Updates header fingerprint.
        """
        fingerprint = hashfn(self.__tmphdrs)
        self.__tmphdrs = ''
        self.info['digest'] = fingerprint.hexdigest()

    def _calcDiff(self):
        """Compute the time difference between the remote and local clocks.

        @return: Time difference.
        @rtype: C{int}
        """
        self.diff = int(self._local - self._remote)


    def incCount(self, num=1):
        """Increase the times this clue has been found.

        @param num: A positive non-zero number of hits to increase.
        @type num: C{int}

        @raise ValueError: in case L{num} is less than or equal to zero.
        """
        if num <= 0:
            raise ValueError
        self.__count += num

    def getCount(self):
        """Retrieve the number of times the clue has been found

        @return: Number of hits.
        @rtype: C{int}.
        """
        return self.__count


    def setTimestamp(self, timestamp):
        """Sets the local clock attribute.

        @param timestamp: The local time (expressed in seconds since the Epoch)
        when the connection to the target was successfully completed.
        @type timestamp: C{int}
        """
        self._local = timestamp


    def __eq__(self, other):
        if self.diff != other.diff:
            return False

        if self.info['digest'] != other.info['digest']:
            return False

        return True

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        if not (self.diff or self.info['digest']):
            return "<Clue at %x>" % id(self)
        return "<Clue at %x diff=%d found=%d digest='%s'>" \
                % (id(self), self.diff, self.__count,
                   self.info['digest'][:4] + '...')

    # ==================================================================
    # The following methods extract relevant data from the MIME headers.
    # ==================================================================

    def _get_server(self, field):
        """Server:"""
        self.info['server'] = field
        self.__tmphdrs += field     # Make sure this gets hashed too.

    def _get_date(self, field):
        """Date:"""
        self.info['date'] = field
        self._remote = time.mktime(rfc822.parsedate(field))

    def _get_contentlocation(self, field):
        """Content-location:"""
        self.info['contloc'] = field
        self.__tmphdrs += field

    def _get_setcookie(self, field):
        """Set-cookie:"""
        self.info['cookie'] = field

    def _get_expires(self, field):
        """Expires:"""
        pass    # By passing we prevent this header from being hashed.

    def _get_age(self, field):
        """Age:"""
        pass

    def _get_contentlength(self, field):
        """Content-length:"""
        pass

    def _get_lastmodified(self, field):
        """Last-modified:"""
        pass

    def _get_etag(self, field):
        """ETag:"""
        pass

    def _get_cacheexpires(self, field):
        """Cache-expires:"""
        pass


# vim: ts=4 sw=4 et
