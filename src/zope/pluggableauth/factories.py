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
"""Principals related factories
"""
__docformat__ = "reStructuredText"

from zope.authentication.interfaces import IAuthentication
from zope.event import notify
from zope.publisher.interfaces import IRequest
from zope.security.interfaces import IGroupClosureAwarePrincipal as IPrincipal

from zope import component
from zope import interface
from zope.pluggableauth import interfaces


@interface.implementer(interfaces.IPrincipalInfo)
class PrincipalInfo:
    """An implementation of IPrincipalInfo used by the principal folder.

    A principal info is created with id, login, title, and description:

      >>> info = PrincipalInfo('users.foo', 'foo', 'Foo', 'An over-used term.')
      >>> info
      PrincipalInfo('users.foo')
      >>> info.id
      'users.foo'
      >>> info.login
      'foo'
      >>> info.title
      'Foo'
      >>> info.description
      'An over-used term.'

    """

    def __init__(self, id, login, title, description):
        self.id = id
        self.login = login
        self.title = title
        self.description = description

    def __repr__(self):
        return 'PrincipalInfo(%r)' % self.id


@interface.implementer(IPrincipal)
class Principal:
    """A group-aware implementation of zope.security.interfaces.IPrincipal.

    A principal is created with an ID:

      >>> p = Principal(1)
      >>> p
      Principal(1)
      >>> p.id
      1

    title and description may also be provided:

      >>> p = Principal('george', 'George', 'A site member.')
      >>> p
      Principal('george')
      >>> p.id
      'george'
      >>> p.title
      'George'
      >>> p.description
      'A site member.'

    The `groups` is a simple list, filled in by plugins.

      >>> p.groups
      []

    The `allGroups` attribute is a readonly iterable of the full closure of the
    groups in the `groups` attribute--that is, if the principal is a direct
    member of the 'Administrators' group, and the 'Administrators' group is
    a member of the 'Reviewers' group, then p.groups would be
    ['Administrators'] and list(p.allGroups) would be
    ['Administrators', 'Reviewers'].

    To illustrate this, we'll need to set up a dummy authentication utility,
    and a few principals.  Our main principal will also gain some groups, as if
    plugins had added the groups to the list.  This is all setup--skip to the
    next block to actually see `allGroups` in action.

      >>> p.groups.extend(
      ...     ['content_administrators', 'zope_3_project',
      ...      'list_administrators', 'zpug'])
      >>> editor = Principal('editors', 'Content Editors')
      >>> creator = Principal('creators', 'Content Creators')
      >>> reviewer = Principal('reviewers', 'Content Reviewers')
      >>> reviewer.groups.extend(['editors', 'creators'])
      >>> usermanager = Principal('user_managers', 'User Managers')
      >>> contentAdmin = Principal(
      ...     'content_administrators', 'Content Administrators')
      >>> contentAdmin.groups.extend(['reviewers', 'user_managers'])
      >>> zope3Dev = Principal('zope_3_project', 'Zope 3 Developer')
      >>> zope3ListAdmin = Principal(
      ...     'zope_3_list_admin', 'Zope 3 List Administrators')
      >>> zope3ListAdmin.groups.append('zope_3_project') # duplicate, but
      ... # should only appear in allGroups once
      >>> listAdmin = Principal('list_administrators', 'List Administrators')
      >>> listAdmin.groups.append('zope_3_list_admin')
      >>> zpugMember = Principal('zpug', 'ZPUG Member')
      >>> martians = Principal('martians', 'Martians') # not in p's allGroups
      >>> group_data = dict((p.id, p) for p in (
      ...     editor, creator, reviewer, usermanager, contentAdmin,
      ...     zope3Dev, zope3ListAdmin, listAdmin, zpugMember, martians))
      >>> @interface.implementer(IAuthentication)
      ... class DemoAuth(object):
      ...     def getPrincipal(self, id):
      ...         return group_data[id]
      ...
      >>> demoAuth = DemoAuth()
      >>> component.provideUtility(demoAuth)

    Now, we have a user with the following groups (lowest level are p's direct
    groups, and lines show membership):

      editors  creators
         \\-----//
             ||                                    zope_3_project (duplicate)
          reviewers  user_managers                          ||
               \\--------//                          zope_3_list_admin
                    ||                                      ||
          content_administrators   zope_3_project   list_administrators   zpug

    The allGroups value includes all of the shown groups, and with
    'zope_3_project' only appearing once.

      >>> p.groups # doctest: +NORMALIZE_WHITESPACE
      ['content_administrators', 'zope_3_project', 'list_administrators',
       'zpug']
      >>> list(p.allGroups) # doctest: +NORMALIZE_WHITESPACE
      ['content_administrators', 'reviewers', 'editors', 'creators',
       'user_managers', 'zope_3_project', 'list_administrators',
       'zope_3_list_admin', 'zpug']
    """

    def __init__(self, id, title='', description=''):
        self.id = id
        self.title = title
        self.description = description
        self.groups = []

    def __repr__(self):
        return 'Principal(%r)' % self.id

    @property
    def allGroups(self):
        if self.groups:
            seen = set()
            principals = component.getUtility(IAuthentication)
            stack = [iter(self.groups)]
            while stack:
                try:
                    group_id = next(stack[-1])
                except StopIteration:
                    stack.pop()
                else:
                    if group_id not in seen:
                        yield group_id
                        seen.add(group_id)
                        group = principals.getPrincipal(group_id)
                        stack.append(iter(group.groups))


