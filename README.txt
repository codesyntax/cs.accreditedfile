cs.accreditedfile
------------------

AccreditedFiles are files which publication is accredited by
a third-party service.

IZENPE, the Basque Government's certification service provider
has a web service to get this kind of certification.

You have to contact them to ask for an application key and
certificate and documentation about the web service.

After installing this product, you will have some configuration
items to check in the portal_registry. You have to provide the
application key and certificate provided by IZENPE.

We use suds library to contact the webservice. Due to the limitations
imposed by suds, each time the web service is called the certificate
and the key have to be written to the filesystem. But we have
write the code to safely delete those files to avoid security issues.

This product uses a subscriber and a ZODB after-commit-hook to get 
the accreditation, because IZENPE needs to see the item published on
the site and in Zope items are not published until the transaction
is commited, so we add an after-commit-hook to contact IZENPE.
