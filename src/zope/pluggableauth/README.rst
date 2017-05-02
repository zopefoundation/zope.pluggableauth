==================================
 Pluggable-Authentication Utility
==================================

The Pluggable-Authentication Utility (PAU) provides a framework for
authenticating principals and associating information with them. It uses
plugins and subscribers to get its work done.

For a pluggable-authentication utility to be used, it should be
registered as a utility providing the
`zope.authentication.interfaces.IAuthentication` interface.

Authentication
==============

The primary job of PAU is to authenticate principals. It uses two types of
plug-ins in its work:

- Credentials Plugins

- Authenticator Plugins

Credentials plugins are responsible for extracting user credentials from a
request. A credentials plugin may in some cases issue a 'challenge' to obtain
credentials. For example, a 'session' credentials plugin reads credentials
from a session (the "extraction"). If it cannot find credentials, it will
redirect the user to a login form in order to provide them (the "challenge").

Authenticator plugins are responsible for authenticating the credentials
extracted by a credentials plugin. They are also typically able to create
principal objects for credentials they successfully authenticate.

Given a request object, the PAU returns a principal object, if it can. The PAU
does this by first iterating through its credentials plugins to obtain a
set of credentials. If it gets credentials, it iterates through its
authenticator plugins to authenticate them.

If an authenticator succeeds in authenticating a set of credentials, the PAU
uses the authenticator to create a principal corresponding to the credentials.
The authenticator notifies subscribers if an authenticated principal is
created. Subscribers are responsible for adding data, especially groups, to
the principal. Typically, if a subscriber adds data, it should also add
corresponding interface declarations.

Simple Credentials Plugin
-------------------------

To illustrate, we'll create a simple credentials plugin:

  >>> from zope import interface
  >>> from zope.pluggableauth.authentication import interfaces

  >>> @interface.implementer(interfaces.ICredentialsPlugin)
  ... class MyCredentialsPlugin(object):
  ...
  ...     def extractCredentials(self, request):
  ...         return request.get('credentials')
  ...
  ...     def challenge(self, request):
  ...         pass # challenge is a no-op for this plugin
  ...
  ...     def logout(self, request):
  ...         pass # logout is a no-op for this plugin

As a plugin, MyCredentialsPlugin needs to be registered as a named utility:

  >>> myCredentialsPlugin = MyCredentialsPlugin()
  >>> provideUtility(myCredentialsPlugin, name='My Credentials Plugin')

Simple Authenticator Plugin
---------------------------

Next we'll create a simple authenticator plugin. For our plugin, we'll need
an implementation of IPrincipalInfo:

  >>> @interface.implementer(interfaces.IPrincipalInfo)
  ... class PrincipalInfo(object):
  ...
  ...     def __init__(self, id, title, description):
  ...         self.id = id
  ...         self.title = title
  ...         self.description = description
  ...
  ...     def __repr__(self):
  ...         return 'PrincipalInfo(%r)' % self.id

Our authenticator uses this type when it creates a principal info:

  >>> @interface.implementer(interfaces.IAuthenticatorPlugin)
  ... class MyAuthenticatorPlugin(object):
  ...
  ...     def authenticateCredentials(self, credentials):
  ...         if credentials == 'secretcode':
  ...             return PrincipalInfo('bob', 'Bob', '')
  ...
  ...     def principalInfo(self, id):
  ...         pass # plugin not currently supporting search

As with the credentials plugin, the authenticator plugin must be registered
as a named utility:

  >>> myAuthenticatorPlugin = MyAuthenticatorPlugin()
  >>> provideUtility(myAuthenticatorPlugin, name='My Authenticator Plugin')

Configuring a PAU
-----------------

Finally, we'll create the PAU itself:

  >>> from zope.pluggableauth import authentication
  >>> pau = authentication.PluggableAuthentication('xyz_')

and configure it with the two plugins:

  >>> pau.credentialsPlugins = ('My Credentials Plugin', )
  >>> pau.authenticatorPlugins = ('My Authenticator Plugin', )

Using the PAU to Authenticate
-----------------------------

  >>> from zope.pluggableauth.factories import AuthenticatedPrincipalFactory
  >>> provideAdapter(AuthenticatedPrincipalFactory)

We can now use the PAU to authenticate a sample request:

  >>> from zope.publisher.browser import TestRequest
  >>> print(pau.authenticate(TestRequest()))
  None

