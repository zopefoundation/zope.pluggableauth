##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Pluggable Authentication Utility Interfaces

$Id$
"""
__docformat__ = "reStructuredText"

import zope.interface
from zope.i18nmessageid import MessageFactory
from zope.authentication.interfaces import ILogout
from zope.schema import Choice, List, TextLine
from zope.container.constraints import contains, containers
from zope.container.interfaces import IContainer

_ = MessageFactory('zope')


class IPlugin(zope.interface.Interface):
    """A plugin for a pluggable authentication component."""


class IPluggableAuthentication(ILogout, IContainer):
    """Provides authentication services with the help of various plugins.

    IPluggableAuthentication implementations will also implement
    zope.authentication.interfaces.IAuthentication.  The `authenticate` method
    of this interface in an IPluggableAuthentication should annotate the
    IPrincipalInfo with the credentials plugin and authentication plugin used.
    The `getPrincipal` method should annotate the IPrincipalInfo with the
    authentication plugin used.
    """

    contains(IPlugin)

    credentialsPlugins = zope.schema.List(
        title=_('Credentials Plugins'),
        description=_("""Used for extracting credentials.
        Names may be of ids of non-utility ICredentialsPlugins contained in
        the IPluggableAuthentication, or names of registered
        ICredentialsPlugins utilities. Contained non-utility ids mask 
        utility names."""),
        value_type=zope.schema.Choice(vocabulary='CredentialsPlugins'),
        default=[],
        )

    authenticatorPlugins = zope.schema.List(
        title=_('Authenticator Plugins'),
        description=_("""Used for converting credentials to principals.
        Names may be of ids of non-utility IAuthenticatorPlugins contained in
        the IPluggableAuthentication, or names of registered
        IAuthenticatorPlugins utilities.  Contained non-utility ids mask 
        utility names."""),
        value_type=zope.schema.Choice(vocabulary='AuthenticatorPlugins'),
        default=[],
        )

    def getCredentialsPlugins():
        """Return iterable of (plugin name, actual credentials plugin) pairs.
        Looks up names in credentialsPlugins as contained ids of non-utility
        ICredentialsPlugins first, then as registered ICredentialsPlugin
        utilities.  Names that do not resolve are ignored."""

    def getAuthenticatorPlugins():
        """Return iterable of (plugin name, actual authenticator plugin) pairs.
        Looks up names in authenticatorPlugins as contained ids of non-utility
        IAuthenticatorPlugins first, then as registered IAuthenticatorPlugin
        utilities.  Names that do not resolve are ignored."""

    prefix = zope.schema.TextLine(
        title=_('Prefix'),
        default=u'',
        required=True,
        readonly=True,
        )

    def logout(request):
        """Performs a logout by delegating to its authenticator plugins."""


class ICredentialsPlugin(IPlugin):
    """Handles credentials extraction and challenges per request."""

    containers(IPluggableAuthentication)

    challengeProtocol = zope.interface.Attribute(
        """A challenge protocol used by the plugin.

        If a credentials plugin works with other credentials pluggins, it
        and the other cooperating plugins should specify a common (non-None)
        protocol. If a plugin returns True from its challenge method, then
        other credentials plugins will be called only if they have the same
        protocol.
        """)

    def extractCredentials(request):
        """Ties to extract credentials from a request.

        A return value of None indicates that no credentials could be found.
        Any other return value is treated as valid credentials.
        """

    def challenge(request):
        """Possibly issues a challenge.

        This is typically done in a protocol-specific way.

        If a challenge was issued, return True, otherwise return False.
        """

    def logout(request):
        """Possibly logout.

        If a logout was performed, return True, otherwise return False.
        """


class IAuthenticatorPlugin(IPlugin):
    """Authenticates a principal using credentials.

    An authenticator may also be responsible for providing information
    about and creating principals.
    """
    containers(IPluggableAuthentication)

    def authenticateCredentials(credentials):
        """Authenticates credentials.

        If the credentials can be authenticated, return an object that provides
        IPrincipalInfo. If the plugin cannot authenticate the credentials,
        returns None.
        """

    def principalInfo(id):
        """Returns an IPrincipalInfo object for the specified principal id.

        If the plugin cannot find information for the id, returns None.
        """


class IPrincipalInfo(zope.interface.Interface):
    """Minimal information about a principal."""

    id = zope.interface.Attribute("The principal id.")

    title = zope.interface.Attribute("The principal title.")

    description = zope.interface.Attribute("A description of the principal.")

    credentialsPlugin = zope.interface.Attribute(
        """Plugin used to generate the credentials for this principal info.

        Optional.  Should be set in IPluggableAuthentication.authenticate.
        """)

    authenticatorPlugin = zope.interface.Attribute(
        """Plugin used to authenticate the credentials for this principal info.

        Optional.  Should be set in IPluggableAuthentication.authenticate and
        IPluggableAuthentication.getPrincipal.
        """)
