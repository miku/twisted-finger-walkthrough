# Read from file
from twisted.application import internet, service
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic


# Since this version is reading data from a file (and refreshing the data every
# 30 seconds), there is no FingerSetterFactory and thus nothing listening on
# port 1079.

# Here we override the standard startService and stopService hooks in the Finger
# service, which is set up as a child service of the application in the last
# line of the code. startService calls _read, the function responsible for
# reading the data; reactor.callLater is then used to schedule it to run again
# after thirty seconds every time it is called. reactor.callLater returns an
# object that lets us cancel the scheduled run in stopService using its cancel
# method.

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

class FingerService(service.Service):
    def __init__(self, filename):
        self.users = {}
        self.filename = filename

    def _read(self):
        for line in file(self.filename):
            user, status = line.split(':', 1)
            user = user.strip()
            status = status.strip()
            self.users[user] = status
        self.call = reactor.callLater(30, self._read)

    def startService(self):
        self._read()
        service.Service.startService(self)

    def stopService(self):
        service.Service.stopService(self)
        self.call.cancel()

    def getUser(self, user):
        return defer.succeed(self.users.get(user, "No such user"))

    def getFingerFactory(self):
        f = protocol.ServerFactory()
        f.protocol = FingerProtocol
        f.getUser = self.getUser
        return f


import os

def touch(fname, times = None):
    with file(fname, 'a'):
        os.utime(fname, times)

finger_users = os.path.join(os.path.expanduser('~'), '.finger_users')
if not os.path.exists(finger_users):
	touch(finger_users)

application = service.Application('finger', uid=1, gid=1)
f = FingerService(finger_users)
finger = internet.TCPServer(79, f.getFingerFactory())

finger.setServiceParent(service.IServiceCollection(application))
f.setServiceParent(service.IServiceCollection(application))