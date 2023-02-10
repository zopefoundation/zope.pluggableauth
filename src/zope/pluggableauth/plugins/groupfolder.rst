===============
 Group Folders
===============

Group folders provide support for groups information stored in the ZODB.  They
are persistent, and must be contained within the PAUs that use them.

Like other principals, groups are created when they are needed.

Group folders contain group-information objects that contain group information.
We create group information using the `GroupInformation` class:

  >>> import zope.pluggableauth.plugins.groupfolder
  >>> g1 = zope.pluggableauth.plugins.groupfolder.GroupInformation("Group 1")

  >>> groups = zope.pluggableauth.plugins.groupfolder.GroupFolder('group.')
  >>> groups['g1'] = g1

Note that when group-info is added, a GroupAdded event is generated:

  >>> from zope.pluggableauth import interfaces
  >>> from zope.component.eventtesting import getEvents
  >>> getEvents(interfaces.IGroupAdded)
  [<GroupAdded 'group.g1'>]

Groups are defined with respect to an authentication service.  Groups
must be accessible via an authentication service and can contain
principals accessible via an authentication service.

To illustrate the group interaction with the authentication service,
we'll create a sample authentication service:

  >>> from zope import interface
  >>> from zope.authentication.interfaces import IAuthentication
  >>> from zope.authentication.interfaces import PrincipalLookupError
  >>> from zope.security.interfaces import IGroupAwarePrincipal
  >>> from zope.pluggableauth.plugins.groupfolder import setGroupsForPrincipal

  >>> @interface.implementer(IGroupAwarePrincipal)
  ... class Principal:
  ...     def __init__(self, id, title='', description=''):
  ...         self.id, self.title, self.description = id, title, description
  ...         self.groups = []

  >>> class PrincipalCreatedEvent:
  ...     def __init__(self, authentication, principal):
  ...         self.authentication = authentication
  ...         self.principal = principal

  >>> from zope.pluggableauth.plugins import principalfolder

  >>> @interface.implementer(IAuthentication)
  ... class Principals:
  ...     def __init__(self, groups, prefix='auth.'):
  ...         self.prefix = prefix
  ...         self.principals = {
  ...            'p1': principalfolder.PrincipalInfo('p1', '', '', ''),
  ...            'p2': principalfolder.PrincipalInfo('p2', '', '', ''),
  ...            'p3': principalfolder.PrincipalInfo('p3', '', '', ''),
  ...            'p4': principalfolder.PrincipalInfo('p4', '', '', ''),
  ...            }
  ...         self.groups = groups
  ...         groups.__parent__ = self
  ...
  ...     def getAuthenticatorPlugins(self):
  ...         return [('principals', self.principals), ('groups', self.groups)]
  ...
  ...     def getPrincipal(self, id):
  ...         if not id.startswith(self.prefix):
  ...             raise PrincipalLookupError(id)
  ...         id = id[len(self.prefix):]
  ...         info = self.principals.get(id)
  ...         if info is None:
  ...             info = self.groups.principalInfo(id)
  ...             if info is None:
  ...                raise PrincipalLookupError(id)
  ...         principal = Principal(self.prefix+info.id,
  ...                               info.title, info.description)
  ...         setGroupsForPrincipal(PrincipalCreatedEvent(self, principal))
  ...         return principal

This class doesn't really implement the full `IAuthentication` interface, but
it implements the `getPrincipal` method used by groups. It works very much
like the pluggable authentication utility.  It creates principals on demand. It
calls `setGroupsForPrincipal`, which is normally called as an event subscriber,
when principals are created. In order for `setGroupsForPrincipal` to find out
group folder, we have to register it as a utility:

  >>> from zope.pluggableauth.interfaces import IAuthenticatorPlugin
  >>> from zope.component import provideUtility
  >>> provideUtility(groups, IAuthenticatorPlugin)

We will create and register a new principals utility:

  >>> principals = Principals(groups)
  >>> provideUtility(principals, IAuthentication)

