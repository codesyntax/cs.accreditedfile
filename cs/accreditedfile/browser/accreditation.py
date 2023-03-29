from Acquisition import aq_inner
from Products.Five.browser import BrowserView

from cs.accreditedfile.subscriber import getPublicationAccreditation
from plone.protect.interfaces import IDisableCSRFProtection
from zope.interface import alsoProvides


class Accreditation(BrowserView):
    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        context = aq_inner(self.context)
        getPublicationAccreditation(context)
        return self.request.response.redirect(context.absolute_url() + "/view")
