from Acquisition import aq_inner, aq_parent
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Products.ATContentTypes.utils import DT2dt
from DateTime import DateTime

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
    parent = aq_parent(object)
    try:
        if not object.ExpirationDate() or object.ExpirationDate() == 'None':
            object.setExpirationDate(DateTime(parent.ExpirationDate()))

        t = transaction.get()
        accreditation_async_hook(1, object)
    except Exception,e:
        from logging import getLogger
        log = getLogger('cs.accreditedfile.file_checks')
        log.info(e)

        
def accreditation_async_hook(succeeded, object):

    from logging import getLogger
    log = getLogger('accreditation_async_hook')
    
    if succeeded:
        from plone.app.async.interfaces import IAsyncService
        async = getUtility(IAsyncService)
        job = async.queueJob(getPublicationAccreditation, object)
        log.info(job.status)
        
def accreditation_hook(succeeded, object_uid, parent):
    if succeeded:
        from logging import getLogger
        log = getLogger('cs.accreditedfile.accreditation_hook')       
        log.info('Calling')
        uid_catalog = getToolByName(aq_inner(parent), 'uid_catalog')
        items = uid_catalog(UID=object_uid)
        if items:
            getPublicationAccreditation(items[0].getObject())            
            log.info('Got accreditation')

def accreditation(object):
    """
    Helper method to get the accreditation for file
    with the given extension and url and expiration date
    """
    date = DT2dt(DateTime(object.ExpirationDate()))
    field = object.getField('file')
    extension = field.getFilename(object).rsplit('.')[-1]
    url = object.absolute_url()
    if not url.startswith('http'):
        # XXX
        # Testing shows that calling this
        # method from async processes does not
        # add the http beforehand, so we have 
        # to add it manually, removing the part
        # corresponding to the plone-site id
        url = siteurl + url.split(plonesiteid)[-1]

    result, accredited_url = get_accreditation_for_url(url, object.Title(), extension, date, object.Language())
    if result and accredited_url is not None:
        object.setUrl(accredited_url)
        return 1
    return 0

def get_accreditation_for_url(url, title, f_extension, f_revision, language):
    import logging
    from logging import getLogger
    log = getLogger('cs.accreditedfile.accreditation')
    log.addHandler(logging.handlers.RotatingFileHandler('cs.log'))
    
    registry = getUtility(IRegistry)
    private_key = registry[u'cs.accreditedfile.applicationkey']
    certificate = registry[u'cs.accreditedfile.applicationcertificate']
    endpointurl = registry[u'cs.accreditedfile.accrediterendpointurl']
    plonesiteid = registry[u'cs.accreditedfile.plonesiteid']
    siteurl = registry[u'cs.accreditedfile.plonesiteurl']

    errorcode = None
    cert_path = createTemporaryFile(certificate)
    pkey_path = createTemporaryFile(private_key)

    accredited_url = None
    
    try:
        ip = socket.gethostbyaddr(url.split('/')[2])[2][0]
    except:
        ip = '127.0.0.1'

    try:
        import time
        time.sleep(5)
        log.info(url)
        log.info(f_extension)
        client = getClient(endpointurl, pkey_path, cert_path)
        data = client.service.constancia(mi_url=base64.encodestring(url),
                                         mi_ip=ip,
                                         mi_puerto=url.startswith('https:') and 443 or 8080,
                                         mi_seguridad=url.startswith('https:'),
                                         mi_titulo=title.decode('utf-8'),
                                         mi_fecharevision=f_revision,
                                         mi_tipo_firma=f_extension,
                                         )
        
        for item in data.item:
            log.info(item.key)
            log.info(item.value)
                
            if item.key == 'tipo' and item.value == 'error':
                # Handle error
                for item2 in data.item:
                    if language == 'eu' and item2.key == 'msjerror_eus':
                        errorcode = item.value
                    elif language == 'es' and item2.key == 'msjerror_cas':
                        errorcode = item.value
                    elif language not in ['eu', 'es'] and item2.key == 'coderror':
                        errorcode = item2.value
                        
            elif item.key == 'tipo' and item.value == 'url':
                for item2 in data.item:
                    if item2.key == 'url_pdf':
                        accredited_url = item2.value
                        log.info(item2.value)
                        result = 1

        if errorcode is not None:
            log.info('Error: %s' % errorcode)
            result = errorcode

    except Exception,e:
        log.info('Exception: %s' % e)        
        result = e

    finally:
        os.remove(cert_path)
        os.remove(pkey_path)

    return result, accredited_url



def getPublicationAccreditation(object):
    from logging import getLogger
    log = getLogger('cs.accreditedfile.getPublicationAccreditation')       

    putils = getToolByName(object, 'plone_utils')

    if object.expiration_date is None:
        # No expiration date, try finding it in parent
        parent = aq_parent(object)
        if parent.expiration_date is not None:
            object.expiration_date = parent.expiration_date
        else:
            # Uff, show error message
            putils.addPortalMessage(_(u'You have not set an expiration date for this file. Set it first and then try to get the accreditation using the menu'), type='warning')
            log.info('Not expiration date')
            return 

    """
    field = object.getField('file')
    f_extension = field.getFilename(object).rsplit('.')[-1]
    if len(f_extension) > 3:
        # if the extension length is bigger than 2
        # we haven't found the correct extension
        # so try guessing from the content-type
        mr = getToolByName(object, 'mimetypes_registry')
        ct = field.getContentType(object)
        if ct:
            mts = mr.lookup(ct)
            for mt in mts:
                extensions = mt.extensions
                if extensions:
                    f_extension = extensions[0]
                    break
        else:
            f_extension = 'pdf'
    """

    result = accreditation(object)

    if result == 1:
        log.info('Accreditation correct')
        putils.addPortalMessage(_(u'Accreditation correct'), type='info')

    else:
        log.info('Error: %s' % result)
        putils.addPortalMessage(_(u'An error occurred getting the accreditation. Try again with the menu option: %(errorcode)s') % {'errorcode': result}, type='warning')

