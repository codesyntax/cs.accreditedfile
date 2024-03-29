# -*- coding: utf-8 -*-
"""
This module contains the tool of cs.accreditedfile
"""
import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


version = "1.5"

long_description = (
    read("README.txt")
    + "\n"
    + "Change history\n**************\n"
    + "\n"
    + read("CHANGES.txt")
    + "\n"
    + "Detailed Documentation\n**********************\n"
    + "\n"
    + read("cs", "accreditedfile", "README.txt")
    + "\n"
    + "Contributors\n************\n"
    + "\n"
    + read("CONTRIBUTORS.txt")
    + "\n"
    + "Download\n********\n"
)

tests_require = ["zope.testing"]

setup(
    name="cs.accreditedfile",
    version=version,
    description=(
        "Files that get published in a website and the publication is"
        " accredited by Izenpe (http://www.izenpe.com)"
    ),
    long_description=long_description,
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Framework :: Plone",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    keywords="",
    author="Mikel Larreategi",
    author_email="mlarreategi@codesyntax.com",
    url="http://www.codesyntax.com/products/cs.accreditedfile",
    license="GPL",
    packages=find_packages(exclude=["ez_setup"]),
    namespace_packages=[
        "cs",
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        # -*- Extra requirements: -*-
        "plone.app.registry",
        "suds",
        "requests-pkcs12",
    ],
    tests_require=tests_require,
    extras_require=dict(tests=tests_require),
    test_suite="cs.accreditedfile.tests.test_docs.test_suite",
    entry_points="""
      # -*- entry_points -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
)