In this case, we cannot authenticate an empty request. In the same way, we
will not be able to authenticate a request with the wrong credentials:

  >>> print(pau.authenticate(TestRequest(credentials='let me in!')))
  None

However, if we provide the proper credentials:

  >>> request = TestRequest(credentials='secretcode')
  >>> principal = pau.authenticate(request)
  >>> principal
  Principal('xyz_bob')

we get an authenticated principal.

Multiple Authenticator Plugins
------------------------------

The PAU works with multiple authenticator plugins. It uses each plugin, in the
order specified in the PAU's authenticatorPlugins attribute, to authenticate
a set of credentials.

To illustrate, we'll create another authenticator:

  >>> class MyAuthenticatorPlugin2(MyAuthenticatorPlugin):
  ...
  ...     def authenticateCredentials(self, credentials):
  ...         if credentials == 'secretcode':
  ...             return PrincipalInfo('black', 'Black Spy', '')
  ...         elif credentials == 'hiddenkey':
  ...             return PrincipalInfo('white', 'White Spy', '')

  >>> provideUtility(MyAuthenticatorPlugin2(), name='My Authenticator Plugin 2')

If we put it before the original authenticator:

  >>> pau.authenticatorPlugins = (
  ...     'My Authenticator Plugin 2',
  ...     'My Authenticator Plugin')

Then it will be given the first opportunity to authenticate a request:

  >>> pau.authenticate(TestRequest(credentials='secretcode'))
  Principal('xyz_black')

If neither plugins can authenticate, pau returns None:

  >>> print(pau.authenticate(TestRequest(credentials='let me in!!')))
  None

When we change the order of the authenticator plugins:

  >>> pau.authenticatorPlugins = (
  ...     'My Authenticator Plugin',
  ...     'My Authenticator Plugin 2')

we see that our original plugin is now acting first:

  >>> pau.authenticate(TestRequest(credentials='secretcode'))
  Principal('xyz_bob')

The second plugin, however, gets a chance to authenticate if first does not:

  >>> pau.authenticate(TestRequest(credentials='hiddenkey'))
  Principal('xyz_white')

Multiple Credentials Plugins
----------------------------

As with with authenticators, we can specify multiple credentials plugins. To
illustrate, we'll create a credentials plugin that extracts credentials from
a request form:

  >>> @interface.implementer(interfaces.ICredentialsPlugin)
  ... class FormCredentialsPlugin:
  ...
  ...     def extractCredentials(self, request):
  ...         return request.form.get('my_credentials')
  ...
  ...     def challenge(self, request):
  ...         pass
  ...
  ...     def logout(request):
  ...         pass

  >>> provideUtility(FormCredentialsPlugin(),
  ...                name='Form Credentials Plugin')

and insert the new credentials plugin before the existing plugin:

  >>> pau.credentialsPlugins = (
  ...     'Form Credentials Plugin',
  ...     'My Credentials Plugin')

The PAU will use each plugin in order to try and obtain credentials from a
request:

  >>> pau.authenticate(TestRequest(credentials='secretcode',
  ...                              form={'my_credentials': 'hiddenkey'}))
  Principal('xyz_white')

In this case, the first credentials plugin succeeded in getting credentials
from the form and the second authenticator was able to authenticate the
credentials. Specifically, the PAU went through these steps:

- Get credentials using 'Form Credentials Plugin'

- Got 'hiddenkey' credentials using 'Form Credentials Plugin', try to
  authenticate using 'My Authenticator Plugin'

- Failed to authenticate 'hiddenkey' with 'My Authenticator Plugin', try
  'My Authenticator Plugin 2'

- Succeeded in authenticating with 'My Authenticator Plugin 2'

Let's try a different scenario:

  >>> pau.authenticate(TestRequest(credentials='secretcode'))
  Principal('xyz_bob')

In this case, the PAU went through these steps::

- Get credentials using 'Form Credentials Plugin'

- Failed to get credentials using 'Form Credentials Plugin', try
  'My Credentials Plugin'

- Got 'scecretcode' credentials using 'My Credentials Plugin', try to
  authenticate using 'My Authenticator Plugin'

- Succeeded in authenticating with 'My Authenticator Plugin'

Let's try a slightly more complex scenario:

  >>> pau.authenticate(TestRequest(credentials='hiddenkey',
  ...                              form={'my_credentials': 'bogusvalue'}))
  Principal('xyz_white')

This highlights PAU's ability to use multiple plugins for authentication:

