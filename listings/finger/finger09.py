#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Read username, output from factory interfacing to OS, drop connections

from twisted.internet import protocol, reactor, defer, utils
from twisted.protocols import basic

class FingerProtocol(basic.LineReceiver):
    def lineReceived(self, user):
        d = self.factory.getUser(user)
        
        def onError(err):
            return "Internal error in server: {0}\n{1}".format(err, err.__dict__)
            
        d.addErrback(onError)
        
        def writeResponse(message):
            self.transport.write(message + "\r\n")
            self.transport.loseConnection()
        
        d.addCallback(writeResponse)
            

class FingerFactory(protocol.ServerFactory):
    protocol = FingerProtocol
    
    def __init__(self, **kwargs):
        self.users = kwargs
    
    def getUser(self, user):

        # This example also makes use of a Deferred.
        # twisted.internet.utils.getProcessOutput is a non-blocking version of Python's
        # commands.getoutput: it runs a shell command (finger, in this case) and
        # captures its standard output. However, getProcessOutput returns a Deferred
        # instead of the output itself. Since FingerProtocol.lineReceived is already
        # expecting a Deferred to be returned by getUser, it doesn't need to be changed,
        # and it returns the standard output as the finger result.

        return utils.getProcessOutput("finger", [user], errortoo=True)
        
reactor.listenTCP(1079, FingerFactory())
reactor.run()

