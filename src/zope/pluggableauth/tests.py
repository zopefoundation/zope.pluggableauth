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
"""Pluggable Authentication Service Tests

$Id$
"""
__docformat__ = "reStructuredText"

import doctest, unittest

from zope.app.testing import placelesssetup
from zope.app.testing.setup import placefulSetUp, placefulTearDown
from zope.component import provideUtility, provideAdapter, provideHandler
from zope.component.eventtesting import getEvents, clearEvents
from zope.interface import implements
from zope.pluggableauth.plugins.session import SessionCredentialsPlugin
from zope.publisher import base
from zope.publisher.interfaces import IRequest
from zope.session.http import CookieClientIdManager
from zope.session.interfaces import (
    IClientId, IClientIdManager, ISession, ISessionDataContainer)
from zope.session.session import (
    ClientId, Session, PersistentSessionDataContainer)


class TestClientId(object):
    implements(IClientId)
    def __new__(cls, request):
        return 'dummyclientidfortesting'


def siteSetUp(test):
    placefulSetUp(site=True)


def siteTearDown(test):
    placefulTearDown()


def sessionSetUp(session_data_container_class=PersistentSessionDataContainer):
    placelesssetup.setUp()
    provideAdapter(TestClientId, [IRequest], IClientId)
    provideAdapter(Session, [IRequest], ISession)
    provideUtility(CookieClientIdManager(), IClientIdManager)
    sdc = session_data_container_class()
    provideUtility(sdc, ISessionDataContainer, '')


def nonHTTPSessionTestCaseSetUp(sdc_class=PersistentSessionDataContainer):
    # I am getting an error with ClientId and not TestClientId
    placelesssetup.setUp()
    provideAdapter(ClientId, [IRequest], IClientId)
    provideAdapter(Session, [IRequest], ISession)
    provideUtility(CookieClientIdManager(), IClientIdManager)
    sdc = sdc_class()
    provideUtility(sdc, ISessionDataContainer, '')


class NonHTTPSessionTestCase(unittest.TestCase):
    # Small test suite to catch an error with non HTTP protocols, like FTP
    # and SessionCredentialsPlugin.
    def setUp(self):
        nonHTTPSessionTestCaseSetUp()

    def tearDown(self):
        placefulTearDown()

    def test_exeractCredentials(self):
        plugin = SessionCredentialsPlugin()

        self.assertEqual(plugin.extractCredentials(base.TestRequest('/')), None)

    def test_challenge(self):
        plugin = SessionCredentialsPlugin()

        self.assertEqual(plugin.challenge(base.TestRequest('/')), False)

    def test_logout(self):
        plugin = SessionCredentialsPlugin()

        self.assertEqual(plugin.logout(base.TestRequest('/')), False)


def test_suite():
    suite = unittest.TestSuite((
        unittest.makeSuite(NonHTTPSessionTestCase),
        doctest.DocTestSuite('zope.pluggableauth.interfaces'),
        doctest.DocTestSuite('zope.pluggableauth.plugins.generic'),
        doctest.DocTestSuite('zope.pluggableauth.plugins.ftpplugins'),
        doctest.DocTestSuite('zope.pluggableauth.plugins.httpplugins'),
        doctest.DocTestSuite('zope.pluggableauth.plugins.session',
                             setUp=siteSetUp,
                             tearDown=siteTearDown),
        doctest.DocFileSuite('README.txt',
                             setUp=siteSetUp,
                             tearDown=siteTearDown,
                             globs={'provideUtility': provideUtility,
                                    'provideAdapter': provideAdapter,
                                    'provideHandler': provideHandler,
                                    'getEvents': getEvents,
                                    'clearEvents': clearEvents,
                                    })))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
