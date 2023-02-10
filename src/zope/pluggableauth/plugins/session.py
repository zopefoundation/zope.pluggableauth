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
""" Session-based and cookie-based extractor and challenge plugins.
"""
__docformat__ = 'restructuredtext'

from urllib.parse import urlencode

import persistent
import transaction
import zope.container.contained
from zope.component import hooks
from zope.interface import Interface
from zope.interface import implementer
from zope.publisher.interfaces.http import IHTTPRequest
from zope.schema import TextLine
from zope.session.interfaces import ISession
from zope.traversing.browser.absoluteurl import absoluteURL

from zope.pluggableauth.interfaces import ICredentialsPlugin


class ISessionCredentials(Interface):
    """Interface for storing and accessing credentials in a session.

    We use a real class with interface here to prevent unauthorized
    access to the credentials.
    """

    def __init__(login, password):
        pass

    def getLogin():
        """Return login name."""

    def getPassword():
        """Return password."""


@implementer(ISessionCredentials)
class SessionCredentials:
    """Credentials class for use with sessions.

    A session credential is created with a login and a password:

      >>> cred = SessionCredentials('scott', 'tiger')

    Logins are read using getLogin:
      >>> cred.getLogin()
      'scott'

    and passwords with getPassword:

      >>> cred.getPassword()
      'tiger'

    """

    def __init__(self, login, password):
        self.login = login
        self.password = password

    def getLogin(self):
        return self.login

    def getPassword(self):
        return self.password

    def __str__(self):
        return self.getLogin() + ':' + self.getPassword()


class IBrowserFormChallenger(Interface):
    """A challenger that uses a browser form to collect user credentials."""

    loginpagename = TextLine(
        title='Loginpagename',
        description="""Name of the login form used by challenger.

        The form must provide 'login' and 'password' input fields.
        """,
        default='loginForm.html')

    loginfield = TextLine(
        title='Loginfield',
        description="Field of the login page in which is looked for the"
        " login user name.",
        default="login")

    passwordfield = TextLine(
        title='Passwordfield',
        description="Field of the login page in which is looked for the"
        " password.",
        default="password")


