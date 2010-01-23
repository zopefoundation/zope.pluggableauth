##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
# This package is developed by the Zope Toolkit project, documented here:
# http://docs.zope.org/zopetoolkit
# When developing and releasing this package, please follow the documented
# Zope Toolkit policies as described by this documentation.
##############################################################################
"""Setup for zope.app.authentication package

$Id$
"""
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(name='zope.app.authentication',
      version = '3.6.3dev',
      author='Zope Corporation and Contributors',
      author_email='zope-dev@zope.org',
      description='Pluggable Authentication Utility',
      long_description=(
        read('README.txt')
        + '\n\n' +
        'Detailed Documentation\n' +
        '----------------------\n'
        + '\n' +
        read('src', 'zope', 'app', 'authentication', 'README.txt')
        + '\n\n' +
        read('src', 'zope', 'app', 'authentication', 'principalfolder.txt')
        + '\n\n' +
        read('src', 'zope', 'app', 'authentication', 'vocabulary.txt')
        + '\n\n' +
        read('CHANGES.txt')
        ),
      url='http://pypi.python.org/pypi/zope.app.authentication',
      license='ZPL 2.1',
      classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Zope Public License',
          'Programming Language :: Python',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Topic :: Internet :: WWW/HTTP',
          'Framework :: Zope3'],
      keywords='zope3 authentication pluggable principal group',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      extras_require=dict(test=['zope.app.testing',
                                'zope.app.securitypolicy',
                                'zope.app.zcmlfiles',
                                'zope.securitypolicy',
                                'zope.testbrowser',
                                'zope.login',]),
      namespace_packages=['zope', 'zope.app'],
      install_requires=['setuptools',
                        'zope.app.component',
                        'zope.app.container',
                        'zope.app.form',
                        'zope.authentication',
                        'zope.dublincore',
                        'zope.event',
                        'zope.exceptions',
                        'zope.i18n',
                        'zope.i18nmessageid',
                        'zope.interface',
                        'zope.location',
                        'zope.password>=3.5.1',
                        'zope.publisher>=3.12',
                        'zope.schema',
                        'zope.security',
                        'zope.session',
                        'zope.site',
                        'zope.traversing',
                        'ZODB3',
                        ],
      include_package_data = True,
      zip_safe = False,
      )
