"""
AMB Project Manager.
Administrative module.
"""
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionGroupProvider
from trac.util.html import html
from trac.web.chrome import add_stylesheet, ITemplateProvider
from pkg_resources import resource_filename


from trac.admin.api import IAdminPanelProvider
from datetime import datetime
from time import time
from utils import get_property, set_property, get_all_tags

DATE_FORMAT="%d/%m/%Y"
DATE_FORMATALT="%d/%m/%y"
DATE_HINT="DD/MM/YYYY"
TIME_FORMAT="%d/%m/%Y %H:%M:%S"

STATUS = {
    'unknown': '5. Desconocido',
    'active': '1. Activo',
    'proposal': '2. Propuesto',
    'standby': '3. Suspendido',
    'closed': '4. Cerrado',
}

DB_VERSION = 2

STATEMENTS = (
    ("CREATE TABLE pm_properties (key text PRIMARY_KEY, value text)", ()),
    ("INSERT INTO pm_properties (key, value) VALUES ('db_version', %s)",(DB_VERSION,)),
    ("INSERT INTO pm_properties (key, value) VALUES ('company', '')",()),
    ("INSERT INTO pm_properties (key, value) VALUES ('status', 'unknown')",()),
    ("INSERT INTO pm_properties (key, value) VALUES ('date_created', %s)",(datetime.now().strftime(TIME_FORMAT),)),
    ("INSERT INTO pm_properties (key, value) VALUES ('date_started', '')",()),
    ("INSERT INTO pm_properties (key, value) VALUES ('date_scheduled', '')",()),
    ("INSERT INTO pm_properties (key, value) VALUES ('date_finished', '')",()),
    ("INSERT INTO pm_properties (key, value) VALUES ('percent', 0)",()),
    ("INSERT INTO pm_properties (key, value) VALUES ('client', '')",()),
    ("INSERT INTO pm_properties (key, value) VALUES ('manager', '')",()),
    ("INSERT INTO pm_properties (key, value) VALUES ('last_login', '0')",()),
    ("INSERT INTO pm_properties (key, value) VALUES ('tags', '')",()),
)

UPDATE = {
    0 : ( # From version 0 to version 1
            ("INSERT INTO pm_properties (key, value) VALUES ('last_login', 0)",()),
        ),
    1 : ( # From version 1 to version 2
            ("INSERT INTO pm_properties (key, value) VALUES ('tags', '')",()),
        ),
}


def check_upgrade(env):
    """
    Check DB version, and if it's old, perform an upgrade
    """
    db_version = get_property(env, 'db_version')
    if not db_version: return False
        
    if int(DB_VERSION) > int(db_version):
        upgrade_db(env, int(db_version), int(DB_VERSION))
        

def upgrade_db(env, old_version, new_version):
    """
    Perform an upgrade to the Project Manager database tables
    """
    db = env.get_db_cnx()
    cursor = db.cursor()

    for version in range(old_version, new_version):
        if not UPDATE.has_key(version): 
            continue
        for statement in UPDATE[version]:
            cursor.execute(statement[0], statement[1])
        
    cursor.execute("UPDATE pm_properties SET value = %s WHERE key = 'db_version'", (new_version,))
    db.commit()



