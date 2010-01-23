##############################################################################
# This package is developed by the Zope Toolkit project, documented here:
# http://docs.zope.org/zopetoolkit
# When developing and releasing this package, please follow the documented
# Zope Toolkit policies as described by this documentation.
##############################################################################

import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(name='zope.pluggableauth',
      version = '1.0dev',
      author='Zope Corporation and Contributors',
      author_email='zope-dev@zope.org',
      description='Pluggable Authentication Utility',
      long_description=(
        read('README.txt')
        + '\n\n' +
        'Detailed Documentation\n' +
        '----------------------\n'
        + '\n' +
        read('src', 'zope', 'pluggableauth', 'README.txt')
        + '\n\n' +
        read('CHANGES.txt')
        ),
      url='http://pypi.python.org/pypi/zope.pluggableauth',
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
      keywords='zope3 ztk authentication pluggable',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      extras_require=dict(test=['zope.app.testing',
                                'zope.app.securitypolicy',
                                'zope.securitypolicy',
                                'zope.login',]),
      namespace_packages=['zope'],
      install_requires=['setuptools',
                        'zope.component',
                        'zope.container',
                        'zope.authentication',
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
