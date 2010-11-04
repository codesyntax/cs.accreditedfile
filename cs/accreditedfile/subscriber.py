from Acquisition import aq_parent
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Products.ATContentTypes.utils import DT2dt

import base64, socket, tempfile, os

from helpers import getClient

from cs.accreditedfile import accreditedfileMessageFactory as _
from Products.CMFCore.utils import getToolByName

def createTemporaryFile(contents):
    filehandle, filepath = tempfile.mkstemp()
    os.write(filehandle, contents)
    os.close(filehandle)
    return filepath

def getPublicationAccreditation(object, event):
    putils = getToolByName(object, 'plone_utils')
    registry = getUtility(IRegistry)
    certificate = registry[u'cs.accreditedfile.applicationkey']
    private_key = registry[u'cs.accreditedfile.applicationcertificate']
    endpointurl = registry[u'cs.accreditedfile.accrediterendpointurl']

    errocode = None
    cert_path = createTemporaryFile(certificate)
    pkey_path = createTemporaryFile(private_key)
    url = object.absolute_url()
    ip = socket.gethostbyaddr(url.split('/')[2])[2][0]
    if object.expiration_date is None:
        f_revision = DT2dt(aq_parent(object).expiration_date)
    else:
        f_revision = DT2dt(object.expiration_date)

    f_extension = object.getFilename().rsplit('.')[-1]
    
    try:
        client = getClient(endpointurl, pkey_path, cert_path)
        data = client.service.constancia(mi_url=base64.encodestring(url),
                                         mi_ip=ip,
                                         mi_puerto=url.startswith('https:') and 443 or 8080,
                                         mi_seguridad=url.startswith('https:'),
                                         mi_titulo=object.Title().decode('utf-8'),
                                         mi_fecharevision=f_revision,
                                         mi_tipo_firma=f_extension,
                                         )
        for item in data.item:
            if item.key == 'tipo' and item.value == 'error':
                # Handle error
                for item in data.item:
                    if item.key == 'coderror':
                        errorcode = item.value
            elif item.key == 'tipo' and item.value == 'url':
                for item in data.item:
                    if item.key == 'url_pdf':
                        object.url = data.value

        if errorcode is not None:
            putils.addPortalMessage(_(u'Accreditation correct'), type='info')
        else:
            putils.addPortalMessage(_(u'An error occurred getting the accreditation. Try again with the menu option: %(errorcode)s') % {'errorcode': errorcode}, type='warning')
    except:
        putils.addPortalMessage(_(u'An error occurred getting the accreditation. Try again with the menu option'), type='warning')

    finally:
        os.remove(cert_path)
        os.remove(pkey_path)


    