- Get credentials using 'Form Credentials Plugin'

- Got 'bogusvalue' credentials using 'Form Credentials Plugin', try to
  authenticate using 'My Authenticator Plugin'

- Failed to authenticate 'boguskey' with 'My Authenticator Plugin', try
  'My Authenticator Plugin 2'

- Failed to authenticate 'boguskey' with 'My Authenticator Plugin 2' --
  there are no more authenticators to try, so lets try the next credentials
  plugin for some new credentials

- Get credentials using 'My Credentials Plugin'

- Got 'hiddenkey' credentials using 'My Credentials Plugin', try to
  authenticate using 'My Authenticator Plugin'

- Failed to authenticate 'hiddenkey' using 'My Authenticator Plugin', try
  'My Authenticator Plugin 2'

- Succeeded in authenticating with 'My Authenticator Plugin 2' (shouts and
  cheers!)

Multiple Authenticator Plugins
------------------------------

As with the other operations we've seen, the PAU uses multiple plugins to
find a principal. If the first authenticator plugin can't find the requested
principal, the next plugin is used, and so on.

  >>> @interface.implementer(interfaces.IAuthenticatorPlugin)
  ... class AnotherAuthenticatorPlugin:
  ...
  ...     def __init__(self):
  ...         self.infos = {}
  ...         self.ids = {}
  ...
  ...     def principalInfo(self, id):
  ...         return self.infos.get(id)
  ...
  ...     def authenticateCredentials(self, credentials):
  ...         id = self.ids.get(credentials)
  ...         if id is not None:
  ...             return self.infos[id]
  ...
  ...     def add(self, id, title, description, credentials):
  ...         self.infos[id] = PrincipalInfo(id, title, description)
  ...         self.ids[credentials] = id


To illustrate, we'll create and register two authenticators:

  >>> authenticator1 = AnotherAuthenticatorPlugin()
  >>> provideUtility(authenticator1, name='Authentication Plugin 1')

  >>> authenticator2 = AnotherAuthenticatorPlugin()
  >>> provideUtility(authenticator2, name='Authentication Plugin 2')

and add a principal to them:

  >>> authenticator1.add('bob', 'Bob', 'A nice guy', 'b0b')
  >>> authenticator1.add('white', 'White Spy', 'Sneaky', 'deathtoblack')
  >>> authenticator2.add('black', 'Black Spy', 'Also sneaky', 'deathtowhite')

When we configure the PAU to use both searchable authenticators (note the
order):

  >>> pau.authenticatorPlugins = (
  ...     'Authentication Plugin 2',
  ...     'Authentication Plugin 1')

we register the factories for our principals:

  >>> from zope.pluggableauth.factories import FoundPrincipalFactory
  >>> provideAdapter(FoundPrincipalFactory)

we see how the PAU uses both plugins:

  >>> pau.getPrincipal('xyz_white')
  Principal('xyz_white')

  >>> pau.getPrincipal('xyz_black')
  Principal('xyz_black')

If more than one plugin know about the same principal ID, the first plugin is
used and the remaining are not delegated to. To illustrate, we'll add
another principal with the same ID as an existing principal:

  >>> authenticator2.add('white', 'White Rider', '', 'r1der')
  >>> pau.getPrincipal('xyz_white').title
  'White Rider'

If we change the order of the plugins:

  >>> pau.authenticatorPlugins = (
  ...     'Authentication Plugin 1',
  ...     'Authentication Plugin 2')

we get a different principal for ID 'white':

  >>> pau.getPrincipal('xyz_white').title
  'White Spy'


Issuing a Challenge
===================

Part of PAU's IAuthentication contract is to challenge the user for
credentials when its 'unauthorized' method is called. The need for this
functionality is driven by the following use case:

- A user attempts to perform an operation he is not authorized to perform.

- A handler responds to the unauthorized error by calling IAuthentication
  'unauthorized'.

- The authentication component (in our case, a PAU) issues a challenge to
  the user to collect new credentials (typically in the form of logging in
  as a new user).

The PAU handles the credentials challenge by delegating to its credentials
plugins.

Currently, the PAU is configured with the credentials plugins that don't
perform any action when asked to challenge (see above the 'challenge' methods).

To illustrate challenges, we'll subclass an existing credentials plugin and
do something in its 'challenge':

  >>> class LoginFormCredentialsPlugin(FormCredentialsPlugin):
  ...
  ...     def __init__(self, loginForm):
  ...         self.loginForm = loginForm
  ...
  ...     def challenge(self, request):
  ...         request.response.redirect(self.loginForm)
  ...         return True

