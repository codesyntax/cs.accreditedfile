from Acquisition import aq_inner, aq_parent
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Products.ATContentTypes.utils import DT2dt

import base64, socket, tempfile, os

from helpers import getClient

from cs.accreditedfile import accreditedfileMessageFactory as _
from Products.CMFCore.utils import getToolByName

import transaction

def createTemporaryFile(contents):
    filehandle, filepath = tempfile.mkstemp()
    os.write(filehandle, contents)
    os.close(filehandle)
    return filepath

def file_checks(object, event):
    # Object is published after the transaction
    # commit, so we have to register a after-transaction-commit
    # hook to call the accreditation method
    parent = aq_parent(object)
    if not object.expiration_date:
        object.expiration_date = parent.expiration_date

    t = transaction.get()
    t.addAfterCommitHook(accreditation_hook, kws={'object_uid':object.UID(), 'parent':parent})

def accreditation_hook(succeeded, object_uid, parent):
    if succeeded:
        from logging import getLogger
        log = getLogger('cs.accreditedfile.accreditation_hook')       
        log.info('Calling')
        uid_catalog = getToolByName(aq_inner(parent), 'uid_catalog')
        items = uid_catalog(UID=object_uid)
        if items:
            getPublicationAccreditation(items[0])            
            log.info('Got accreditation')


def getPublicationAccreditation(object):
    putils = getToolByName(object, 'plone_utils')
    registry = getUtility(IRegistry)
    private_key = registry[u'cs.accreditedfile.applicationkey']
    certificate = registry[u'cs.accreditedfile.applicationcertificate']
    endpointurl = registry[u'cs.accreditedfile.accrediterendpointurl']

    errorcode = None
    cert_path = createTemporaryFile(certificate)
    pkey_path = createTemporaryFile(private_key)
    url = object.absolute_url()
    try:
        ip = socket.gethostbyaddr(url.split('/')[2])[2][0]
    except:
        ip = '127.0.0.1'

    import pdb;pdb.set_trace()
    
    if object.expiration_date is None:
        # No expiration date, try finding it in parent
        parent = aq_parent(object)
        if parent.expiration_date is not None:
            f_revision = DT2dt(parent.expiration_date)
            object.expiration_date = parent.expiration_date
        else:
            # Uff, show error message
            putils.addPortalMessage(_(u'You have not set an expiration date for this file. Set it first and then try to get the accreditation using the menu'), type='warning')
            return

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
                for item2 in data.item:
                    if object.Language() == 'eu' and item2.key == 'msjerror_eus':
                        errorcode = item.value
                    elif object.Language() == 'es' and item2.key == 'msjerror_cas':
                        errorcode = item.value
                    elif object.Language() not in ['eu', 'es'] and item2.key == 'coderror':
                        errorcode = item2.value
                        
            elif item.key == 'tipo' and item.value == 'url':
                for item2 in data.item:
                    if item2.key == 'url_pdf':
                        object.url = item2.value

        if errorcode is not None:
            putils.addPortalMessage(_(u'An error occurred getting the accreditation. Try again with the menu option: %(errorcode)s') % {'errorcode': errorcode}, type='warning')
        else:
            putils.addPortalMessage(_(u'Accreditation correct'), type='info')

    except Exception,e:
        putils.addPortalMessage(_(u'An error occurred getting the accreditation. Try again with the menu option'), type='warning')

        from logging import getLogger
        log = getLogger('cs.accredittedfile')
        log.info('Exception: %s' % e)        

    finally:
        os.remove(cert_path)
        os.remove(pkey_path)


    

