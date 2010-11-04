# -*- encoding: utf-8 -*-
import httplib
import urllib2
from suds.transport.https import HttpTransport
from suds.client import Client
from suds.options import Options


def getClient(url, key, cert):
    transport = HttpClientAuthTransport(key, cert)
    return Client(url, transport = transport)


#SUDS Client Auth solution
class HttpClientAuthTransport(HttpTransport):
    def __init__(self, key, cert, options = Options(),):
        HttpTransport.__init__(self)#, options)
        self.urlopener = urllib2.build_opener(HTTPSClientAuthHandler(key, cert))

#HTTPS Client Auth solution for urllib2, inspired by
# http://bugs.python.org/issue3466
# and improved by David Norton of Three Pillar Software. In this
# implementation, we use properties passed in rather than static module
# fields.
class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
    def __init__(self, key, cert):
        urllib2.HTTPSHandler.__init__(self)
        self.key = key
        self.cert = cert
    def https_open(self, req):
        #Rather than pass in a reference to a connection class, we pass in
        # a reference to a function which, for all intents and purposes,
        # will behave as a constructor
        return self.do_open(self.getConnection, req)
    def getConnection(self, host, timeout=None):
        return httplib.HTTPSConnection(host, key_file=self.key, cert_file=self.cert)


