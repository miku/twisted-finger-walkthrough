# Read username, output from non-empty factory, drop connections
# Use deferreds, to minimize synchronicity assumptions
# Write application. Save in 'finger.tpy'

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

class FingerFactory(protocol.ServerFactory):
    protocol = FingerProtocol

    def __init__(self, **kwargs):
        self.users = kwargs

    def getUser(self, user):
        return defer.succeed(self.users.get(user, "No such user"))

application = service.Application('finger', uid=1, gid=1)
factory = FingerFactory(moshez='Happy and well')
internet.TCPServer(79, factory).setServiceParent(
    service.IServiceCollection(application))

# root% twistd -ny finger11.tac # just like before
# root% twistd -y finger11.tac # daemonize, keep pid in twistd.pid
# root% twistd -y finger11.tac --pidfile=finger.pid
# root% twistd -y finger11.tac --rundir=/
# root% twistd -y finger11.tac --chroot=/var
# root% twistd -y finger11.tac -l /var/log/finger.log
# root% twistd -y finger11.tac --syslog # just log to syslog
# root% twistd -y finger11.tac --syslog --prefix=twistedfinger # use given prefix