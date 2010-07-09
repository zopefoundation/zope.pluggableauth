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

##############################################################################
# This package is developed by the Zope Toolkit project, documented here:
# http://docs.zope.org/zopetoolkit
# When developing and releasing this package, please follow the documented
# Zope Toolkit policies as described by this documentation.
##############################################################################
"""Pluggable Authentication Utility
"""

import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(name='zope.pluggableauth',
      version = '1.0.3',
      author='Zope Foundation and Contributors',
      author_email='zope-dev@zope.org',
      description='Pluggable Authentication Utility',
      long_description= "%s\n\n%s\n\n%s" % (
        read('README.txt'), 
        read('src', 'zope', 'pluggableauth', 'README.txt'),
        read('CHANGES.txt')),
      url='http://pypi.python.org/pypi/zope.pluggableauth',
      license='ZPL 2.1',
      keywords='zope3 ztk authentication pluggable',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['zope'],
      include_package_data = True,
      zip_safe = False,
      extras_require=dict(test=['zope.component[test]']),
      install_requires=[
          'ZODB3',
          'setuptools',
          'zope.authentication',
          'zope.component',
          'zope.container',
          'zope.event',
          'zope.i18nmessageid',
          'zope.interface',
          'zope.publisher>=3.12',
          'zope.schema',
          'zope.security',
          'zope.session',
          'zope.site',
          'zope.traversing'],
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
      )
