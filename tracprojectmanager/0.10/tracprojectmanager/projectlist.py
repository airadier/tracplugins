"""
AMB Project Manager.
Project List module.
"""

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web import IRequestHandler
from trac.util.html import html
from trac.web.chrome import add_stylesheet, INavigationContributor, ITemplateProvider
from trac.web.href import Href
from trac.env import open_environment

from admin import STATUS, get_property, check_upgrade, TIME_FORMAT, DATE_FORMAT

from datetime import datetime

import re
import os
import posixpath


DEFAULT_SORT_FIELD = 'name'

class AMBProjectList(Component):
    """
    AM&B Project List renderer
    """
    implements(INavigationContributor)#, IPermissionRequestor)#
    implements(IRequestHandler)
   
    
    def __init__(self):
        #Set some sorting and filtering defaults
        self.status = None
        self.order = DEFAULT_SORT_FIELD
        self.desc = None
    
    
    ##################################
    ## Begin INavigationContributor Methods

    def get_active_navigation_item(self, req):
        return 'projectlist'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('ROADMAP_VIEW'):
            return
        yield ('mainnav', 'projectlist',
            html.A('Project List', href=req.href.projectlist()))

    ##################################


    ##################################
    ## Begin IRequestHandler Methods

    def  match_request(self, req):
        if re.match(r'/projectlist(?:/(.*))?$', req.path_info):
            return True

    def process_request(self, req):
        req.perm.assert_permission('ROADMAP_VIEW')
        
        #If the page was posted, a filter was applied. Build and redirect using query strnig
        if req.args.has_key('update'):
            req.redirect(self._get_href(req))
            
        req.hdf['title'] = 'Project List'
        
        #Process filtering arguments
        self.status = req.args.has_key('status') and req.args['status'] or None
        
        #Process sorting arguments
        self.desc = req.args.has_key('desc') and req.args['desc'] == '1' or None        
        self.order = req.args.has_key('order') and req.args['order'] or DEFAULT_SORT_FIELD

        #Get search path and base_url
        search_path, this_project = os.path.split(self.env.path)
        base_url, _ = posixpath.split(req.abs_href())
        href = Href(base_url)
                
        #Start with an empty project list
        projects = []
        for project in os.listdir(search_path):
            
            #Open the project environment
            project_path = os.path.join(search_path,project)
            env = open_environment(project_path)
            
            #Check if DB needs upgrading
            check_upgrade(env)        
            
            #Trim project description if too long
            if len(env.project_description) <= 60:
                description = env.project_description
            else:
                description = "%s..." % env.project_description[:60]
            
            #Get last_login timestamp, and convert to human readable
            last_login = int(get_property(env, 'last_login',0))
            if last_login == 0:
                last_login = ''
            else:
                last_login = datetime.fromtimestamp(last_login).strftime(TIME_FORMAT)
            

            #Filter by status
            project_status = get_property(env, 'status','unknown')
            if self.status and project_status != self.status: 
                continue

            projects.append({'name': env.project_name,
                'description': description,
                'company': get_property(env, 'company'),
                'created': get_property(env, 'date_created'),
                'started': get_property(env, 'date_started'),
                'scheduled': get_property(env, 'date_scheduled'),
                'finished': get_property(env, 'date_finished'),
                'percent_finished': get_property(env, 'percent', '0'),
                'percent_remaining': 100 - int(get_property(env, 'percent', '0')),
                'status': STATUS[project_status],
                'client': get_property(env, 'client'),
                'manager': get_property(env, 'manager'),              
                'last_login': last_login,
                'href': href(project)})
        
        #Status selection
        sorted_keys = STATUS.keys()
        sorted_keys.sort()
        statuses = [dict(name='', label='*', selected=self.status ==None)]
        statuses += [
            dict(name=x, label=STATUS[x], selected=self.status == x) for x in sorted_keys
        ]
        
        
        ####################################
        ## Functions for project sorting, depending on the field
        def cmp_datetime(x,y):
            try:
                return datetime.strptime(x, TIME_FORMAT) < datetime.strptime(y, TIME_FORMAT) and -1 or 1
            except:
                return x.lower() < y.lower() and -1 or 1
            

        def cmp_date(x,y):
            try:
                return datetime.strptime(x, DATE_FORMAT) < datetime.strptime(y, DATE_FORMAT) and -1 or 1
            except:
                return x.lower() < y.lower() and -1 or 1
        
        def cmp_int(x,y):
            try:
                return int(x) < int(y) and -1 or 1
            except:
                return x < y and -1 or 1
        
        def cmp_str_nocase(x,y):
            try:
                return x.lower() < y.lower() and -1 or 1
            except:
                return x < y and -1 or 1
        #################################

        #For some fields, use a special comparison function
        if self.order in ('created', 'last_login'):
            cmp = lambda x,y: cmp_datetime(x[self.order], y[self.order])
        if self.order in ('started', 'scheduled', 'finished'):
            cmp = lambda x,y: cmp_date(x[self.order], y[self.order])
        if self.order in ('percent_finished'):
            cmp = lambda x,y: cmp_int(x[self.order],y[self.order])
        else:
            cmp = lambda x,y: cmp_str_nocase(x[self.order],y[self.order])

        projects.sort(cmp=cmp, reverse=self.desc and True or False)

        #Set template HDF
        req.hdf['projects'] = projects
        req.hdf['statuses'] = statuses
        req.hdf['status'] = self.status
        req.hdf['order'] = self.order 
        req.hdf['desc'] = self.desc
        
        add_stylesheet(req, 'tracprojectmanager/css/projectlist.css')
                
        return 'projectlist.cs', None


    ## End IRequestHandler Methods
    ##################################
    
    
    def _get_href(self, req):
        
        #Update sorting and filtering from request values
        if req.args.has_key('status'):
            self.status = req.args['status']
        if req.args.has_key('order'):
            self.order = req.args['order']
        if req.args.has_key('desc'):
            self.desc = req.args['desc']
        
        #Build URL and querystring
        return req.href.projectlist(status=1 and self.status or None,
            order = self.order or None, desc = self.desc or None)
        
