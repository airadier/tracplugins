"""
AMB Project Manager.
Make New project module.
"""
from trac.core import *
from trac.env import open_environment, Environment
from trac.config import Option, ListOption
from trac.util.html import html
from trac.web.chrome import add_stylesheet

from trac.admin.api import IAdminPanelProvider
from admin import check_upgrade
from subprocess import Popen, PIPE
import os
import time



class AMBProjectMake(Component):
    """
    AMB Project Manager - Make Project.
    Provides the administrative pages for creating a new project.
    """
    implements(IAdminPanelProvider)
    
    sql_defaults = Option('projectmanager', 'sql_defaults',
        doc='SQL to be run on every project after creation')
    
    groups = ListOption('projectmanager', 'groups',
        doc='Comma separated list of available project groups')
        
    tracadmin_command = Option('projectmanager', 'tracadmin_command', 'trac-admin.exe',
        doc='Full path to the trac-admin command')

    svnadmin_command = Option('projectmanager', 'svnadmin_command', 'svnadmin.exe',
        doc='Full path to the svnadmin command')
    
    repos_dir = Option('projectmanager', 'repos_dir', 
        doc='Path to the base of the repositories')

    environments_dir = Option('projectmanager', 'environments_dir', 
        doc='Path to the base of the environments')

    ##################################
    ## IAdminPanelProvider

    def get_admin_panels(self, req):
        """
        Adds new Administrative pages for Project Properties
        """
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('projectmanager', 'Project Management', 'newproject', 'New Project')


    def render_admin_panel(self, req, cat, page, component):
        """
        Render the project properties Admin page
        """
        req.perm.assert_permission('TRAC_ADMIN')
        
        #Check if DB needs upgrading
        check_upgrade(self.env)
        
        if req.method == 'POST':
            if req.args.has_key('make'):
                data = self._do_createproject(req)
            if req.args.has_key('back'):
                req.redirect(req.href.admin(cat, page))
                return
        else:
            data = self._render_view(req)
    
        add_stylesheet(req, 'tracprojectmanager/css/projectproperties.css')
    
        return 'newproject.html', data

    ##################################


    
    def _do_createproject(self, req):
        """
        Update project properties from the Admin form
        """
        data = {}
        data['project_created'] = True
        
        group = req.args['group']
        templates_dir = self.env.config.get('inherit', 'templates_dir')
        inherit_file = self.env.config.get('inherit', 'file')
        
        #Try to get custom settings for this project group
        templates_dir = self.env.config.get('projectmanager', 'groups.%s.templates_dir' % group, templates_dir)
        inherit_file = self.env.config.get('projectmanager', 'groups.%s.inherit_file' % group, inherit_file)
        group_dir = self.env.config.get('projectmanager', 'groups.%s.dirname' % group, group)
        sql_defaults = self.env.config.get('projectmanager', 'groups.%s.sql_defaults' % group, self.sql_defaults)
        
        assert self.repos_dir, "repos_dir not defined in .ini"
        assert self.environments_dir, "environments_dir not defined in .ini"

        if req.args.has_key('makesvn'):
            cmd = "%s create %s" % (self.svnadmin_command,os.path.join(self.repos_dir, group_dir, req.args['short_name']))
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)            
            (stdout, stderr) = p.communicate()
            if p.returncode != 0:
                data['svn_error'] = True
            data['svn_created'] = True
            data['svn_output'] = stdout
            data['svn_errors'] = stderr
        

        if req.args.has_key('maketrac'):
            
            repos_dir = os.path.join(self.repos_dir, group_dir, req.args['short_name'])
            env_dir = os.path.join(self.environments_dir, group_dir, req.args['short_name'])
            
            cmd = '%s "%s" initenv "%s" sqlite:%s svn "%s" --inherit="%s"' % (
                self.tracadmin_command,
                env_dir,
                req.args['full_name'],
                os.path.join('db','trac.db'),
                repos_dir,
                inherit_file                
                )
            #stdin, stdout, stderr = os.popen3(command)
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            (stdout, stderr) = p.communicate()
            data['trac_error'] = p.returncode != 0

            try:
                template = os.path.join(env_dir, 'templates', 'site.html') 
                stdout = stdout + 'Removing template: %s' % template
                os.remove(template)
            except: pass

            data['trac_created'] = True
            data['trac_output'] = stdout
            data['trac_errors'] = stderr
            
            try:
                env = open_environment(env_dir, use_cache=False)
                db = env.get_db_cnx()
                cursor = db.cursor()
                
                output = ""
                output = output + "\n\nSQL Defaults, executing statements\n"
                output = output + "==================================\n"
                for statement in sql_defaults.splitlines():
                    output = output + "Executing: %s\n" % statement 
                    cursor.execute(statement)
                
                db.commit()
                data['trac_output'] = data['trac_output'] + output
                
                env.shutdown()
                
            except:
                data['trac_output'] = data['trac_output'] + "\n\nError running SQL Defaults statements, skipping\n"
            
            return data


    def _render_view(self,req):
        """
        Build template data for the Admin page
        """
        
        groups = []
        for group in self.groups:
            description = self.env.config.get('projectmanager', 'groups.%s.description' % group, group)
            groups.append(dict(name=group, label=description))
                
        return {'groups': groups }
        
        