Now we can set the principals on the group:

  >>> g1.principals = ['auth.p1', 'auth.p2']
  >>> g1.principals
  ('auth.p1', 'auth.p2')

Adding principals fires an event.

  >>> getEvents(interfaces.IPrincipalsAddedToGroup)[-1]
  <PrincipalsAddedToGroup ['auth.p1', 'auth.p2'] 'auth.group.g1'>

We can now look up groups for the principals:

  >>> groups.getGroupsForPrincipal('auth.p1')
  ('group.g1',)

Note that the group id is a concatenation of the group-folder prefix
and the name of the group-information object within the folder.

If we delete a group:

  >>> del groups['g1']

then the groups folder loses the group information for that group's
principals:

  >>> groups.getGroupsForPrincipal('auth.p1')
  ()

but the principal information on the group is unchanged:

  >>> g1.principals
  ('auth.p1', 'auth.p2')

It also fires an event showing that the principals are removed from the group
(g1 is group information, not a zope.security.interfaces.IGroup).

  >>> getEvents(interfaces.IPrincipalsRemovedFromGroup)[-1]
  <PrincipalsRemovedFromGroup ['auth.p1', 'auth.p2'] 'auth.group.g1'>

Adding the group sets the folder principal information.  Let's use a
different group name:

  >>> groups['G1'] = g1

  >>> groups.getGroupsForPrincipal('auth.p1')
  ('group.G1',)

Here we see that the new name is reflected in the group information.

An event is fired, as usual.

  >>> getEvents(interfaces.IPrincipalsAddedToGroup)[-1]
  <PrincipalsAddedToGroup ['auth.p1', 'auth.p2'] 'auth.group.G1'>

In terms of member events (principals added and removed from groups), we have
now seen that events are fired when a group information object is added and
when it is removed from a group folder; and we have seen that events are fired
when a principal is added to an already-registered group.  Events are also
fired when a principal is removed from an already-registered group.  Let's
quickly see some more examples.

  >>> g1.principals = ('auth.p1', 'auth.p3', 'auth.p4')
  >>> getEvents(interfaces.IPrincipalsAddedToGroup)[-1]
  <PrincipalsAddedToGroup ['auth.p3', 'auth.p4'] 'auth.group.G1'>
  >>> getEvents(interfaces.IPrincipalsRemovedFromGroup)[-1]
  <PrincipalsRemovedFromGroup ['auth.p2'] 'auth.group.G1'>
  >>> g1.principals = ('auth.p1', 'auth.p2')
  >>> getEvents(interfaces.IPrincipalsAddedToGroup)[-1]
  <PrincipalsAddedToGroup ['auth.p2'] 'auth.group.G1'>
  >>> getEvents(interfaces.IPrincipalsRemovedFromGroup)[-1]
  <PrincipalsRemovedFromGroup ['auth.p3', 'auth.p4'] 'auth.group.G1'>

Groups can contain groups:

  >>> g2 = zope.pluggableauth.plugins.groupfolder.GroupInformation("Group Two")
  >>> groups['G2'] = g2
  >>> g2.principals = ['auth.group.G1']

  >>> groups.getGroupsForPrincipal('auth.group.G1')
  ('group.G2',)

  >>> old = getEvents(interfaces.IPrincipalsAddedToGroup)[-1]
  >>> old
  <PrincipalsAddedToGroup ['auth.group.G1'] 'auth.group.G2'>

Groups cannot contain cycles:

  >>> g1.principals = ('auth.p1', 'auth.p2', 'auth.group.G2')
  ... # doctest: +NORMALIZE_WHITESPACE
  Traceback (most recent call last):
  ...
  zope.pluggableauth.plugins.groupfolder.GroupCycle: ('auth.group.G2', ['auth.group.G2', 'auth.group.G1'])

Trying to do so does not fire an event.

  >>> getEvents(interfaces.IPrincipalsAddedToGroup)[-1] is old
  True

