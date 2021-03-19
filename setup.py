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
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()

tests_require = [
    'zope.testing',
    'zope.testrunner',
]

setup(
    name='zope.pluggableauth',
    version='2.3.1',
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.org',
    description='Pluggable Authentication Utility',
    long_description="\n\n".join((
        read('README.rst'),
        read('src', 'zope', 'pluggableauth', 'README.rst'),
        read('src', 'zope', 'pluggableauth', 'plugins', 'principalfolder.rst'),
        read('src', 'zope', 'pluggableauth', 'plugins', 'groupfolder.rst'),
        read('CHANGES.rst'),
    )),
    url='http://pypi.python.org/pypi/zope.pluggableauth',
    license='ZPL 2.1',
    keywords='zope3 ztk authentication pluggable',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Framework :: Zope :: 3'
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['zope'],
    extras_require={
        'test': tests_require,
    },
    install_requires=[
        'persistent',
        'setuptools',
        'transaction',
        'zope.authentication',
        'zope.component',
        'zope.container',
        'zope.event',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.password >= 3.5.1',
        'zope.publisher>=3.12',
        'zope.schema',
        'zope.security',
        'zope.session',
        'zope.site',
        'zope.traversing',
    ],
    tests_require=tests_require,
    test_suite='zope.pluggableauth.tests.test_suite',
    include_package_data=True,
    zip_safe=False,
)
