"""Definition of the AccreditedFile content type
"""

from zope.interface import implements
from zope.i18n import translate
from Acquisition import aq_parent

from Products.Archetypes import atapi
from Products.ATContentTypes.content import file
from Products.ATContentTypes.content import schemata
from Products.Archetypes import PloneMessageFactory as _PMF

# -*- Message Factory Imported Here -*-
from cs.accreditedfile import accreditedfileMessageFactory as _
from cs.accreditedfile.interfaces import IAccreditedFile
from cs.accreditedfile.config import PROJECTNAME

AccreditedFileSchema = file.ATFileSchema.copy() + atapi.Schema((

    # -*- Your Archetypes field definitions here ... -*-
    atapi.StringField('url',
                      required=False,
                      searchable=True,
                      languageIndependent=True,
                      storage = atapi.AnnotationStorage(),
                      widget = atapi.StringWidget(
                               description = '',
                               label=_(u'label_url', default=u'Accreditation URL'),
                               visible={'view': 'visible', 'edit': 'invisible' } 
                               )
              ),
))

# Set storage on fields copied from ATContentTypeSchema, making sure
# they work well with the python bridge properties.

AccreditedFileSchema['title'].storage = atapi.AnnotationStorage()
AccreditedFileSchema['description'].storage = atapi.AnnotationStorage()

schemata.finalizeATCTSchema(AccreditedFileSchema, moveDiscussion=False)

# Move dates to main schemata. finalizeSchemata moves them to 'dates'
AccreditedFileSchema.changeSchemataForField('effectiveDate', 'default')
AccreditedFileSchema.changeSchemataForField('expirationDate', 'default')


class AccreditedFile(file.ATFile):
    """File with publication accreditation by Izenpe"""
    implements(IAccreditedFile)

    meta_type = "AccreditedFile"
    schema = AccreditedFileSchema

    title = atapi.ATFieldProperty('title')
    description = atapi.ATFieldProperty('description')

    # -*- Your ATSchema to Python Property Bridges Here ... -*-
    url = atapi.ATFieldProperty('url')


    def pre_validate(self, REQUEST=None, errors=None):
        super(file.ATFile, self).pre_validate(REQUEST, errors)
        if self.expiration_date is None:
            parent = aq_parent(self)
            if parent.expiration_date is None:
                error = _PMF(u'error_required',
                             default=u'${name} is required, please correct.',
                             mapping={'name': 'expirationDate'})
                error = translate(error, context=REQUEST)
                errors['expirationDate'] = error
            else:
                self.expiration_date = parent.expiration_date

atapi.registerType(AccreditedFile, PROJECTNAME)