class AMBProjectAdmin(Component):
    """
    AMB Project Manager.
    AMBProjectAdmin provides the administrative pages (WebAdmin plugin required), and
    database timestamp updating and upgrading, so it should be included in all projects.
    """
    implements(IEnvironmentSetupParticipant)
    implements(ITemplateProvider)
    implements(IAdminPanelProvider)
    implements(IPermissionGroupProvider)
    
    
    ##################################
    ## Begin IPermissionGroupProvider Methods

    def  get_permission_groups(self, username):
        """
        Updates the project activity timestamp if permission groups are inquired for
        a logged user.
        """
        
        if username and username != 'anonymous':
            self._update_last_login()

        return []
        
    ############################################
    
    
    ##################################
    ## Begin IEnvironmentSetupParticipant Methods

    def environment_created(self):
        """
        On environment creation, add the Project Manager tables 
        """
        self._do_createdb(verbose=True)
    
    def environment_needs_upgrade(self, db):
        return False
    
    def upgrade_environment(self, db):
        pass

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


    ##################################
    ## IAdminPanelProvider

    def get_admin_panels(self, req):
        """
        Adds new Administrative pages for Project Properties
        """
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('projectmanager', 'Project Management', 'properties', 'Properties')
            self._update_last_login()
            

    def render_admin_panel(self, req, cat, page, component):
        """
        Render the project properties Admin page
        """
        req.perm.assert_permission('TRAC_ADMIN')
        
        #Check if DB needs upgrading
        check_upgrade(self.env)
        
        data = {}
        if req.method == 'POST':
            if req.args.has_key('save'):
                self._do_update(req)
            if req.args.has_key('createdb'):
                self._do_createdb()
            #After a post, redirect to the page to avoid double posting on reload problem
            req.redirect(req.href.admin(cat, page))
        else:
            data = self._render_view(req)
    
        add_stylesheet(req, 'tracprojectmanager/css/projectproperties.css')
    
        return 'projectproperties.html', data

    ##################################


    
    def _do_update(self, req):
        """
        Update project properties from the Admin form
        """
        
        #Update tags
        taglist = set([])
        taglist.update(req.args['more_tags'].split())        
        tags = req.args.get('tags',[])
        if type(tags) is list: taglist.update(tags)
        else: taglist.update([tags])
        set_property(self.env, 'tags', " ".join(sorted(taglist)))
        
        #Check dates
        def formatted_date(strdate):
            try:
                return datetime.strptime(strdate, DATE_FORMAT).strftime(DATE_FORMAT)
            except:
                try:
                    return datetime.strptime(strdate, TIME_FORMAT).strftime(DATE_FORMAT)
                except:
                    try:
                        return datetime.strptime(strdate, DATE_FORMATALT).strftime(DATE_FORMAT)
                    except:
                        return ''
                        
        set_property(self.env, 'date_started', formatted_date(req.args.get('date_started',None)))
        set_property(self.env, 'date_scheduled', formatted_date(req.args.get('date_scheduled',None)))
        set_property(self.env, 'date_finished', formatted_date(req.args.get('date_finished',None)))
        
        for value in ('company', 'percent', 'status', 'client', 'manager', ) :
            set_property(self.env, value, req.args[value])
        
    
    def _render_view(self,req):
        """
        Build template data for the Admin page
        """
        
        data = {}
        
        #Check if Project Management tables exist
        if get_property(self.env, 'db_version') == str(DB_VERSION):            
            data['database_ok'] = True
        else:
            return data

        status = get_property(self.env, 'status')

        statuses = [
            dict(name=x, label=y, selected=status == x) for x,y in sorted(STATUS.iteritems(), cmp=(lambda i1,i2: i1[1] > i2[1] and 1 or -1))
        ]

        project_data = {'tags': get_property(self.env, 'tags', '').split(),
                'company': get_property(self.env, 'company'),
                'date_started': get_property(self.env, 'date_started'),
                'date_scheduled': get_property(self.env, 'date_scheduled'),
                'date_finished': get_property(self.env, 'date_finished'),
                'percent': get_property(self.env, 'percent'),
                'status': STATUS[status],
                'client': get_property(self.env, 'client'),
                'manager': get_property(self.env, 'manager'),
                'statuses': statuses}
        
        data['admin'] = {}
        data['admin']['project'] = project_data
        data['admin']['date_hint'] = DATE_HINT
        data['admin']['all_tags'] = sorted(get_all_tags(self.env))
        
        return data
    
        
    def _do_createdb(self, verbose = False):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        if verbose:
            print "AMB Project Manager, executing statements"

        for statement in STATEMENTS:
            if verbose:
                print "Executing: " + statement[0] % tuple(["'%s'" % x for x in statement[1]])
            cursor.execute(statement[0], statement[1])
        
        db.commit()


    def _update_last_login(self):
        """
        Update the last_login time when a logged user browses something
        """
        last_login = get_property(self.env, 'last_login', None)
        if last_login != None:
            set_property(self.env, 'last_login', int(time()))
        

    