@component.adapter(interfaces.IPrincipalInfo, IRequest)
@interface.implementer(interfaces.IAuthenticatedPrincipalFactory)
class AuthenticatedPrincipalFactory:
    """Creates 'authenticated' principals.

    An authenticated principal is created as a result of an authentication
    operation.

    To use the factory, create it with the info (interfaces.IPrincipalInfo) of
    the principal to create and a request:

      >>> info = PrincipalInfo('users.mary', 'mary', 'Mary', 'The site admin.')
      >>> from zope.publisher.base import TestRequest
      >>> request = TestRequest('/')
      >>> factory = AuthenticatedPrincipalFactory(info, request)

    The factory must be called with a pluggable-authentication object:

      >>> class Auth:
      ...     prefix = 'auth.'
      >>> auth = Auth()

      >>> principal = factory(auth)

    The factory uses the pluggable authentication and the info to
    create a principal with the same ID, title, and description:

      >>> principal.id
      'auth.users.mary'
      >>> principal.title
      'Mary'
      >>> principal.description
      'The site admin.'

    It also fires an AuthenticatedPrincipalCreatedEvent:

      >>> from zope.component.eventtesting import getEvents
      >>> [event] = getEvents(interfaces.IAuthenticatedPrincipalCreated)
      >>> event.principal is principal, event.authentication is auth
      (True, True)
      >>> event.info
      PrincipalInfo('users.mary')
      >>> event.request is request
      True

    Listeners can subscribe to this event to perform additional operations
    when the authenticated principal is created.

    For information on how factories are used in the authentication process,
    see README.txt.
    """

    def __init__(self, info, request):
        self.info = info
        self.request = request

    def __call__(self, authentication):
        principal = Principal(authentication.prefix + self.info.id,
                              self.info.title,
                              self.info.description)
        notify(interfaces.AuthenticatedPrincipalCreated(
            authentication, principal, self.info, self.request))
        return principal


@component.adapter(interfaces.IPrincipalInfo)
@interface.implementer(interfaces.IFoundPrincipalFactory)
class FoundPrincipalFactory:
    """Creates 'found' principals.

    A 'found' principal is created as a result of a principal lookup.

    To use the factory, create it with the info (interfaces.IPrincipalInfo) of
    the principal to create:

      >>> info = PrincipalInfo('users.sam', 'sam', 'Sam', 'A site user.')
      >>> factory = FoundPrincipalFactory(info)

    The factory must be called with a pluggable-authentication object:

      >>> class Auth:
      ...     prefix = 'auth.'
      >>> auth = Auth()

      >>> principal = factory(auth)

    The factory uses the pluggable-authentication object and the info
    to create a principal with the same ID, title, and description:

      >>> principal.id
      'auth.users.sam'
      >>> principal.title
      'Sam'
      >>> principal.description
      'A site user.'

    It also fires a FoundPrincipalCreatedEvent:

      >>> from zope.component.eventtesting import getEvents
      >>> [event] = getEvents(interfaces.IFoundPrincipalCreated)
      >>> event.principal is principal, event.authentication is auth
      (True, True)
      >>> event.info
      PrincipalInfo('users.sam')

    Listeners can subscribe to this event to perform additional operations
    when the 'found' principal is created.

    For information on how factories are used in the authentication process,
    see README.txt.
    """

    def __init__(self, info):
        self.info = info

    def __call__(self, authentication):
        principal = Principal(authentication.prefix + self.info.id,
                              self.info.title,
                              self.info.description)
        notify(interfaces.FoundPrincipalCreated(authentication,
                                                principal, self.info))
        return principal
