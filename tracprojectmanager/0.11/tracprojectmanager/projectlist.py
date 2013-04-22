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
from trac.env import open_environment, Environment

from admin import STATUS, get_property, check_upgrade, TIME_FORMAT, DATE_FORMAT, DATE_FORMATALT
from utils import get_property, set_property, get_project_list, get_all_tags

from datetime import datetime

import sys
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
    
    
    #######################################
    ## Begin INavigationContributor Methods

    def get_active_navigation_item(self, req):
        return 'projectlist'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('ROADMAP_VIEW') and not req.perm.has_permission('TRAC_ADMIN'):
            return
        yield ('mainnav', 'projectlist',
            html.A('Project List', href=req.href.projectlist()))

    #######################################


    ################################
    ## Begin IRequestHandler Methods

    def  match_request(self, req):
        if re.match(r'/projectlist(?:/(.*))?$', req.path_info):
            return True

    def process_request(self, req):
        if not req.perm.has_permission('TRAC_ADMIN'):
            req.perm.assert_permission('ROADMAP_VIEW')
        
        #If the page was posted, a filter was applied. Build and redirect using query strnig
        if req.args.has_key('update'):
            req.redirect(self._get_href(req))
            
        #Process filtering arguments
        self.status = req.args.get('status', None)
        
        #Process sorting arguments
        self.desc = req.args.get('desc','0') == '1'
        self.order = req.args.get('order', None) or DEFAULT_SORT_FIELD

        #Start with an empty project list for each project group
        projects = { }
        for status in STATUS.keys():
            projects[status] = []
        
        selected_tags = req.args.get('tags', [])        
        if type(selected_tags) is not list:
            selected_tags = [selected_tags]
        
        for project, project_path, project_url, env in get_project_list(self.env, req, True, True):
            
            needs_upgrade = False
            if not env:
                try:
                    env = Environment(project_path)
                    needs_upgrade = env.needs_upgrade()
                except:
                    continue
            
            #Upgrade selected, project needs upgrade, and project checked... do it!
            if req.args.has_key('upgrade') and req.args.has_key('checked_%s' % project):
                try:
                    env.upgrade()
                    upgraded = "Upgrade OK!"
                except:
                    upgraded = "Upgrade ERROR: %s:%s" % (sys.exc_info()[0],sys.exc_info()[1])
            else:
                upgraded = None
            
            #Check if DB needs upgrading
            check_upgrade(env)        
                        
            #Get last_login timestamp, and convert to human readable
            last_login = int(get_property(env, 'last_login',0))
            if last_login == 0:
                last_login = None
            else:
                last_login = datetime.fromtimestamp(last_login)
            

            #Filter by status
            project_status = get_property(env, 'status','unknown')
            if self.status and project_status != self.status: 
                continue
        
            #Filter by tag
            project_tags = get_property(env, 'tags', '').split()     
            if selected_tags and not set(selected_tags) & set(project_tags): 
                continue

            projects[project_status].append({
                'shortname': project,
                'name': env.project_name,
                'tags': project_tags,
                'needs_upgrade': needs_upgrade,
                'upgraded': upgraded,
                'checked': req.args.has_key('checked_%s' % project),
                'description': env.project_description,
                'company': get_property(env, 'company'),
                'created': self._parsed_date(get_property(env, 'date_created')),
                'started': self._parsed_date(get_property(env, 'date_started')),
                'scheduled': self._parsed_date(get_property(env, 'date_scheduled')),
                'finished': self._parsed_date(get_property(env, 'date_finished')),
                'percent_finished': get_property(env, 'percent', '0'),
                'percent_remaining': 100 - int(get_property(env, 'percent', '0')),
                'status': STATUS[project_status],
                'client': get_property(env, 'client'),
                'manager': get_property(env, 'manager','').replace(',',' ').split(),
                'last_login': last_login,
                'href': project_url,
                'adminurl': project_url + '/admin/projectmanager/properties'
            })
        
        #Status selection
        statuses = [dict(name='', label='*', selected=self.status ==None)]
        statuses += [
            dict(name=x, label=y, selected=self.status == x)
            for x,y in sorted(STATUS.items(), cmp=(lambda i1,i2: i1[1] > i2[1] and 1 or -1))
        ]
        
                
        ####################################
        ## Functions for project sorting, depending on the field
        def cmp_datetime(x,y):
            if x and not y: return 1
            if y and not x: return -1
            return x < y and -1 or 1
        
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
        elif self.order in ('started', 'scheduled', 'finished'):
            cmp = lambda x,y: cmp_datetime(x[self.order], y[self.order])
        elif self.order in ('percent_finished'):
            cmp = lambda x,y: cmp_int(x[self.order],y[self.order])
        else:
            cmp = lambda x,y: cmp_str_nocase(x[self.order],y[self.order])
                
        for project_group in projects.values():
            project_group.sort(cmp=cmp, reverse=self.desc and True or False)

        add_stylesheet(req, 'tracprojectmanager/css/projectlist.css')
        
        #For Genshi, when used, return a 3 element tuple
        return 'projectlist.html', {
            'title': 'Project List',
            'status_names': STATUS,
            'projects': projects,
            'statuses': statuses,
            'status': self.status,
            'order': self.order,
            'desc': self.desc,
            'selected_tags': selected_tags,
            'all_tags': sorted(get_all_tags(self.env))}, None


    ## End IRequestHandler Methods
    ################################
    
    def _parsed_date(self, strdate):
        try:
            return datetime.strptime(strdate, DATE_FORMAT)
        except:
            try:
                return datetime.strptime(strdate, TIME_FORMAT)
            except:
                try:
                    return datetime.strptime(strdate, DATE_FORMATALT)
                except:
                    return None    
    
    def _get_href(self, req):
        
        #Build URL and querystring
        return req.href.projectlist(status=req.args.get('status'),
            order = req.args.get('order'), desc = req.args.get('desc'), tags=req.args.get('tags'))
        
