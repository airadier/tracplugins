# -*- coding: utf-8 -*-
"""
AMB Project Manager.
Shared auth Module
"""
## trac imports
from trac.env import Environment, open_environment
from trac.core import *
from trac.config import BoolOption
from trac.web import IAuthenticator, IRequestFilter, auth
from sharedsettings import get_master_env
from utils import wrapfunc

class SharedAuth(Component):
    
    implements(IRequestFilter)
    implements(IAuthenticator)
    
    def __init__(self):
        #When initing, replace _do_login and _do_logout with customized versions
        #Note these functions cannot be methods of SharedAuth, because there is a SharedAuth instance
        #for every environment, so wrapping would make an infinite recursion        
        wrapfunc(auth.LoginModule, "_do_login", _shared_do_login)
        self.env.log.info("ProjectManager SharedAuth replaced LoginModule._do_login")
        wrapfunc(auth.LoginModule, "_do_logout", _shared_do_logout)
        self.env.log.info("ProjectManager SharedAuth replaced LoginModule._do_logout")
        wrapfunc(auth.LoginModule, "_expire_cookie", _shared_expire_cookie)
        self.env.log.info("ProjectManager SharedAuth replaced LoginModule._expire_cookie")


    # IRequestFilter methods. Do nothing, just make sure SharedAuth is instantiated
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type    
    
    # IAuthenticator methods
    def authenticate(self, req):
        if req.incookie.has_key('trac_auth'):
            #Try to authenticate in the master environment
            self.log.debug("Trying to authenticate in master environment")
            env = get_master_env(self.env)            
            return auth.LoginModule(env).authenticate(req)
            
        return None

def _shared_do_login(original_callable, the_class, req, *args, **kwargs):   
    
    #Call the original _do_login
    original_callable(the_class, req, *args, **kwargs)
    
    child_env = the_class.env
    env = get_master_env(child_env)
    if env.path != child_env.path:
        #Instantiate a trac LoginModule using the master environment, and login on it
        auth.LoginModule(env)._do_login(req)
    
    auth_path = child_env.config.get('projectmanager', 'auth_cookie_path', '/')
    child_env.log.debug("Changing auth cookie path to %s" % auth_path)
    req.outcookie['trac_auth']['path'] = auth_path


def _shared_do_logout(original_callable, the_class, req, *args, **kwargs):   

    #Call the original _do_logout
    original_callable(the_class, req, *args, **kwargs)

    child_env = the_class.env
    env = get_master_env(child_env)    
    if env.path != child_env.path:
        #Instantiate a trac LoginModule using the master environment, and login on it
        auth.LoginModule(env)._do_logout(req)
    
    auth_path = child_env.config.get('projectmanager', 'auth_cookie_path', '/')
    child_env.log.debug("Changing auth cookie path to %s" % auth_path)
    if req.outcookie.has_key('trac_auth'): 
        req.outcookie['trac_auth']['path'] = auth_path


def _shared_expire_cookie(original_callable, the_class, req):
    child_env = the_class.env
    auth_path = child_env.config.get('projectmanager', 'auth_cookie_path', '/')
    if req.outcookie.has_key('trac_auth'): 
        if req.outcookie['trac_auth']['path'] != auth_path:
            del req.outcookie['trac_auth']
            return
    
    original_callable(the_class, req)
    