# -*- coding: utf-8 -*-
"""
AMB Project Manager.
Shared auth Module
"""
## trac imports
from trac.env import Environment, open_environment
from trac.core import *
from trac.web import IRequestFilter
from trac.wiki.api import WikiSystem, IWikiPageManipulator
from trac.wiki.web_ui import WikiModule
from trac.wiki.model import WikiPage
from trac.resource import Resource
from sharedsettings import get_master_env
from trac.config import ListOption
from utils import wrapfunc

class SharedTemplates(Component):
    
    implements(IRequestFilter)
    implements(IWikiPageManipulator)
    
    global_template_prefixes = ListOption('projectmanager', 'global_templates_prefix',
        'GlobalTemplates')
    
    def __init__(self):
        wrapfunc(WikiSystem, "get_pages", _wrapped_get_pages)
        self.env.log.info("ProjectManager SharedTemplates replaced WikiSystem.get_pages")
        wrapfunc(WikiPage, "__init__", _wrapped_wikipage_init)
        self.env.log.info("ProjectManager SharedTemplates replaced WikiPage.__init__")
        
    # IRequestFilter methods. Do nothing, just make sure SharedAuth is instantiated
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if data and self.env == get_master_env(self.env):
            data['global_template_patterns'] = self.global_template_prefixes
        return template, data, content_type    
        
        
    #IWikiPageManipulator Methods
    def prepare_wiki_page(self, req, page, fields):
        """Not currently called, but should be provided for future
        compatibility."""
        pass

    def validate_wiki_page(self, req, page):
        for global_prefix in self.global_template_prefixes:
            prefix = WikiModule.PAGE_TEMPLATES_PREFIX + global_prefix + "/"
            #Check if page starts with one of the Global Template prefixes
            if page.name.startswith(prefix):
                return [(None, 'Global templates must be modified from master project')]
        return []


def _wrapped_wikipage_init(original_callable, the_class, child_env, name=None, version=None, db=None, *args, **kwargs):
    """
    Intercept WikiPage constructor, to recover Global templates
    from the master project
    """
    
    for global_prefix in SharedTemplates(child_env).global_template_prefixes:
        prefix = WikiModule.PAGE_TEMPLATES_PREFIX + global_prefix + "/"
        #Check if page starts with one of the Global Template prefixes
        if not name.startswith(prefix): continue
        
        #Get master environment
        env = get_master_env(child_env)

        #Remove PageTemplate/ prefix
        template_name = name[len(WikiModule.PAGE_TEMPLATES_PREFIX):]
        child_env.log.debug("Recovering page %s from master environment", template_name )
        
        original_callable(the_class, env, template_name, version, None, *args, **kwargs)
        
        #Add the PageTemplates prefix to the page, once recovered
        the_class.name = WikiModule.PAGE_TEMPLATES_PREFIX + the_class.name
        the_class.resource = Resource('wiki', the_class.name, version)
        #Make read only except in master environment
        if env != child_env:
            the_class.readonly = True
        child_env.log.debug("Recovered page %s from master environment", the_class.name )

        return
    
    original_callable(the_class, child_env, name, version, db, *args, **kwargs)

def _wrapped_get_pages(original_callable, the_class, prefix=None, *args, **kwargs):
    
    #Call the original _do_login
    for page in original_callable(the_class, prefix, *args, **kwargs):
        yield page
    
    env = get_master_env(the_class.env)
    if env.path == the_class.env.path: return
        
    wiki_system = WikiSystem(env)
    
    if not WikiModule.PAGE_TEMPLATES_PREFIX.startswith(prefix or ''): return
    
    for prefix in SharedTemplates(the_class.env).global_template_prefixes:
        for page in wiki_system.get_pages(prefix):
            yield WikiModule.PAGE_TEMPLATES_PREFIX + page
    