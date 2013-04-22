from setuptools import setup

PACKAGE = 'tracprojectmanager'
VERSION = '0.8.0'

setup(name=PACKAGE,
    version=VERSION,
    packages=['tracprojectmanager'],
    package_data={
        'tracprojectmanager': [
            'htdocs/css/*.css',
            'htdocs/img/*.png',
            'htdocs/js/*.js',
            'templates/*.html'
        ]
    },
    author='Alvaro J. Iradier',
    author_email = "alvaro.iradier@polartech.es",
    description = "Multi project improvements for Trac",
    long_description = "",
    license = "GPL",
    keywords = "trac plugin multi project multiproject", 
    url="",
    
    entry_points = {
        'trac.plugins': ['tracprojectmanager = tracprojectmanager']
    })