They need not be hierarchical:

  >>> ga = zope.pluggableauth.plugins.groupfolder.GroupInformation("Group A")
  >>> groups['GA'] = ga

  >>> gb = zope.pluggableauth.plugins.groupfolder.GroupInformation("Group B")
  >>> groups['GB'] = gb
  >>> gb.principals = ['auth.group.GA']

  >>> gc = zope.pluggableauth.plugins.groupfolder.GroupInformation("Group C")
  >>> groups['GC'] = gc
  >>> gc.principals = ['auth.group.GA']

  >>> gd = zope.pluggableauth.plugins.groupfolder.GroupInformation("Group D")
  >>> groups['GD'] = gd
  >>> gd.principals = ['auth.group.GA', 'auth.group.GB']

  >>> ga.principals = ['auth.p1']

Group folders provide a very simple search interface.  They perform
simple string searches on group titles and descriptions.

  >>> list(groups.search({'search': 'gro'})) # doctest: +NORMALIZE_WHITESPACE
  ['group.G1', 'group.G2',
   'group.GA', 'group.GB', 'group.GC', 'group.GD']

  >>> list(groups.search({'search': 'two'}))
  ['group.G2']

They also support batching:

  >>> list(groups.search({'search': 'gro'}, 2, 3))
  ['group.GA', 'group.GB', 'group.GC']


If you don't supply a search key, no results will be returned:

  >>> list(groups.search({}))
  []

Identifying groups
==================
The function, `setGroupsForPrincipal`, is a subscriber to
principal-creation events.  It adds any group-folder-defined groups to
users in those groups:

  >>> principal = principals.getPrincipal('auth.p1')

  >>> principal.groups
  ['auth.group.G1', 'auth.group.GA']

Of course, this applies to groups too:

  >>> principal = principals.getPrincipal('auth.group.G1')
  >>> principal.id
  'auth.group.G1'

  >>> principal.groups
  ['auth.group.G2']

In addition to setting principal groups, the `setGroupsForPrincipal`
function also declares the `IGroup` interface on groups:

  >>> [iface.__name__ for iface in interface.providedBy(principal)]
  ['IGroup', 'IGroupAwarePrincipal']

  >>> [iface.__name__
  ...  for iface in interface.providedBy(principals.getPrincipal('auth.p1'))]
  ['IGroupAwarePrincipal']

Special groups
==============
Two special groups, Authenticated, and Everyone may apply to users
created by the pluggable-authentication utility.  There is a
subscriber, specialGroups, that will set these groups on any non-group
principals if IAuthenticatedGroup, or IEveryoneGroup utilities are
provided.

Lets define a group-aware principal:

  >>> import zope.security.interfaces
  >>> @interface.implementer(zope.security.interfaces.IGroupAwarePrincipal)
  ... class GroupAwarePrincipal(Principal):
  ...     def __init__(self, id):
  ...         Principal.__init__(self, id)
  ...         self.groups = []

If we notify the subscriber with this principal, nothing will happen
because the groups haven't been defined:

  >>> prin = GroupAwarePrincipal('x')
  >>> event = interfaces.FoundPrincipalCreated(42, prin, {})
  >>> zope.pluggableauth.plugins.groupfolder.specialGroups(event)
  >>> prin.groups
  []

Now, if we define the Everybody group:

  >>> import zope.authentication.interfaces
  >>> @interface.implementer(zope.authentication.interfaces.IEveryoneGroup)
  ... class EverybodyGroup(Principal):
  ...     pass

  >>> everybody = EverybodyGroup('all')
  >>> provideUtility(everybody, zope.authentication.interfaces.IEveryoneGroup)

Then the group will be added to the principal:

  >>> zope.pluggableauth.plugins.groupfolder.specialGroups(event)
  >>> prin.groups
  ['all']

