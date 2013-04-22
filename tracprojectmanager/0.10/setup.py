from setuptools import setup

PACKAGE = 'tracprojectmanager'
VERSION = '0.1'

setup(name='tracprojectmanager',
    version='0.1',
    packages=['tracprojectmanager'],
    package_data={
        'tracprojectmanager': [
            'htdocs/css/*.css',
            'htdocs/img/*.png',
            'htdocs/js/*.js',
            'templates/*.cs'
        ]
    },
    author='Alvaro J. Iradier',
    url="",
    license='BSD',
    entry_points = {'trac.plugins': ['tracprojectmanager = tracprojectmanager']})
