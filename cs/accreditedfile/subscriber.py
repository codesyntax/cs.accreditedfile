# -*- coding: utf-8 -*-
from plone import api
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
from logging import getLogger


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
    date = object.expires.toZone("UTC").ISO8601()
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
        siteurl = registry["cs.accreditedfile.plonesiteurl"]
        plonesiteid = registry["cs.accreditedfile.plonesiteid"]
        url = siteurl + url.split(plonesiteid)[-1]

    result, accredited_url, message = get_accreditation_for_url(
        url, object.Title(), extension, date, object.Language()
    )
    if result and accredited_url:
        if result == 1:
            object.setUrl(accredited_url)
            log = getLogger(__name__)
            log.info("OK Izenpe: url: %s message: %s", url, message)
            return 1, message
        else:
            log.info("Error Izenpe: url: %s message: %s", url, message)
            return 0, message

    log.info("Error Izenpe: url: %s message: %s", url, message)
    return 0, message


def get_accreditation_for_url(url, title, f_extension, f_revision, language):
    registry = getUtility(IRegistry)
    endpointurl = registry["cs.accreditedfile.accrediterendpointurl"]
    pkcs_12_file_contents_b64 = registry["cs.accreditedfile.pkcs12_file_content_b64"]
    pkcs_12_file_pass = registry["cs.accreditedfile.pkcs12_file_password"]
    try:
        ip = socket.gethostbyaddr(url.split("/")[2])[2][0]
    except:
        ip = "127.0.0.1"

    data = requests.post(
        endpointurl,
        json={
            "url": url,
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
        timeout=10,
    )
    if data.ok:
        results = data.json()

        return results.get("status"), results.get("url"), results.get("message")
    else:
        return 0, None, ""


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
                    "You have not set an expiration date for this file. Set"
                    " it first and then try to get the accreditation using"
                    " the menu"
                ),
                type="warning",
            )
            return

    result, message = accreditation(object)

    if result == 1:
        putils.addPortalMessage(_("Accreditation correct"), type="info")
        send_mail(message, object)

    else:
        putils.addPortalMessage(
            _(
                "An error occurred getting the accreditation. Try again with"
                " the menu option: %(errorcode)s"
            )
            % {"errorcode": result},
            type="warning",
        )
        send_mail(message, object)



def send_mail(message, object):
    mailhost = api.portal.get_tool('MailHost')
    portal = api.portal.get()
    messageText = 'Izenperekin konexioaren emaitza: %s' % message
    mailhost.send(messageText, mto='mlarreategi@codesyntax.com', mfrom=portal.email_from_address, subject='Izenpe emaitza',

    )
