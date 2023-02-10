==================
 Principal Folder
==================

Principal folders contain principal-information objects that contain principal
information. We create an internal principal using the `InternalPrincipal`
class:

  >>> from zope.pluggableauth.plugins.principalfolder import InternalPrincipal
  >>> p1 = InternalPrincipal('login1', '123', "Principal 1",
  ...     passwordManagerName="SHA1")
  >>> p2 = InternalPrincipal('login2', '456', "The Other One")

and add them to a principal folder:

  >>> from zope.pluggableauth.plugins.principalfolder import PrincipalFolder
  >>> principals = PrincipalFolder('principal.')
  >>> principals['p1'] = p1
  >>> principals['p2'] = p2

Authentication
==============

Principal folders provide the `IAuthenticatorPlugin` interface. When we
provide suitable credentials:

  >>> from pprint import pprint
  >>> principals.authenticateCredentials({'login': 'login1', 'password': '123'})
  PrincipalInfo('principal.p1')

We get back a principal id and supplementary information, including the
principal title and description.  Note that the principal id is a concatenation
of the principal-folder prefix and the name of the principal-information object
within the folder.

None is returned if the credentials are invalid:

  >>> principals.authenticateCredentials({'login': 'login1',
  ...                                     'password': '1234'})
  >>> principals.authenticateCredentials(42)

Search
======

Principal folders also provide the IQuerySchemaSearch interface.  This
supports both finding principal information based on their ids:

  >>> principals.principalInfo('principal.p1')
  PrincipalInfo('principal.p1')

  >>> principals.principalInfo('p1')

and searching for principals based on a search string:

  >>> list(principals.search({'search': 'other'}))
  ['principal.p2']

  >>> list(principals.search({'search': 'OTHER'}))
  ['principal.p2']

  >>> list(principals.search({'search': ''}))
  ['principal.p1', 'principal.p2']

  >>> list(principals.search({'search': 'eek'}))
  []

  >>> list(principals.search({}))
  []

If there are a large number of matches:

  >>> for i in range(20):
  ...     i = str(i)
  ...     p = InternalPrincipal('l'+i, i, "Dude "+i)
  ...     principals[i] = p

  >>> pprint(list(principals.search({'search': 'D'})), width=25)
  ['principal.0',
   'principal.1',
   'principal.10',
   'principal.11',
   'principal.12',
   'principal.13',
   'principal.14',
   'principal.15',
   'principal.16',
   'principal.17',
   'principal.18',
   'principal.19',
   'principal.2',
   'principal.3',
   'principal.4',
   'principal.5',
   'principal.6',
   'principal.7',
   'principal.8',
   'principal.9']

We can use batching parameters to specify a subset of results:

  >>> pprint(list(principals.search({'search': 'D'}, start=17)))
  ['principal.7', 'principal.8', 'principal.9']

  >>> pprint(list(principals.search({'search': 'D'}, batch_size=5)), width=60)
  ['principal.0',
   'principal.1',
   'principal.10',
   'principal.11',
   'principal.12']

  >>> pprint(list(principals.search({'search': 'D'}, start=5, batch_size=5)),
  ...        width=25)
  ['principal.13',
   'principal.14',
   'principal.15',
   'principal.16',
   'principal.17']

There is an additional method that allows requesting the principal id
associated with a login id.  The method raises KeyError when there is
no associated principal:

  >>> principals.getIdByLogin("not-there")
  Traceback (most recent call last):
  KeyError: 'not-there'

If there is a matching principal, the id is returned:

  >>> principals.getIdByLogin("login1")
  'principal.p1'

Changing credentials
====================

Credentials can be changed by modifying principal-information objects:

  >>> p1.login = 'bob'
  >>> p1.password = 'eek'

  >>> principals.authenticateCredentials({'login': 'bob', 'password': 'eek'})
  PrincipalInfo('principal.p1')

  >>> principals.authenticateCredentials({'login': 'login1',
  ...                                     'password': 'eek'})

  >>> principals.authenticateCredentials({'login': 'bob',
  ...                                     'password': '123'})


It is an error to try to pick a login name that is already taken:

  >>> p1.login = 'login2'
  Traceback (most recent call last):
  ...
  ValueError: Principal Login already taken!

If such an attempt is made, the data are unchanged:

  >>> principals.authenticateCredentials({'login': 'bob', 'password': 'eek'})
  PrincipalInfo('principal.p1')

Removing principals
===================

Of course, if a principal is removed, we can no-longer authenticate it:

  >>> del principals['p1']
  >>> principals.authenticateCredentials({'login': 'bob',
  ...                                     'password': 'eek'})
