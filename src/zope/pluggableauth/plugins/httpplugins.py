##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""PAS plugins related to HTTP
"""
__docformat__ = "reStructuredText"

import base64

from zope.interface import Interface
from zope.interface import implementer
from zope.publisher.interfaces.http import IHTTPRequest
from zope.schema import TextLine

from zope.pluggableauth import interfaces


class IHTTPBasicAuthRealm(Interface):
    """HTTP Basic Auth Realm

    Represents the realm string that is used during basic HTTP authentication
    """

    realm = TextLine(title='Realm',
                     description='HTTP Basic Authentication Realm',
                     required=True,
                     default='Zope')


@implementer(interfaces.ICredentialsPlugin, IHTTPBasicAuthRealm)
class HTTPBasicAuthCredentialsPlugin:

    realm = 'Zope'

    protocol = 'http auth'

    def extractCredentials(self, request):
        """Extracts HTTP basic auth credentials from a request.

        First we need to create a request that contains some credentials.

          >>> from zope.publisher.browser import TestRequest
          >>> request = TestRequest(
          ...     environ={'HTTP_AUTHORIZATION': 'Basic bWdyOm1ncnB3'})

        Now create the plugin and get the credentials.

          >>> plugin = HTTPBasicAuthCredentialsPlugin()
          >>> from pprint import pprint
          >>> pprint(plugin.extractCredentials(request))
          {'login': 'mgr', 'password': 'mgrpw'}

        Make sure we return `None`, if no authentication header has been
        specified.

          >>> print(plugin.extractCredentials(TestRequest()))
          None

        Also, this plugin can *only* handle basic authentication.

          >>> request = TestRequest(environ={'HTTP_AUTHORIZATION': 'foo bar'})
          >>> print(plugin.extractCredentials(TestRequest()))
          None

        This plugin only works with HTTP requests.

          >>> from zope.publisher.base import TestRequest
          >>> print(plugin.extractCredentials(TestRequest('/')))
          None

        According to RFC 2617, password can contain one or more colons; user ID
        can't contain any colon.

          >>> from zope.publisher.browser import TestRequest as BrowserRequest
          >>> request = BrowserRequest('/',
          ...     environ={'HTTP_AUTHORIZATION': 'Basic bWdyOm1ncnB3OndpdGg6Y29sb24='})
          >>> pprint(plugin.extractCredentials(request))
          {'login': 'mgr', 'password': 'mgrpw:with:colon'}

        """  # noqa: E501 line too long
        if not IHTTPRequest.providedBy(request):
            return None

        if request._auth:
            if request._auth.lower().startswith('basic '):
                credentials = request._auth.split()[-1]
                if isinstance(credentials, str):
                    # No encoding needed, should be base64 string anyways.
                    credentials = credentials.encode()
                login, password = base64.b64decode(credentials).split(b':', 1)
                return {'login': login.decode('utf-8'),
                        'password': password.decode('utf-8')}
        return None

    def challenge(self, request):
        """Issues an HTTP basic auth challenge for credentials.

        The challenge is issued by setting the appropriate response headers.
        To illustrate, we'll create a plugin:

          >>> plugin = HTTPBasicAuthCredentialsPlugin()

        The plugin adds its challenge to the HTTP response.

          >>> from zope.publisher.browser import TestRequest
          >>> request = TestRequest()
          >>> response = request.response
          >>> plugin.challenge(request)
          True
          >>> response._status
          401
          >>> response.getHeader('WWW-Authenticate', literal=True)
          'basic realm="Zope"'

        Notice that the realm is quoted, as per RFC 2617.

        The plugin only works with HTTP requests.

          >>> from zope.publisher.base import TestRequest
          >>> request = TestRequest('/')
          >>> response = request.response
          >>> print(plugin.challenge(request))
          False

        """
        if not IHTTPRequest.providedBy(request):
            return False
        request.response.setHeader("WWW-Authenticate",
                                   'basic realm="%s"' % self.realm,
                                   literal=True)
        request.response.setStatus(401)
        return True

    def logout(self, request):
        """Always returns False as logout is not supported by basic auth.

          >>> plugin = HTTPBasicAuthCredentialsPlugin()
          >>> from zope.publisher.browser import TestRequest
          >>> plugin.logout(TestRequest())
          False

        """
        return False
