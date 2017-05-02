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
"""Pluggable Authentication Service Tests
"""
__docformat__ = "reStructuredText"

import doctest
import re
import unittest
import zope.component
from zope.component.interfaces import IComponentLookup
from zope.container.interfaces import ISimpleReadContainer
from zope.container.traversal import ContainerTraversable
from zope.interface import implementer
from zope.interface import Interface
from zope.pluggableauth.plugins.session import SessionCredentialsPlugin
from zope.publisher import base
from zope.publisher.interfaces import IRequest
from zope.session.http import CookieClientIdManager
from zope.site.folder import rootFolder
from zope.site.site import LocalSiteManager, SiteManagerAdapter
from zope.testing import renormalizing
from zope.traversing.interfaces import ITraversable
from zope.traversing.testing import setUp
import zope.component.eventtesting
import zope.password
from zope.session.interfaces import (
    IClientId, IClientIdManager, ISession, ISessionDataContainer)
from zope.session.session import (
    ClientId, Session, PersistentSessionDataContainer)
import zope.component.testing

checker = renormalizing.RENormalizing([
    # Python 3 unicode removed the "u".
    (re.compile("u('.*?')"), r"\1"),
    (re.compile('u(".*?")'), r"\1"),
])

@implementer(IClientId)
class TestClientId(object):

    def __new__(cls, request):
        return 'dummyclientidfortesting'


def siteSetUp(test):
    zope.component.hooks.setHooks()

    # Set up site manager adapter
    zope.component.provideAdapter(
        SiteManagerAdapter, (Interface,), IComponentLookup)

    # Set up traversal
    setUp()
    zope.component.provideAdapter(
        ContainerTraversable, (ISimpleReadContainer,), ITraversable)

    # Set up site
    site = rootFolder()
    site.setSiteManager(LocalSiteManager(site))
    zope.component.hooks.setSite(site)

    return site


def siteTearDown(test):
    zope.component.hooks.resetHooks()
    zope.component.hooks.setSite()


def sessionSetUp(container=PersistentSessionDataContainer):
    zope.component.provideAdapter(TestClientId, [IRequest], IClientId)
    zope.component.provideAdapter(Session, [IRequest], ISession)
    zope.component.provideUtility(CookieClientIdManager(), IClientIdManager)
    zope.component.provideUtility(container(), ISessionDataContainer, '')


def nonHTTPSessionTestCaseSetUp(container=PersistentSessionDataContainer):
    # I am getting an error with ClientId and not TestClientId
    zope.component.provideAdapter(ClientId, [IRequest], IClientId)
    zope.component.provideAdapter(Session, [IRequest], ISession)
    zope.component.provideUtility(CookieClientIdManager(), IClientIdManager)
    zope.component.provideUtility(container(), ISessionDataContainer, '')


class NonHTTPSessionTestCase(unittest.TestCase):
    """Small test suite to catch an error with non HTTP protocols,
    like FTP and SessionCredentialsPlugin.
    """

    def setUp(self):
        nonHTTPSessionTestCaseSetUp()

    def tearDown(self):
        zope.component.hooks.resetHooks()
        zope.component.hooks.setSite()

    def test_exeractCredentials(self):
        plugin = SessionCredentialsPlugin()
        self.assertEqual(
            plugin.extractCredentials(base.TestRequest('/')), None)

    def test_challenge(self):
        plugin = SessionCredentialsPlugin()
        self.assertEqual(
            plugin.challenge(base.TestRequest('/')), False)

    def test_logout(self):
        plugin = SessionCredentialsPlugin()
        self.assertEqual(
            plugin.logout(base.TestRequest('/')), False)

def setupPassword(test):
    from zope.password.interfaces import IPasswordManager
    from zope.password.password import SHA1PasswordManager, SSHAPasswordManager
    zope.component.provideUtility(
        SHA1PasswordManager(), IPasswordManager, 'SHA1')
    zope.component.provideUtility(
        SSHAPasswordManager(), IPasswordManager, 'SSHA')

def test_suite():
    flags = (doctest.ELLIPSIS
             |doctest.NORMALIZE_WHITESPACE
             | renormalizing.IGNORE_EXCEPTION_MODULE_IN_PYTHON2)

    def module_test(modname, **kwargs):
        return doctest.DocTestSuite(
            'zope.pluggableauth.' + modname,
            optionflags=flags,
            checker=checker,
            **kwargs)

    def file_test(filename, **kwargs):
        return doctest.DocFileSuite(
            filename + '.rst',
            optionflags=flags,
            checker=checker,
            **kwargs)

    module_tests = [module_test('plugins.' + m) for m in
                           ('generic', 'ftpplugins',
                            'httpplugins', 'idpicker',
                            'principalfolder',
                            'groupfolder',)]

    module_tests.append(module_test('plugins.session',
                                    setUp=siteSetUp,
                                    tearDown=siteTearDown))

    module_tests.extend([module_test(m,
                                     setUp=zope.component.eventtesting.setUp,
                                     tearDown=zope.component.testing.tearDown)
                         for m in
                         ('authentication',
                          'factories',
                          'interfaces',)])

    file_tests = [file_test(f, setUp=setup) for f, setup
                  in (('plugins/principalfolder', setupPassword),
                      ('plugins/groupfolder', zope.component.eventtesting.setUp))]

    file_tests.append(file_test("README",
                                setUp=siteSetUp,
                                tearDown=siteTearDown,
                                globs={'provideUtility': zope.component.provideUtility,
                                       'provideAdapter': zope.component.provideAdapter,
                                       'provideHandler': zope.component.provideHandler,
                                       'getEvents': zope.component.eventtesting.getEvents,
                                       'clearEvents': zope.component.eventtesting.clearEvents,
                                }))

    alltests = [unittest.defaultTestLoader.loadTestsFromName(__name__)]
    alltests.extend(module_tests)
    alltests.extend(file_tests)
    suite = unittest.TestSuite(alltests)
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
