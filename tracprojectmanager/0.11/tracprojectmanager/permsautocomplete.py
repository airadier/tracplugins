"""
AMB Project Manager.
Favorites plugin
"""

import re
from trac.core import *
from trac.web import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from pkg_resources import resource_filename
from trac.perm import IPermissionGroupProvider

class PermsAutocomplete(Component):

    implements(IRequestFilter)
    implements(ITemplateProvider)   
    implements(IRequestHandler)

    ##################################
    ## IRequestFilter
    
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, content_type):
        return template, content_type
    
    def post_process_request(self, req, template, data, content_type):
        if template == 'admin_perms.html':
            add_stylesheet(req, 'tracprojectmanager/css/jquery.autocomplete.css')
            add_script(req, 'tracprojectmanager/js/jquery.autocomplete.js')
            add_script(req, '../autocompleteperms/autocompleteperms.js')
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
        if re.match(r'/autocompleteperms/autocompleteperms\.js$', req.path_info):
            return True

    group_providers = ExtensionPoint(IPermissionGroupProvider)

    def process_request(self, req):
        req.perm.assert_permission('TRAC_ADMIN')        
        if not re.match(r'/autocompleteperms/autocompleteperms\.js$', req.path_info): return

        subjects = set([])
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT username,action FROM permission")
        rows = cursor.fetchall()
        while True:
            num_users = len(subjects)                
            for user, action in rows:
                if user not in subjects:
                    subjects.add(user)
                    for provider in self.group_providers:
                        subjects.update(provider.get_permission_groups(action))
                    
                if not action.isupper() and action not in subjects:
                    subjects.add(action)
                    for provider in self.group_providers:
                        subjects.update(provider.get_permission_groups(action))
                        
            if num_users == len(subjects):
                break
        
        try:
            from acct_mgr.api import AccountManager
            acc_mgr = AccountManager(self.env)
            users = acc_mgr.get_users()
        except:
            users = [x[0] for x in self.env.get_known_users()]
        
        
        group_list = list(subjects - set(users) - set('#%s' % user for user in users))
        subjects.update(users)
        user_list = list(subjects)
        
        user_list.sort()
        group_list.sort()

        out = """
        var data = "%s".split(" ");
        var data_groups = "%s".split(" ");
        $(document).ready(function() {
            $("#gp_subject").autocomplete(data, {minChars: 0, max:9999});
            $("#sg_subject").autocomplete(data, {minChars: 0, max:9999});
            $("#sg_group").autocomplete(data_groups, {minChars: 0, max:9999});
        });
        """ % (" ".join(user_list), " ".join(group_list))
        
        req.send(out.encode("utf-8"), "text/javascript") 

    
    ##################################  