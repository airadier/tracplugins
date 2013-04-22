"""
AMB Project Manager.
Make New project module.
"""
from trac.core import *
from trac.util.html import html
from trac.web.chrome import add_stylesheet

from webadmin.web_ui import IAdminPageProvider
from datetime import datetime
from time import time
from admin import check_upgrade
import os
from subprocess import Popen, PIPE

TRAC_COMMAND = "trac-admin"
ENVS_FOLDER="/var/trac"

SVN_COMMAND="svnadmin"
REPOS_FOLDER="/var/svn"



class AMBProjectMake(Component):
    """
    AMB Project Manager - Make Project.
    Provides the administrative pages for creating a new project.
    """
    implements(IAdminPageProvider)

    ##################################
    ## IAdminPageProvider

    def get_admin_pages(self, req):
        """
        Adds new Administrative pages for Project Properties
        """
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('projectmanager', 'Project Management', 'newproject', 'New Project')


    def process_admin_request(self, req, cat, page, component):
        """
        Render the project properties Admin page
        """
        req.perm.assert_permission('TRAC_ADMIN')
        
        #Check if DB needs upgrading
        check_upgrade(self.env)
        
        if req.method == 'POST':
            if req.args.has_key('make'):
                self._do_createproject(req)
            if req.args.has_key('back'):
                req.redirect(self.env.href.admin(cat, page))
                return
        else:
            self._render_view(req)
    
        add_stylesheet(req, 'tracprojectmanager/css/projectproperties.css')
    
        return 'newproject.cs', None

    ##################################


    
    def _do_createproject(self, req):
        """
        Update project properties from the Admin form
        """
        req.hdf['project_created'] = True

        templates_dir = self.env.config.get('trac', 'templates_dir')
        tracadmin_command = self.env.config.get('trac', 'tracadmin_command')
        svnadmin_command = self.env.config.get('trac', 'svnadmin_command')
        repos_dir = self.env.config.get('trac', 'repos_dir')
        environments_dir = self.env.config.get('trac', 'environments_dir')
        
        assert templates_dir, "templates_dir not defined in .ini"
        assert tracadmin_command, "tracadmin_command not defined in .ini"
        assert svnadmin_command, "tracadmin_command not defined in .ini"
        assert repos_dir, "repos_dir not defined in .ini"
        assert environments_dir, "environments_dir not defined in .ini"
        

        if req.args.has_key('makesvn'):
            cmd = "%s create %s" % (svnadmin_command,os.path.join(repos_dir,req.args['company'], req.args['short_name']))
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)            
            (stdout, stderr) = p.communicate()
            if p.returncode != 0:
                req.hdf['svn_error'] = True
            req.hdf['svn_created'] = True
            req.hdf['svn_output'] = stdout
            req.hdf['svn_errors'] = stderr
        

        if req.args.has_key('maketrac'):
            
            cmd = '%s "%s" initenv "%s" sqlite:%s svn "%s" "%s"' % (
                tracadmin_command,
                os.path.join(environments_dir,req.args['company'], req.args['short_name']),
                req.args['full_name'],
                os.path.join('db','trac.db'),
                os.path.join(repos_dir,req.args['company'], req.args['short_name']),
                templates_dir
                )
            #stdin, stdout, stderr = os.popen3(command)
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            (stdout, stderr) = p.communicate()
            if p.returncode != 0:
                req.hdf['trac_error'] = True
            req.hdf['trac_created'] = True
            req.hdf['trac_output'] = "Output test"
            req.hdf['trac_output'] = stdout
            req.hdf['trac_errors'] = stderr


    def _render_view(self,req):
        """
        Build template data for the Admin page
        """
        companies = [
            dict(name='amb', label='AM&B'),
            dict(name='ecom', label='ECOM'),
            dict(name='thales', label='Thales'),
        ]
        
        req.hdf['admin.project.companies'] = companies
        
        

    