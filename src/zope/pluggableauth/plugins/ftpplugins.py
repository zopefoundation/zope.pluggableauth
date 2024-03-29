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
"""PAS plugins related to FTP
"""
__docformat__ = 'restructuredtext'

from zope.interface import implementer
from zope.publisher.interfaces.ftp import IFTPRequest

from zope.pluggableauth import interfaces


@implementer(interfaces.ICredentialsPlugin)
class FTPCredentialsPlugin:

    def extractCredentials(self, request):
        """Extracts the FTP credentials from a request.

        First we need to create a FTP request that contains some credentials.
        Note the path is a required in the envirnoment.

          >>> from zope.publisher.ftp import FTPRequest
          >>> from io import StringIO
          >>> request = FTPRequest(StringIO(''),
          ...                      {'credentials': (b'bob', b'123'),
          ...                       'path': '/a/b/c'})

        Now we create the plugin and get the credentials.

          >>> plugin = FTPCredentialsPlugin()
          >>> from pprint import pprint
          >>> pprint(plugin.extractCredentials(request))
          {'login': 'bob', 'password': '123'}

        This only works for FTPRequests.

          >>> from zope.publisher.base import TestRequest
          >>> print(plugin.extractCredentials(TestRequest('/')))
          None

        """
        if not IFTPRequest.providedBy(request):
            return None

        if request._auth:
            login, password = request._auth
            return {'login': login.decode('utf-8'),
                    'password': password.decode('utf-8')}
        return None

    def challenge(self, request):
        return False

    def logout(self, request):
        return False