This plugin handles a challenge by redirecting the response to a login form.
It returns True to signal to the PAU that it handled the challenge.

We will now create and register a couple of these plugins:

  >>> provideUtility(LoginFormCredentialsPlugin('simplelogin.html'),
  ...                name='Simple Login Form Plugin')

  >>> provideUtility(LoginFormCredentialsPlugin('advancedlogin.html'),
  ...                name='Advanced Login Form Plugin')

and configure the PAU to use them:

  >>> pau.credentialsPlugins = (
  ...     'Simple Login Form Plugin',
  ...     'Advanced Login Form Plugin')

Now when we call 'unauthorized' on the PAU:

  >>> request = TestRequest()
  >>> pau.unauthorized(id=None, request=request)

we see that the user is redirected to the simple login form:

  >>> request.response.getStatus()
  302
  >>> request.response.getHeader('location')
  'simplelogin.html'

We can change the challenge policy by reordering the plugins:

  >>> pau.credentialsPlugins = (
  ...     'Advanced Login Form Plugin',
  ...     'Simple Login Form Plugin')

Now when we call 'unauthorized':

  >>> request = TestRequest()
  >>> pau.unauthorized(id=None, request=request)

the advanced plugin is used because it's first:

  >>> request.response.getStatus()
  302
  >>> request.response.getHeader('location')
  'advancedlogin.html'

Challenge Protocols
-------------------

Sometimes, we want multiple challengers to work together. For example, the
HTTP specification allows multiple challenges to be issued in a response. A
challenge plugin can provide a `challengeProtocol` attribute that effectively
groups related plugins together for challenging. If a plugin returns `True`
from its challenge and provides a non-None challengeProtocol, subsequent
plugins in the credentialsPlugins list that have the same challenge protocol
will also be used to challenge.

Without a challengeProtocol, only the first plugin to succeed in a challenge
will be used.

Let's look at an example. We'll define a new plugin that specifies an
'X-Challenge' protocol:

  >>> class XChallengeCredentialsPlugin(FormCredentialsPlugin):
  ...
  ...     challengeProtocol = 'X-Challenge'
  ...
  ...     def __init__(self, challengeValue):
  ...         self.challengeValue = challengeValue
  ...
  ...     def challenge(self, request):
  ...         value = self.challengeValue
  ...         existing = request.response.getHeader('X-Challenge', '')
  ...         if existing:
  ...             value += ' ' + existing
  ...         request.response.setHeader('X-Challenge', value)
  ...         return True

and register a couple instances as utilities:

  >>> provideUtility(XChallengeCredentialsPlugin('basic'),
  ...                name='Basic X-Challenge Plugin')

  >>> provideUtility(XChallengeCredentialsPlugin('advanced'),
  ...                name='Advanced X-Challenge Plugin')

When we use both plugins with the PAU:

  >>> pau.credentialsPlugins = (
  ...     'Basic X-Challenge Plugin',
  ...     'Advanced X-Challenge Plugin')

and call 'unauthorized':

  >>> request = TestRequest()
  >>> pau.unauthorized(None, request)

we see that both plugins participate in the challenge, rather than just the
first plugin:

  >>> request.response.getHeader('X-Challenge')
  'advanced basic'


Pluggable-Authentication Prefixes
=================================

Principal ids are required to be unique system wide. Plugins will often provide
options for providing id prefixes, so that different sets of plugins provide
unique ids within a PAU. If there are multiple pluggable-authentication
utilities in a system, it's a good idea to give each PAU a unique prefix, so
that principal ids from different PAUs don't conflict. We can provide a prefix
when a PAU is created:

  >>> pau = authentication.PluggableAuthentication('mypau_')
  >>> pau.credentialsPlugins = ('My Credentials Plugin', )
  >>> pau.authenticatorPlugins = ('My Authenticator Plugin', )

When we create a request and try to authenticate:

  >>> pau.authenticate(TestRequest(credentials='secretcode'))
  Principal('mypau_bob')

Note that now, our principal's id has the pluggable-authentication
utility prefix.

We can still lookup a principal, as long as we supply the prefix::

  >> pau.getPrincipal('mypas_42')
  Principal('mypas_42', "{'domain': 42}")

  >> pau.getPrincipal('mypas_41')
  OddPrincipal('mypas_41', "{'int': 41}")
