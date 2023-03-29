# -*- coding: utf-8 -*-
import base64
import os
import socket
import tempfile

import requests
from Acquisition import aq_parent
from cs.accreditedfile import accreditedfileMessageFactory as _
from DateTime import DateTime
from plone.registry.interfaces import IRegistry
from Products.ATContentTypes.utils import DT2dt
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from zope.component import getUtility


def createTemporaryFile(contents):
    filehandle, filepath = tempfile.mkstemp()
    os.write(filehandle, contents)
    os.close(filehandle)
    return filepath


def accreditation(object):
    """
    Helper method to get the accreditation for file
    with the given extension and url and expiration date
    """
    date = DT2dt(DateTime(object.ExpirationDate())).date().isoformat()
    field = object.getField("file")
    extension = field.getFilename(object).rsplit(".")[-1]
    url = object.absolute_url()
    if not url.startswith("http"):
        # XXX
        # Testing shows that calling this
        # method from async processes does not
        # add the http beforehand, so we have
        # to add it manually, removing the part
        # corresponding to the plone-site id
        registry = getUtility(IRegistry)
        siteurl = registry[u"cs.accreditedfile.plonesiteurl"]
        plonesiteid = registry[u"cs.accreditedfile.plonesiteid"]
        url = siteurl + url.split(plonesiteid)[-1]

    result, accredited_url = get_accreditation_for_url(
        url, object.Title(), extension, date, object.Language()
    )
    if result and accredited_url is not None:
        object.setUrl(accredited_url)
        return 1
    return 0


def get_accreditation_for_url(url, title, f_extension, f_revision, language):
    registry = getUtility(IRegistry)
    endpointurl = registry[u"cs.accreditedfile.accrediterendpointurl"]
    pkcs_12_file_contents_b64 = registry[
        u"cs.accreditedfile.pkcs12_file_content_b64"
    ]
    pkcs_12_file_pass = registry[u"cs.accreditedfile.pkcs12_file_password"]
    try:
        ip = socket.gethostbyaddr(url.split("/")[2])[2][0]
    except:
        ip = "127.0.0.1"

    data = requests.post(
        endpointurl,
        json={
            "url": base64.encodestring(url),
            "ip": ip,
            "port": url.startswith("https:") and 443 or 80,
            "security": url.startswith("https:"),
            "title": safe_unicode(title).encode("utf-8"),
            "revision_date": f_revision,
            "extension": f_extension,
            "language": language,
            "p12filecontents": pkcs_12_file_contents_b64,
            "p12filepassword": pkcs_12_file_pass,
        },
    )

    results = data.json()

    return results.get("status"), results.get("url")


def getPublicationAccreditation(object):
    putils = getToolByName(object, "plone_utils")

    if object.expiration_date is None:
        # No expiration date, try finding it in parent
        parent = aq_parent(object)
        if parent.expiration_date is not None:
            object.expiration_date = parent.expiration_date
        else:
            # Uff, show error message
            putils.addPortalMessage(
                _(
                    u"You have not set an expiration date for this file. Set"
                    u" it first and then try to get the accreditation using"
                    u" the menu"
                ),
                type="warning",
            )
            return

    result = accreditation(object)

    if result == 1:
        putils.addPortalMessage(_(u"Accreditation correct"), type="info")

    else:
        putils.addPortalMessage(
            _(
                u"An error occurred getting the accreditation. Try again with"
                u" the menu option: %(errorcode)s"
            )
            % {"errorcode": result},
            type="warning",
        )
