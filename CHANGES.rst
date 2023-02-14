=========
 Changes
=========

3.0 (2023-02-14)
================

- Add support for Python 3.8, 3.9, 3.10, 3.11.

- Drop support for Python 2.7, 3.5, 3.6.

- Drop support for deprecated ``python setup.py test``.


2.3.1 (2021-03-19)
==================

- Drop support for Python 3.4.

- Add support for Python 3.7.

- Import from zope.interface.interfaces to avoid deprecation warning.


2.3.0 (2017-11-12)
==================

- Drop support for Python 3.3.


2.2.0 (2017-05-02)
==================

- Add support for Python 3.6.

- Fix a NameError in the idpicker under Python 3.6.
  See `issue 7 <https://github.com/zopefoundation/zope.pluggableauth/issues/7>`_.

2.1.0 (2016-07-04)
==================

- Add support for Python 3.5.

- Drop support for Python 2.6.


2.0.0 (2014-12-24)
==================

- Add support for Python 3.4.

- Refactor ``zope.pluggableauth.plugins.session.redirectWithComeFrom``
  into a reusable function.

- Fix: allow password containing colon(s) in HTTP basic authentication
  credentials extraction plug-in, to conform with RFC2617


2.0.0a1 (2013-02-21)
====================

- Add ``tox.ini`` and ``MANIFEST.in``.

- Add support for Python 3.3.

- Replace deprecated ``zope.component.adapts`` usage with equivalent
  ``zope.component.adapter`` decorator.

- Replace deprecated ``zope.interface.implements`` usage with equivalent
  ``zope.interface.implementer`` decorator.

- Drop support for Python 2.4 and 2.5.


1.3 (2011-02-08)
================

- As the ``camefrom`` information is most probably used for a redirect,
  require it to be an absolute URL (see also
  http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.30).

1.2 (2010-12-16)
================

- Add a hook to ``SessionCredentialsPlugin`` (``_makeCredentials``) that can
  be overriden in subclasses to store the credentials in the session
  differently.

  For example, you could use ``keas.kmi`` and encrypt the passwords of the
  currently logged-in users so they don't appear in plain text in the ZODB.

1.1 (2010-10-18)
================

- Move concrete ``IAuthenticatorPlugin`` implementations from
  ``zope.app.authentication`` to ``zope.pluggableauth.plugins``.

  As a result, projects that want to use the ``IAuthenticator`` plugins
  (previously found in ``zope.app.authentication``) do not automatically
  also pull in the ``zope.app.*`` dependencies that are needed to register
  the ZMI views.

1.0.3 (2010-07-09)
==================

- Fix dependency declaration.

1.0.2 (2010-07-90)
==================

- Add ``persistent.Persistent`` and ``zope.container.contained.Contained`` as
  bases for ``zope.pluggableauth.plugins.session.SessionCredentialsPlugin``,
  so instances of ``zope.app.authentication.session.SessionCredentialsPlugin``
  won't be changed.
  (https://mail.zope.org/pipermail/zope-dev/2010-July/040898.html)

1.0.1 (2010-02-11)
==================

* Declare adapter in a new ZCML file : `principalfactories.zcml`.  Avoids
  duplication errors in ``zope.app.authentication``.

1.0 (2010-02-05)
================

* Splitting off from zope.app.authentication
