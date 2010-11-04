from Acquisition import aq_inner
from Products.Five.browser import BrowserView

from cs.accreditedfile.subscriber import getPublicationAccreditation

class Accreditation(BrowserView):
    def __call__(self):
        context = aq_inner(self.context)
        getPublicationAccreditation(context, None)
        return self.request.response.redirect(context.absolute_url())


        
    
