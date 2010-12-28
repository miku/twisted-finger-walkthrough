# But let's try and fix setting away messages, shall we?
from twisted.application import internet, service
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic
from twisted.python import log

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

class FingerFactory(protocol.ServerFactory):
    protocol = FingerProtocol

    def __init__(self, **kwargs):
        self.users = kwargs

    def getUser(self, user):
        return defer.succeed(self.users.get(user, "No such user"))

class FingerSetterProtocol(basic.LineReceiver):
    def connectionMade(self):
        log.msg("connectionMade.")
        self.lines = []
        # How do we get out of telnet if CTRL-C or CTRL-D won't work?
        self.transport.write("Type 'q.' to exit." + '\r\n')
    
    def lineReceived(self, line):
        log.msg("lineReceived: {0}".format(line))
        self.lines.append(line)
        if line.strip() in ("q.", "quit.", "exit.", "close."):
            self.transport.loseConnection()

    def connectionLost(self, reason):
        log.msg("connectionLost: {0}".format(reason))
        user = self.lines[0]
        status = self.lines[1]
        self.factory.setUser(user, status)

class FingerSetterFactory(protocol.ServerFactory):
    protocol = FingerSetterProtocol

    def __init__(self, fingerFactory):
        self.fingerFactory = fingerFactory

    def setUser(self, user, status):
        self.fingerFactory.users[user] = status

ff = FingerFactory(moshez='Happy and well')
fsf = FingerSetterFactory(ff)

# This program has two protocol-factory-TCPServer pairs, which are both child
# services of the application. Specifically, the setServiceParent method is used
# to define the two TCPServer services as children of application, which
# implements IServiceCollection. Both services are thus started with the
# application.

application = service.Application('finger', uid=1, gid=1)
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(79,ff).setServiceParent(serviceCollection)
internet.TCPServer(1079,fsf).setServiceParent(serviceCollection)
