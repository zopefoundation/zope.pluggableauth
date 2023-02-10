# ##############################################################################
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
"""Helper base class that picks principal ids

"""
__docformat__ = 'restructuredtext'

import re

from zope.container.contained import NameChooser
from zope.exceptions.interfaces import UserError
from zope.i18nmessageid import MessageFactory


try:
    text_type = unicode
except NameError:  # py3
    text_type = str

_ = MessageFactory('zope')

ok = re.compile('[!-~]+$').match


class IdPicker(NameChooser):
    """Helper base class that picks principal ids.

    Add numbers to ids given by users to make them unique.

    The Id picker is a variation on the name chooser that picks numeric
    ids when no name is given.

      >>> from zope.pluggableauth.plugins.idpicker import IdPicker
      >>> IdPicker({}).chooseName('', None)
      '1'

      >>> IdPicker({'1': 1}).chooseName('', None)
      '2'

      >>> IdPicker({'2': 1}).chooseName('', None)
      '1'

      >>> IdPicker({'1': 1}).chooseName('bob', None)
      'bob'

      >>> IdPicker({'bob': 1}).chooseName('bob', None)
      'bob1'

    """

    def chooseName(self, name, object):
        i = 0
        name = text_type(name)
        orig = name
        while (not name) or (name in self.context):
            i += 1
            name = orig + str(i)

        self.checkName(name, object)
        return name

    def checkName(self, name, object):
        """Limit ids

        Ids can only contain printable, non-space, 7-bit ASCII strings:

        >>> from zope.pluggableauth.plugins.idpicker import IdPicker
        >>> IdPicker({}).checkName('1', None)
        True

        >>> IdPicker({}).checkName('bob', None)
        True

        >>> try:
        ...     IdPicker({}).checkName('bob\xfa', None)
        ... except UserError as e:
        ...     print(e)
        ...     # doctest: +NORMALIZE_WHITESPACE
        Ids must contain only printable 7-bit non-space ASCII characters

        >>> try:
        ...     IdPicker({}).checkName('big bob', None)
        ... except UserError as e:
        ...     print(e)
        ...     # doctest: +NORMALIZE_WHITESPACE
        Ids must contain only printable 7-bit non-space ASCII characters

        Ids also can't be over 100 characters long:

        >>> IdPicker({}).checkName('x' * 100, None)
        True

        >>> IdPicker({}).checkName('x' * 101, None)
        Traceback (most recent call last):
        ...
        zope.exceptions.interfaces.UserError: Ids can't be more than 100 characters long.

        """  # noqa: E501 line too long
        NameChooser.checkName(self, name, object)
        if not ok(name):
            raise UserError(
                _("Ids must contain only printable 7-bit non-space"
                  " ASCII characters")
            )
        if len(name) > 100:
            raise UserError(
                _("Ids can't be more than 100 characters long.")
            )
        return True
