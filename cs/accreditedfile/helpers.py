# -*- encoding: utf-8 -*-
import functools
import traceback

import httplib
import requests
import suds.transport as transport
import urllib2
from StringIO import StringIO
from suds.client import Client
from suds.options import Options
from suds.transport import Reply, TransportError
from suds.transport.http import HttpAuthenticated
from suds.transport.https import HttpTransport

from requests_pkcs12 import get as pkcs12_get
from requests_pkcs12 import post as pkcs12_post


def handle_errors(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.HTTPError as e:
            buf = StringIO(e.response.content)
            raise transport.TransportError(
                "Error in requests\n" + traceback.format_exc(),
                e.response.status_code,
                buf,
            )
        except requests.RequestException:
            buf = StringIO(traceback.format_exc().encode("utf-8"))
            raise transport.TransportError(
                "Error in requests\n" + traceback.format_exc(),
                000,
                buf,
            )

    return wrapper


class RequestsTransport(transport.Transport):
    def __init__(
        self, session=None, pkcs12_file=None, pkcs12_pass=None, verify=False
    ):
        transport.Transport.__init__(self)
        self._session = session or requests.Session()
        self.pkcs12_file = pkcs12_file
        self.pkcs12_pass = pkcs12_pass
        self.verify = verify

    @handle_errors
    def open(self, request):
        if self.pkcs12_file and self.pkcs12_pass:
            import pdb

            pdb.set_trace()
            a = 1

            resp = pkcs12_get(
                request.url,
                pkcs12_filename=self.pkcs12_file,
                pkcs12_password=self.pkcs12_pass,
                verify=self.verify,
            )
        else:
            resp = self._session.get(request.url, verify=self.verify)
        resp.raise_for_status()
        return StringIO(resp.content)

    @handle_errors
    def send(self, request):
        if self.pkcs12_file and self.pkcs12_pass:
            import pdb

            pdb.set_trace()
            a = 1

            resp = pkcs12_post(
                request.url,
                data=request.message,
                pkcs12_filename=self.pkcs12_file,
                pkcs12_password=self.pkcs12_pass,
                headers=request.headers,
            )
        else:
            resp = self._session.post(
                request.url,
                data=request.message,
                headers=request.headers,
            )
        if resp.headers.get("content-type") not in (
            "text/xml",
            "application/soap+xml",
        ):
            resp.raise_for_status()
        return transport.Reply(
            resp.status_code,
            resp.headers,
            resp.content,
        )


def getClient2(wsdl_uri, pkcs12_file, pkcs12_pass):

    headers = {"Content-Type": "text/xml;charset=UTF-8", "SOAPAction": ""}
    t = RequestsTransport(
        pkcs12_file=pkcs12_file, pkcs12_pass=pkcs12_pass, verify=False
    )
    return Client(wsdl_uri, headers=headers, transport=t)
