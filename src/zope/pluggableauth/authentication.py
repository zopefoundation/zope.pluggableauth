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
"""Pluggable Authentication Utility implementation
"""
from zope.authentication.interfaces import IAuthentication
from zope.authentication.interfaces import PrincipalLookupError
from zope.component import queryNextUtility
from zope.container.btree import BTreeContainer
from zope.interface import implementer
from zope.schema.interfaces import ISourceQueriables

from zope import component
from zope.pluggableauth import interfaces


@implementer(
    IAuthentication,
    interfaces.IPluggableAuthentication,
    ISourceQueriables)
class PluggableAuthentication(BTreeContainer):

    authenticatorPlugins = ()
    credentialsPlugins = ()

    def __init__(self, prefix=''):
        super().__init__()
        self.prefix = prefix

    def _plugins(self, names, interface):
        for name in names:
            plugin = self.get(name)
            if not interface.providedBy(plugin):
                plugin = component.queryUtility(interface, name, context=self)
            if plugin is not None:
                yield name, plugin

    def getAuthenticatorPlugins(self):
        return self._plugins(
            self.authenticatorPlugins, interfaces.IAuthenticatorPlugin)

    def getCredentialsPlugins(self):
        return self._plugins(
            self.credentialsPlugins, interfaces.ICredentialsPlugin)

    def authenticate(self, request):
        authenticatorPlugins = [p for n, p in self.getAuthenticatorPlugins()]
        for name, credplugin in self.getCredentialsPlugins():
            credentials = credplugin.extractCredentials(request)
            for authplugin in authenticatorPlugins:
                if authplugin is None:
                    continue
                info = authplugin.authenticateCredentials(credentials)
                if info is None:
                    continue
                info.credentialsPlugin = credplugin
                info.authenticatorPlugin = authplugin
                principal = component.getMultiAdapter(
                    (info, request),
                    interfaces.IAuthenticatedPrincipalFactory)(self)
                principal.id = self.prefix + info.id
                return principal
        return None

    def getPrincipal(self, id):
        if not id.startswith(self.prefix):
            next = queryNextUtility(self, IAuthentication)
            if next is None:
                raise PrincipalLookupError(id)
            return next.getPrincipal(id)
        id = id[len(self.prefix):]
        for name, authplugin in self.getAuthenticatorPlugins():
            info = authplugin.principalInfo(id)
            if info is None:
                continue
            info.credentialsPlugin = None
            info.authenticatorPlugin = authplugin
            principal = interfaces.IFoundPrincipalFactory(info)(self)
            principal.id = self.prefix + info.id
            return principal
        next = queryNextUtility(self, IAuthentication)
        if next is not None:
            return next.getPrincipal(self.prefix + id)
        raise PrincipalLookupError(id)

    def getQueriables(self):
        for name, authplugin in self.getAuthenticatorPlugins():
            queriable = component.queryMultiAdapter(
                (authplugin, self), interfaces.IQueriableAuthenticator)
            if queriable is not None:
                yield name, queriable

    def unauthenticatedPrincipal(self):
        return None

    def unauthorized(self, id, request):
        challengeProtocol = None

        for name, credplugin in self.getCredentialsPlugins():
            protocol = getattr(credplugin, 'challengeProtocol', None)
            if challengeProtocol is None or protocol == challengeProtocol:
                if credplugin.challenge(request):
                    if protocol is None:
                        return
                    elif challengeProtocol is None:
                        challengeProtocol = protocol

        if challengeProtocol is None:
            next = queryNextUtility(self, IAuthentication)
            if next is not None:
                next.unauthorized(id, request)

    def logout(self, request):
        challengeProtocol = None

        for name, credplugin in self.getCredentialsPlugins():
            protocol = getattr(credplugin, 'challengeProtocol', None)
            if challengeProtocol is None or protocol == challengeProtocol:
                if credplugin.logout(request):
                    if protocol is None:
                        return
                    elif challengeProtocol is None:
                        challengeProtocol = protocol

        if challengeProtocol is None:
            next = queryNextUtility(self, IAuthentication)
            if next is not None:
                next.logout(request)
