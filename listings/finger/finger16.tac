# Read from file, announce on the web, irc
from twisted.application import internet, service
from twisted.internet import protocol, reactor, defer
from twisted.words.protocols import irc
from twisted.protocols import basic
from twisted.web import resource, server, static

import cgi

# This is the first time there is client code. IRC clients often act a lot like
# servers: responding to events from the network. The reconnecting client
# factory will make sure that severed links will get re-established, with
# intelligent tweaked exponential back-off algorithms. The IRC client itself is
# simple: the only real hack is getting the nickname from the factory in
# connectionMade.


# FingerService now has another new function, getIRCbot, which returns the
# ReconnectingClientFactory. This factory in turn will instantiate the
# IRCReplyBot protocol. The IRCBot is configured in the last line to connect to
# irc.freenode.org with a nickname of fingerbot.
# 
# By overriding irc.IRCClient.connectionMade, IRCReplyBot can access the
# nickname attribute of the factory that instantiated it.

class FingerProtocol(basic.LineReceiver):
    def lineReceived(self, user):
        d = self.factory.getUser(user)

        def onError(err):
            return 'Internal error in server'
        d.addErrback(onError)

        def writeResponse(message):
            self.transport.write(message + '\r\n')
            self.transport.loseConnection()
        d.addCallback(writeResponse)


class IRCReplyBot(irc.IRCClient):
    def connectionMade(self):
        self.nickname = self.factory.nickname
        irc.IRCClient.connectionMade(self)

    def privmsg(self, user, channel, msg):
        user = user.split('!')[0]
        if self.nickname.lower() == channel.lower():
            d = self.factory.getUser(msg)

            def onError(err):
                return 'Internal error in server'
            d.addErrback(onError)

            def writeResponse(message):
                irc.IRCClient.msg(self, user, msg+': '+message)
            d.addCallback(writeResponse)

class FingerService(service.Service):
    def __init__(self, filename):
        self.filename = filename
        self.users = {}
        self._read()

    def _read(self):
        self.users.clear()
        for line in file(self.filename):
            user, status = line.split(':', 1)
            user = user.strip()
            status = status.strip()
            self.users[user] = status
        self.call = reactor.callLater(30, self._read)

    def getUser(self, user):
        return defer.succeed(self.users.get(user, "No such user"))

    def getFingerFactory(self):
        f = protocol.ServerFactory()
        f.protocol = FingerProtocol
        f.getUser = self.getUser
        return f

    def getResource(self):
        r = resource.Resource()
        r.getChild = (lambda path, request:
                      static.Data('<h1>%s</h1><p>%s</p>' %
                      tuple(map(cgi.escape,
                      [path,self.users.get(path,
                      "No such user <p/> usage: site/user")])),
                      'text/html'))
        return r

    def getIRCBot(self, nickname):
        f = protocol.ReconnectingClientFactory()
        f.protocol = IRCReplyBot
        f.nickname = nickname
        f.getUser = self.getUser
        return f

application = service.Application('finger', uid=1, gid=1)
f = FingerService('/etc/users')
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(79, f.getFingerFactory()
                   ).setServiceParent(serviceCollection)
internet.TCPServer(8000, server.Site(f.getResource())
                   ).setServiceParent(serviceCollection)
internet.TCPClient('irc.freenode.org', 6667, f.getIRCBot('fingerbot')
                   ).setServiceParent(serviceCollection)