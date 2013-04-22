"""
AMB Project Manager.
Favorites plugin
"""

import re
from trac.core import *
from trac.web import IRequestFilter, IRequestHandler
from trac.util.html import html
from trac.web.chrome import ITemplateProvider, add_script
from trac.web.href import Href
from pkg_resources import resource_filename
from trac.wiki.macros import WikiMacroBase
from utils import get_project_list

class FavoriteSelector(Component):

    implements(IRequestFilter)
    implements(IRequestHandler)
    implements(ITemplateProvider)   

    ##################################
    ## IRequestFilter
    
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, content_type):
        return template, content_type
    
    def post_process_request(self, req, template, data, content_type):
        add_script(req, 'tracprojectmanager/js/fav.js')
        if template and not content_type or content_type == 'text/html':
            if not data: data = {}
            data.update({'base_template' : template,
                'is_favourite': req.session.has_key('favourite') and req.session['favourite'] == '1'})
        
            return ("fav.html", data, content_type)
        else: 
            return template, data, content_type
    
    ##################################

    ##################################
    ## ITemplateProvider

    def get_htdocs_dirs(self):
        """
        Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('tracprojectmanager', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return [resource_filename(__name__, 'templates')]

    ##################################    
    
    
    ################################
    ## Begin IRequestHandler Methods

    def  match_request(self, req):
        return req.authname != 'anonymous' \
            and re.match(r'/makefavourite/?$', req.path_info)
        

    def process_request(self, req):
        if req.args.has_key('favourite'):
            req.session['favourite'] = req.args['favourite']
            req.session.save()
        req.send("", 'text/plain')
        return None

    ## End IRequestHandler Methods
    ################################
    

        

class FavoriteProjects(WikiMacroBase):
    """
    FavoriteProjects - Display a list of favorite projects
    
    Usage example:
    {{{
    [[FavoriteProjects]]
    }}}
    """
    
    def expand_macro(self, formatter, name, text, args):
        
        if formatter.req.authname == 'anonymous':
            return "<div class='favouriteprojects'>Not available</div>"
        
        projects = get_project_list(self.env, formatter.req)
        fav_projects = []
        for project, path, url, env in projects:
            cnx = env.get_db_cnx()
            cursor = cnx.cursor()
            cursor.execute("SELECT value FROM session_attribute WHERE authenticated=1 AND sid=%s AND name='favourite'", (formatter.req.authname,))
            row = cursor.fetchone()
            if row and row[0] == '1':
                fav_projects.append((project, path, url, env, row[0]))
        
        fav_projects.sort(cmp = lambda x,y: x[0] < y[0] and 1 or -1)
        
        out = "<ul class='favouriteprojects'>"
        for project, path, url, env, last_visit in fav_projects:
            out = out + "<li class='favouriteprojectitem'><a href='%s'>%s</a></li>" % (url, env.project_name)
            
        out = out + "</ul>"
        return out
