from zope.interface import implements, Interface

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from cs.accreditedfile import accreditedfileMessageFactory as _

from zope.component import getUtility
from plone.registry.interfaces import IRegistry


class IAccreditedFileView(Interface):
    """
    AccreditedFile view interface
    """

    def accrediter():
        """
        Return the name of the accrediter
        """

class AccreditedFileView(BrowserView):
    """
    AccreditedFile browser view
    """
    implements(IAccreditedFileView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()


    def accrediter(self):
        registry = getUtility(IRegistry)
        return registry['cs.accreditedfile.accreditername']
