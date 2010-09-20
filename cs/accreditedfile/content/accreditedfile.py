"""Definition of the AccreditedFile content type
"""

from zope.interface import implements

from Products.Archetypes import atapi
from Products.ATContentTypes.content import file
from Products.ATContentTypes.content import schemata

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


class AccreditedFile(file.ATFile):
    """File with publication accreditation by Izenpe"""
    implements(IAccreditedFile)

    meta_type = "AccreditedFile"
    schema = AccreditedFileSchema

    title = atapi.ATFieldProperty('title')
    description = atapi.ATFieldProperty('description')

    # -*- Your ATSchema to Python Property Bridges Here ... -*-
    url = atapi.ATFieldProperty('url')


atapi.registerType(AccreditedFile, PROJECTNAME)
