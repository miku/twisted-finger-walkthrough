# Fix asymmetry

# The previous version had the setter poke at the innards of the finger factory.
# This strategy is usually not a good idea: this version makes both factories
# symmetric by making them both look at a single object. Services are useful for
# when an object is needed which is not related to a specific network server.
# Here, we define a common service class with methods that will create factories
# on the fly. The service also contains methods the factories will depend on.

from twisted.application import internet, service
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic

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

class FingerSetterProtocol(basic.LineReceiver):
    def connectionMade(self):
        self.lines = []

    def lineReceived(self, line):
        self.lines.append(line)

    def connectionLost(self,reason):
        user = self.lines[0]
        status = self.lines[1]
        self.factory.setUser(user, status)

class FingerService(service.Service):
    def __init__(self, **kwargs):
        self.users = kwargs

    def getUser(self, user):
        return defer.succeed(self.users.get(user, "No such user"))

    def setUser(self, user, status):
        self.users[user] = status

    def getFingerFactory(self):
        f = protocol.ServerFactory()
        f.protocol = FingerProtocol
        f.getUser = self.getUser
        return f

    def getFingerSetterFactory(self):
        f = protocol.ServerFactory()
        f.protocol = FingerSetterProtocol
        f.setUser = self.setUser
        return f

application = service.Application('finger', uid=1, gid=1)
f = FingerService(moshez='Happy and well')
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(79,f.getFingerFactory()
                   ).setServiceParent(serviceCollection)
internet.TCPServer(1079,f.getFingerSetterFactory()
                   ).setServiceParent(serviceCollection)