@implementer(ICredentialsPlugin, IBrowserFormChallenger)
class SessionCredentialsPlugin(persistent.Persistent,
                               zope.container.contained.Contained):
    """A credentials plugin that uses Zope sessions to get/store credentials.

    To illustrate how a session plugin works, we'll first setup some session
    machinery:

      >>> from zope.session.session import RAMSessionDataContainer
      >>> from zope.pluggableauth.tests import sessionSetUp
      >>> sessionSetUp(RAMSessionDataContainer)

    This lets us retrieve the same session info from any test request, which
    simulates what happens when a user submits a session ID as a cookie.

    We also need a session plugin:

      >>> plugin = SessionCredentialsPlugin()

    A session plugin uses an ISession component to store the last set of
    credentials it gets from a request. Credentials can be retrieved from
    subsequent requests using the session-stored credentials.

    Our test environment is initially configured without credentials:

      >>> from zope.pluggableauth.tests import sessionSetUp
      >>> from zope.publisher.browser import TestRequest
      >>> request = TestRequest()
      >>> print(plugin.extractCredentials(request))
      None

    We must explicitly provide credentials once so the plugin can store
    them in a session:

      >>> request = TestRequest(login='scott', password='tiger')
      >>> from pprint import pprint
      >>> pprint(plugin.extractCredentials(request))
      {'login': 'scott', 'password': 'tiger'}

    Subsequent requests now have access to the credentials even if they're
    not explicitly in the request:

      >>> pprint(plugin.extractCredentials(TestRequest()))
      {'login': 'scott', 'password': 'tiger'}

    We can always provide new credentials explicitly in the request:

      >>> pprint(plugin.extractCredentials(TestRequest(
      ...     login='harry', password='hirsch')))
      {'login': 'harry', 'password': 'hirsch'}

    and these will be used on subsequent requests:

      >>> pprint(plugin.extractCredentials(TestRequest()))
      {'login': 'harry', 'password': 'hirsch'}

    We can also change the fields from which the credentials are extracted:

      >>> plugin.loginfield = "my_new_login_field"
      >>> plugin.passwordfield = "my_new_password_field"

    Now we build a request that uses the new fields:

      >>> request = TestRequest(my_new_login_field='luke',
      ...                       my_new_password_field='the_force')

    The plugin now extracts the credentials information from these new fields:

      >>> pprint(plugin.extractCredentials(request))
      {'login': 'luke', 'password': 'the_force'}

    Finally, we clear the session credentials using the logout method:

      >>> plugin.logout(TestRequest())
      True
      >>> print(plugin.extractCredentials(TestRequest()))
      None

    Instances are persistent:

      >>> import persistent.interfaces

      >>> persistent.interfaces.IPersistent.providedBy(plugin)
      True
      >>> isinstance(plugin, persistent.Persistent)
      True

    Instances provide IContained:

      >>> import zope.location.interfaces

      >>> zope.location.interfaces.IContained.providedBy(plugin)
      True

    """

    loginpagename = 'loginForm.html'
    loginfield = 'login'
    passwordfield = 'password'

    def extractCredentials(self, request):
        """Extracts credentials from a session if they exist."""
        if not IHTTPRequest.providedBy(request):
            return None
        session = ISession(request)
        sessionData = session.get(
            'zope.pluggableauth.browserplugins')
        login = request.get(self.loginfield, None)
        password = request.get(self.passwordfield, None)
        credentials = None

        if login and password:
            credentials = self._makeCredentials(login, password)
        elif not sessionData:
            return None
        sessionData = session[
            'zope.pluggableauth.browserplugins']
        if credentials:
            sessionData['credentials'] = credentials
        else:
            credentials = sessionData.get('credentials', None)
        if not credentials:
            return None
        return {'login': credentials.getLogin(),
                'password': credentials.getPassword()}

    def _makeCredentials(self, login, password):
        """Create an ISessionCredentials.

        You can override this if you desire a different implementation, e.g.
        one that encrypts the password, so it's not stored in plain text in
        the ZODB.
        """
        return SessionCredentials(login, password)

    def challenge(self, request):
        """Challenges by redirecting to a login form.

        To illustrate, we'll create a test request:

          >>> from zope.publisher.browser import TestRequest
          >>> request = TestRequest()

        and confirm its response's initial status and 'location' header:

          >>> request.response.getStatus()
          599
          >>> request.response.getHeader('location')

        When we issue a challenge using a session plugin:

          >>> plugin = SessionCredentialsPlugin()
          >>> plugin.challenge(request)
          True

        we get a redirect:

          >>> request.response.getStatus()
          302
          >>> request.response.getHeader('location')
          'http://127.0.0.1/@@loginForm.html?camefrom=http%3A%2F%2F127.0.0.1'

        The plugin redirects to the page defined by the loginpagename
        attribute:

          >>> plugin.loginpagename = 'mylogin.html'
          >>> plugin.challenge(request)
          True
          >>> request.response.getHeader('location')
          'http://127.0.0.1/@@mylogin.html?camefrom=http%3A%2F%2F127.0.0.1'

        It also provides the request URL as a 'camefrom' GET style parameter.
        To illustrate, we'll pretend we've traversed a couple names:

          >>> env = {
          ...     'REQUEST_URI': '/foo/bar/folder/page%201.html?q=value',
          ...     'QUERY_STRING': 'q=value'
          ...     }
          >>> request = TestRequest(environ=env)
          >>> request._traversed_names = [u'foo', u'bar']
          >>> request._traversal_stack = [u'page 1.html', u'folder']
          >>> request['REQUEST_URI']
          '/foo/bar/folder/page%201.html?q=value'

        When we challenge:

          >>> plugin.challenge(request)
          True

        We see the 'camefrom' points to the requested URL:

          >>> request.response.getHeader('location')
          'http://127.0.0.1/@@mylogin.html?camefrom=http%3A%2F%2F127.0.0.1%2Ffoo%2Fbar%2Ffolder%2Fpage+1.html%3Fq%3Dvalue'

        This can be used by the login form to redirect the user back to the
        originating URL upon successful authentication.

        Now that the 'camefrom' is an absolute URL, quickly demonstrate that
        'camefrom' information that inadvertently points to a different host,
        will by default not be trusted in a redirect:

          >>> camefrom = request.response.getHeader('location')
          >>> request.response.redirect(camefrom)
          'http://127.0.0.1/@@mylogin.html?camefrom=http%3A%2F%2F127.0.0.1%2Ffoo%2Fbar%2Ffolder%2Fpage+1.html%3Fq%3Dvalue'
          >>> suspicious_camefrom = 'http://example.com/foobar'
          >>> request.response.redirect(suspicious_camefrom) # doctest: +ELLIPSIS
          Traceback (most recent call last):
          ...
          ValueError: Untrusted redirect to host 'example.com:80' not allowed.

        """   # noqa: E501 line too long
        if not IHTTPRequest.providedBy(request):
            return False

        site = hooks.getSite()
        redirectWithComeFrom(request, '{}/@@{}'.format(
            absoluteURL(site, request), self.loginpagename))
        return True

    def logout(self, request):
        """Performs logout by clearing session data credentials."""
        if not IHTTPRequest.providedBy(request):
            return False

        sessionData = ISession(request)[
            'zope.pluggableauth.browserplugins']
        sessionData['credentials'] = None
        transaction.commit()
        return True


def redirectWithComeFrom(request, location):
    """Redirect to a new location adding the current URL as ?comefrom=...

          >>> from zope.publisher.browser import TestRequest
          >>> request = TestRequest()

          >>> redirectWithComeFrom(request, 'http://127.0.0.1/login')

          >>> request.response.getStatus()
          302
          >>> request.response.getHeader('location')
          'http://127.0.0.1/login?camefrom=http%3A%2F%2F127.0.0.1'

    We'll fake up a more interesting request

          >>> env = {
          ...     'REQUEST_URI': '/foo/bar/folder/page%201.html?q=value',
          ...     'QUERY_STRING': 'q=value'
          ...     }
          >>> request = TestRequest(environ=env)
          >>> request._traversed_names = [u'foo', u'bar']
          >>> request._traversal_stack = [u'page 1.html', u'folder']
          >>> request['REQUEST_URI']
          '/foo/bar/folder/page%201.html?q=value'

          >>> redirectWithComeFrom(request, 'http://127.0.0.1/login')

          >>> request.response.getHeader('location')
          'http://127.0.0.1/login?camefrom=http%3A%2F%2F127.0.0.1%2Ffoo%2Fbar%2Ffolder%2Fpage+1.html%3Fq%3Dvalue'

    """

    # We need the traversal stack to complete the 'camefrom' parameter
    # (sice this function must work during traversal as well as after it)
    stack = request.getTraversalStack()
    stack.reverse()

    # Better to add the query string, if present
    query = request.get('QUERY_STRING')

    camefrom = '/'.join([request.getURL()] + stack)
    if query:
        camefrom = camefrom + '?' + query

    # We assume location doesn't have query parameters
    url = '{}?{}'.format(location, urlencode({'camefrom': camefrom}))
    request.response.redirect(url)
