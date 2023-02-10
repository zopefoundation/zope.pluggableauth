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
"""ZODB-based Authentication Source

$Id$
"""
__docformat__ = "reStructuredText"

from persistent import Persistent
from zope.component import getUtility
from zope.container.btree import BTreeContainer
from zope.container.constraints import containers
from zope.container.constraints import contains
from zope.container.contained import Contained
from zope.container.interfaces import DuplicateIDError
from zope.i18nmessageid import MessageFactory
from zope.interface import Interface
from zope.interface import implementer
from zope.password.interfaces import IPasswordManager
from zope.schema import Choice
from zope.schema import Password
from zope.schema import Text
from zope.schema import TextLine

from zope.pluggableauth.factories import PrincipalInfo
from zope.pluggableauth.interfaces import IAuthenticatorPlugin
from zope.pluggableauth.interfaces import IQuerySchemaSearch


_ = MessageFactory('zope')


class IInternalPrincipal(Interface):
    """Principal information"""

    login = TextLine(
        title=_("Login"),
        description=_("The Login/Username of the principal. "
                      "This value can change."))

    def setPassword(password, passwordManagerName=None):
        pass

    password = Password(
        title=_("Password"),
        description=_("The password for the principal."))

    passwordManagerName = Choice(
        title=_("Password Manager"),
        vocabulary="Password Manager Names",
        description=_("The password manager will be used"
                      " for encode/check the password"),
        default="SSHA",
        # TODO: The password manager name may be changed only
        # if the password changed
        readonly=True
    )

    title = TextLine(
        title=_("Title"),
        description=_("Provides a title for the principal."))

    description = Text(
        title=_("Description"),
        description=_("Provides a description for the principal."),
        required=False,
        missing_value='',
        default='')


class IInternalPrincipalContainer(Interface):
    """A container that contains internal principals."""

    prefix = TextLine(
        title=_("Prefix"),
        description=_(
            "Prefix to be added to all principal ids to assure "
            "that all ids are unique within the authentication service"),
        missing_value="",
        default='',
        readonly=True)

    def getIdByLogin(login):
        """Return the principal id currently associated with login.

        The return value includes the container prefix, but does not
        include the PAU prefix.

        KeyError is raised if no principal is associated with login.

        """

    contains(IInternalPrincipal)


class IInternalPrincipalContained(Interface):
    """Principal information"""

    containers(IInternalPrincipalContainer)


class ISearchSchema(Interface):
    """Search Interface for this Principal Provider"""

    search = TextLine(
        title=_("Search String"),
        description=_("A Search String"),
        required=False,
        default='',
        missing_value='')


@implementer(IInternalPrincipal, IInternalPrincipalContained)
class InternalPrincipal(Persistent, Contained):
    """An internal principal for Persistent Principal Folder."""

    # If you're searching for self._passwordManagerName, or self._password
    # probably you just need to evolve the database to new generation
    # at /++etc++process/@@generations.html

    # NOTE: All changes needs to be synchronized with the evolver at
    # zope.app.zopeappgenerations.evolve2

    def __init__(self, login, password, title, description='',
                 passwordManagerName="SSHA"):
        self._login = login
        self._passwordManagerName = passwordManagerName
        self.password = password
        self.title = title
        self.description = description

    def getPasswordManagerName(self):
        return self._passwordManagerName

    passwordManagerName = property(getPasswordManagerName)

    def _getPasswordManager(self):
        return getUtility(IPasswordManager, self.passwordManagerName)

    def getPassword(self):
        return self._password

    def setPassword(self, password, passwordManagerName=None):
        if passwordManagerName is not None:
            self._passwordManagerName = passwordManagerName
        passwordManager = self._getPasswordManager()
        self._password = passwordManager.encodePassword(password)

    password = property(getPassword, setPassword)

    def checkPassword(self, password):
        passwordManager = self._getPasswordManager()
        return passwordManager.checkPassword(self.password, password)

    def getLogin(self):
        return self._login

    def setLogin(self, login):
        oldLogin = self._login
        self._login = login
        if self.__parent__ is not None:
            try:
                self.__parent__.notifyLoginChanged(oldLogin, self)
            except ValueError:
                self._login = oldLogin
                raise

    login = property(getLogin, setLogin)


@implementer(IAuthenticatorPlugin,
             IQuerySchemaSearch,
             IInternalPrincipalContainer)
class PrincipalFolder(BTreeContainer):
    """A Persistent Principal Folder and Authentication plugin.

    See principalfolder.txt for details.
    """

    schema = ISearchSchema

    def __init__(self, prefix=''):
        self.prefix = prefix
        super().__init__()
        self.__id_by_login = self._newContainerData()

    def notifyLoginChanged(self, oldLogin, principal):
        """Notify the Container about changed login of a principal.

        We need this, so that our second tree can be kept up-to-date.
        """
        # A user with the new login already exists
        if principal.login in self.__id_by_login:
            raise ValueError('Principal Login already taken!')

        del self.__id_by_login[oldLogin]
        self.__id_by_login[principal.login] = principal.__name__

    def __setitem__(self, id, principal):
        """Add principal information.

        Create a Principal Folder

            >>> pf = PrincipalFolder()

        Create a principal with 1 as id
        Add a login attr since __setitem__ is in need of one

            >>> from zope.pluggableauth.factories import Principal
            >>> principal = Principal(1)
            >>> principal.login = 1

        Add the principal within the Principal Folder

            >>> pf.__setitem__(u'1', principal)

        Try to add another principal with the same id.
        It should raise a DuplicateIDError

            >>> try:
            ...     pf.__setitem__(u'1', principal)
            ... except DuplicateIDError:
            ...     pass
            >>>
        """
        # A user with the new login already exists
        if principal.login in self.__id_by_login:
            raise DuplicateIDError('Principal Login already taken!')

        super().__setitem__(id, principal)
        self.__id_by_login[principal.login] = id

    def __delitem__(self, id):
        """Remove principal information."""
        principal = self[id]
        super().__delitem__(id)
        del self.__id_by_login[principal.login]

    def authenticateCredentials(self, credentials):
        """Return principal info if credentials can be authenticated
        """
        if not isinstance(credentials, dict):
            return None
        if not ('login' in credentials and 'password' in credentials):
            return None
        id = self.__id_by_login.get(credentials['login'])
        if id is None:
            return None
        internal = self[id]
        if not internal.checkPassword(credentials["password"]):
            return None
        return PrincipalInfo(self.prefix + id, internal.login, internal.title,
                             internal.description)

    def principalInfo(self, id):
        if id.startswith(self.prefix):
            internal = self.get(id[len(self.prefix):])
            if internal is not None:
                return PrincipalInfo(id, internal.login, internal.title,
                                     internal.description)

    def getIdByLogin(self, login):
        return self.prefix + self.__id_by_login[login]

    def search(self, query, start=None, batch_size=None):
        """Search through this principal provider."""
        search = query.get('search')
        if search is None:
            return
        search = search.lower()
        n = 1
        for i, value in enumerate(self.values()):
            if (search in value.title.lower() or
                search in value.description.lower() or
                    search in value.login.lower()):
                if not ((start is not None and i < start)
                        or (batch_size is not None and n > batch_size)):
                    n += 1
                    yield self.prefix + value.__name__
