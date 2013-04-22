from setuptools import setup

PACKAGE = 'tracscriptlet'
VERSION = '0.2'

setup(name=PACKAGE,
      version=VERSION,
      packages=['tracscriptlet'],
      author='Alvaro J. Iradier',
      url="http://www.trac-hacks.org/wiki/TracScriptlet",
      license='BSD',
      entry_points = {'trac.plugins': ['tracscriptlet = tracscriptlet']})
