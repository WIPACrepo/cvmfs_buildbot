# -*- coding: utf-8 -*-

import ldap3
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.credentials import IUsernamePassword
from twisted.cred.error import UnauthorizedLogin
from twisted.internet import defer
from zope.interface.declarations import implements
from zope.interface import implementer
from twisted.cred.portal import Portal
from twisted.web.error import Error
from twisted.web.guard import BasicCredentialFactory
from twisted.web.guard import HTTPAuthSessionWrapper
from buildbot.www import auth
from buildbot.www import resource

class LDAPAuth(auth.AuthBase):

    def __init__(self, lserver, bind, group, admin_group, **kwargs):
        self.credentialFactories = [BasicCredentialFactory("buildbot"),]
        self.checkers = [LDAPAuthChecker(lserver, bind, group),]
        self.userInfoProvider = LDAPUserInfoProvider(lserver, bind, admin_group)

    def getLoginResource(self):
        return HTTPAuthSessionWrapper(
            Portal(auth.AuthRealm(self.master, self), self.checkers),
            self.credentialFactories)


class LDAPUserInfoProvider(auth.UserInfoProviderBase):
    name = "LDAP"
    lserver = ""
    base_dn = ""

    def __init__(self, lserver, bind, group):
        self.lserver = lserver
        self.base_dn = bind

        
        l = ldap3.Connection(self.lserver, auto_bind=True)
        groupFilter = '(cn='+group+')'
        l.search(self.base_dn, groupFilter, attributes=ldap3.ALL_ATTRIBUTES)
        self.group_members = l.entries[0].memberUid.value

    def getUserInfo(self, username):
        l = ldap3.Connection(self.lserver, auto_bind=True)
        userFilter = '(uid='+username+')'
        results = l.search(self.base_dn, userFilter, attributes=ldap3.ALL_ATTRIBUTES)
        details = l.entries[0]
        groups = ['buildbot', username]
        if username in self.group_members:
            groups.append('buildbot-admin')
        return defer.succeed(dict(userName=username,
                                  fullName=details.gecos.value,
                                  email=details.mail.value,
                                  groups=groups))


class LDAPAuthChecker():
    implements (ICredentialsChecker)

    credentialInterfaces = IUsernamePassword,

    lserver = ""
    base_dn = ""
    group = ""


    def __init__(self, lserver, bind, group):
        self.lserver = lserver
        self.base_dn = bind
        self.group = group

    def requestAvatarId(self, credentials):
        # check username/password
        l = ldap3.Connection(self.lserver, 'uid={},ou=People,{}'.format(credentials.username, self.base_dn),
                             credentials.password, auto_bind=True)

        # check group
        #groupFilter = '(&(cn='+self.group+')(memberUid=' +credentials.username+'))'
        #if l.search(self.base_dn, groupFilter):
        return defer.succeed(credentials.username)

        # Something went wrong. Simply fail authentication
        return defer.fail(UnauthorizedLogin("unable to verify password"))        
