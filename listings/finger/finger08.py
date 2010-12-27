#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Read username, output from non-empty factory, drop connections
# Use deferreds, to minimize synchronicity assumptions

from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic

class FingerProtocol(basic.LineReceiver):
    def lineReceived(self, user):
        d = self.factory.getUser(user)
        
        def onError(err):
            return "Internal error in server"
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

        # But, here we tweak it just for the hell of it. Yes, while the previous
        # version worked, it did assume the result of getUser is always
        # immediately available. But what if instead of an in-memory database,
        # we would have to fetch the result from a remote Oracle server? By
        # allowing getUser to return a Deferred, we make it easier for the data
        # to be retrieved asynchronously so that the CPU can be used for other
        # tasks in the meanwhile.

        return defer.succeed(self.users.get(user, "No such user"))
        
reactor.listenTCP(1079, FingerFactory(moshez="Happy and well"))
reactor.run()

# As described in the Deferred HOWTO, Deferreds allow a program to be driven by
# events. For instance, if one task in a program is waiting on data, rather than
# have the CPU (and the program!) idly waiting for that data (a process normally
# called 'blocking'), the program can perform other operations in the meantime,
# and waits for some signal that data is ready to be processed before returning
# to that process.

# In brief, the code in FingerFactory above creates a Deferred, to which we
# start to attach callbacks. The deferred action in FingerFactory is actually a
# fast-running expression consisting of one dictionary method, get. Since this
# action can execute without delay, FingerFactory.getUser uses defer.succeed to
# create a Deferred which already has a result, meaning its return value will be
# passed immediately to the first callback function, which turns out to be
# FingerProtocol.writeResponse. We've also defined an errback (appropriately
# named FingerProtocol.onError) that will be called instead of writeResponse if
# something goes wrong.