Similarly for the authenticated group:

  >>> @interface.implementer(
  ...         zope.authentication.interfaces.IAuthenticatedGroup)
  ... class AuthenticatedGroup(Principal):
  ...     pass

  >>> authenticated = AuthenticatedGroup('auth')
  >>> provideUtility(authenticated, zope.authentication.interfaces.IAuthenticatedGroup)

Then the group will be added to the principal:

  >>> prin.groups = []
  >>> zope.pluggableauth.plugins.groupfolder.specialGroups(event)
  >>> prin.groups.sort()
  >>> prin.groups
  ['all', 'auth']

These groups are only added to non-group principals:

  >>> prin.groups = []
  >>> interface.directlyProvides(prin, zope.security.interfaces.IGroup)
  >>> zope.pluggableauth.plugins.groupfolder.specialGroups(event)
  >>> prin.groups
  []

And they are only added to group aware principals:

  >>> @interface.implementer(zope.security.interfaces.IPrincipal)
  ... class SolitaryPrincipal:
  ...     id = title = description = ''

  >>> event = interfaces.FoundPrincipalCreated(42, SolitaryPrincipal(), {})
  >>> zope.pluggableauth.plugins.groupfolder.specialGroups(event)
  >>> prin.groups
  []

Member-aware groups
===================
The groupfolder includes a subscriber that gives group principals the
zope.security.interfaces.IGroupAware interface and an implementation thereof.
This allows groups to be able to get and set their members.

Given an info object and a group...

    >>> @interface.implementer(
    ...         zope.pluggableauth.plugins.groupfolder.IGroupInformation)
    ... class DemoGroupInformation(object):
    ...     def __init__(self, title, description, principals):
    ...         self.title = title
    ...         self.description = description
    ...         self.principals = principals
    ...
    >>> i = DemoGroupInformation(
    ...     'Managers', 'Taskmasters', ('joe', 'jane'))
    ...
    >>> info = zope.pluggableauth.plugins.groupfolder.GroupInfo(
    ...     'groups.managers', i)
    >>> @interface.implementer(IGroupAwarePrincipal)
    ... class DummyGroup(object):
    ...     def __init__(self, id, title='', description=''):
    ...         self.id = id
    ...         self.title = title
    ...         self.description = description
    ...         self.groups = []
    ...
    >>> principal = DummyGroup('foo')
    >>> zope.security.interfaces.IMemberAwareGroup.providedBy(principal)
    False

...when you call the subscriber, it adds the two pseudo-methods to the
principal and makes the principal provide the IMemberAwareGroup interface.

    >>> zope.pluggableauth.plugins.groupfolder.setMemberSubscriber(
    ...     interfaces.FoundPrincipalCreated(
    ...         'dummy auth (ignored)', principal, info))
    >>> principal.getMembers()
    ('joe', 'jane')
    >>> principal.setMembers(('joe', 'jane', 'jaimie'))
    >>> principal.getMembers()
    ('joe', 'jane', 'jaimie')
    >>> zope.security.interfaces.IMemberAwareGroup.providedBy(principal)
    True

The two methods work with the value on the IGroupInformation object.

    >>> i.principals == principal.getMembers()
    True

Limitation
----------

The current group-folder design has an important limitation!

There is no point in assigning principals to a group
from a group folder unless the principal is from the same pluggable
authentication utility.

* If a principal is from a higher authentication utility, the user
  will not get the group definition. Why? Because the principals
  group assignments are set when the principal is authenticated. At
  that point, the current site is the site containing the principal
  definition. Groups defined in lower sites will not be consulted,

* It is impossible to assign users from lower authentication
  utilities because they can't be seen when managing the group,
  from the site containing the group.

A better design might be to store user-role assignments independent of
the group definitions and to look for assignments during (url)
traversal.  This could get quite complex though.

While it is possible to have multiple authentication utilities long a
URL path, it is generally better to stick to a simpler model in which
there is only one authentication utility along a URL path (in addition
to the global utility, which is used for bootstrapping purposes).
