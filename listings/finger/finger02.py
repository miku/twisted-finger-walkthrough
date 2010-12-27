#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.internet import protocol, reactor

class FingerProtocol(protocol.Protocol):
    pass

class FingerFactory(protocol.ServerFactory):
    protocol = FingerProtocol


# twisted.internet.interfaces.listenTCP(port, factory, backlog=50, interface='')
# Connects a given protocol factory to the given numeric TCP/IP port.
# :factory must be an instance of a ServerFactory
reactor.listenTCP(1079, FingerFactory())

# There is exactly one reactor in any running
# Twisted application. Once started it loops over and over again, responding to
# network events and making scheduled calls to code. 
reactor.run()
