"""
Copyright (C) 2009 Polar Technologies - www.polartech.es
Author: Alvaro Iradier <alvaro.iradier@polartech.es>
"""

from setuptools import setup

setup(
    name = 'WikiInclude',
    version = '0.2',
    packages = ['wikiinclude'],
    author = "Alvaro J. Iradier",
    author_email = "alvaro.iradier@polartech.es",
    description = "Include other wiki pages, attachments or repository files inside wiki pages",
    license = "GPL",
    keywords = "trac plugin wiki include",
    url = "http://trac-hacks.org/wiki/WikiInclude",

    entry_points = {
        'trac.plugins': [
            'wikiinclude.wikiinclude = wikiinclude.wikiinclude',
        ],
    },
    
    install_requires = [ 'Trac', ],
    
)
